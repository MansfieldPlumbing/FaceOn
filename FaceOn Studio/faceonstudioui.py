import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, colorchooser
import numpy as np
from PIL import Image, ImageDraw, ImageTk, ImageFont
import faceonstudiodefs
import faceonstudiocore
import queue
from faceonstudiocolor import ColorPicker, LivePreviewWindow
from faceonstudioface import dump_safe_face
import cv2

SYMBOLS = [
    'Off', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')',
    '●', '■', '◆', '♥', '★', '♦', '▲', '▼', '◄', '►',
    '+', '=', '~', '?'
]

class HistoryManager:
    def __init__(self, temp_dir):
        self.temp_dir = temp_dir
        self.steps = []
        self.current_step = -1
    def add_step(self, image_pil):
        if self.current_step < len(self.steps) - 1:
            for step_path in self.steps[self.current_step + 1:]:
                if os.path.exists(step_path):
                    os.remove(step_path)
            self.steps = self.steps[:self.current_step + 1]
        step_index = len(self.steps)
        filepath = os.path.join(self.temp_dir, f"step_{step_index:04d}.png")
        image_pil.save(filepath)
        self.steps.append(filepath)
        self.current_step = len(self.steps) - 1

    def undo(self):
        if self.current_step > 0:
            self.current_step -= 1
            return self.steps[self.current_step]
        return None

    def redo(self):
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            return self.steps[self.current_step]
        return None

class PaintShopApp(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master.configure(bg="#2b2b2b")
        self.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.core = faceonstudiocore.PaintShopCore()
        self.core.start()
        self.history = None
        self.source_image_path = None
        self.source_image_pil = None
        self.canvas_image_pil = None
        self.live_canvas = None
        self.last_x, self.last_y = None, None
        self.brush_color_rgb = (255, 0, 0)
        self.brush_size = 20.0
        self.brush_opacity = 1.0
        self.brush_hardness = 0.5
        self.brush_step = 1.0
        self.symbol_index = 0
        self.brush_stamp = None
        self.eyedropper_active = False
        self.core_update_job_id = None
        self.is_painting = False
        
        self.zoom_level = 1.0
        self.pan_offset = np.array([0.0, 0.0])
        self.last_pan_pos = None

        self.canvas_bg_id = None
        self.canvas_bg_photo = None
        self.live_preview_photo = None
        self.updated_canvas_photo = None
        
        self.external_preview_window = None
        
        self.persistent_title_status = "Broadcasting. Please Launch VirtuaCam"
        self.title_reset_job = None

        self._setup_styles()
        self._create_widgets()
        self._create_brush_stamp()
        self._poll_core_queue()
        self.set_title_status(self.persistent_title_status)

    def set_title_status(self, message, is_temporary=False, duration=5000):
        if self.title_reset_job:
            self.master.after_cancel(self.title_reset_job)
            self.title_reset_job = None

        full_title = f"FaceOn Studio | {message}"
        self.master.title(full_title)

        if is_temporary:
            self.title_reset_job = self.master.after(duration, lambda: self.set_title_status(self.persistent_title_status))

    def _setup_styles(self):
        self.bg, self.fg, self.trough, self.accent = "#2b2b2b", "#dcdcdc", "#3c3f41", "#555555"
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background=self.bg, foreground=self.fg, font=('Segoe UI', 9))
        style.configure('TFrame', background=self.bg)
        style.configure('TLabel', background=self.bg, foreground=self.fg)
        style.map('TButton', background=[('active', '#4a4a4a')])
        style.configure('TButton', background=self.trough, foreground=self.fg, borderwidth=1)
        
        style.configure('Horizontal.TScale', background=self.bg, troughcolor=self.trough, sliderthickness=15, borderwidth=0, relief='flat')
        style.map('TScale', background=[('active', self.accent)])
        
        self.configure(bg=self.bg)

    def _create_widgets(self):
        top_frame = ttk.Frame(self, style='TFrame')
        top_frame.pack(fill=tk.X, pady=(0, 5))
        
        col = 0
        
        icon_btn_style = {
            'font': ('Segoe UI Emoji', 11),
            'bg': self.bg,
            'fg': self.fg,
            'activebackground': '#4a4a4a',
            'activeforeground': self.fg,
            'borderwidth': 0,
            'relief': 'flat',
            'pady': 1,
            'padx': 2 
        }

        tk.Button(top_frame, text="📂", command=self._load_image, **icon_btn_style).grid(row=0, column=col); col += 1
        tk.Button(top_frame, text="💾", command=self._save_face_embedding, **icon_btn_style).grid(row=0, column=col, padx=(2, 10)); col += 1
        tk.Button(top_frame, text="↩️", command=self._undo, **icon_btn_style).grid(row=0, column=col); col += 1
        tk.Button(top_frame, text="↪️", command=self._redo, **icon_btn_style).grid(row=0, column=col, padx=(2, 10)); col += 1
        
        tk.Button(top_frame, text="🔍-", command=lambda: self._zoom(1/1.2), **icon_btn_style).grid(row=0, column=col); col += 1
        tk.Button(top_frame, text="🔎+", command=lambda: self._zoom(1.2), **icon_btn_style).grid(row=0, column=col, padx=(2, 10)); col += 1

        controls = {"Opacity": (0.02, 1), "Hardness": (0.02, 1), "Size": (2, 100), "Step": (1, 25)}
        defaults = {"Opacity": 1.0, "Hardness": 0.5, "Size": 20, "Step": 1}
        for name, (min_val, max_val) in controls.items():
            ttk.Label(top_frame, text=f"{name}:").grid(row=0, column=col, padx=(4, 2)); col += 1
            slider = ttk.Scale(top_frame, from_=min_val, to=max_val, value=defaults[name], command=self._update_brush_props)
            slider.grid(row=0, column=col, sticky='ew'); col += 1
            setattr(self, f"{name.lower()}_slider", slider)
            top_frame.grid_columnconfigure(col - 1, weight=1, minsize=50)

        ttk.Label(top_frame, text="Symbol:").grid(row=0, column=col, padx=(10, 2)); col += 1
        self.symbol_slider = ttk.Scale(top_frame, from_=0, to=len(SYMBOLS)-1, value=0, command=self._update_brush_props)
        self.symbol_slider.grid(row=0, column=col, sticky='ew'); col += 1
        top_frame.grid_columnconfigure(col - 1, weight=1, minsize=50)
        
        self.symbol_swatch = tk.Label(top_frame, text="", bg="#1e1e1e", fg="white", width=3, height=1, relief="sunken", font=('Segoe UI', 10, 'bold'))
        self.symbol_swatch.grid(row=0, column=col, padx=(5, 5), ipady=2); col += 1
        
        top_frame.grid_columnconfigure(col, weight=10); col += 1

        ttk.Button(top_frame, text="+", command=self._open_color_chooser, width=2).grid(row=0, column=col, padx=2); col += 1
        self.color_swatch = tk.Label(top_frame, bg="#ff0000", width=3, height=1, relief="sunken")
        self.color_swatch.grid(row=0, column=col, padx=(2, 5), ipady=2); col += 1

        main_frame = ttk.Frame(self, style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.canvas = tk.Canvas(main_frame, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_panel = ttk.Frame(main_frame, style='TFrame', width=240)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5,0))
        right_panel.pack_propagate(False)
        self.color_picker = ColorPicker(right_panel, size=220, callback=self._on_color_picked)
        self.color_picker.pack(pady=(10,10))
        self.updated_canvas_preview = ttk.Label(right_panel, text="Updated Canvas", style='TLabel', anchor='center', background="#1e1e1e")
        self.updated_canvas_preview.pack(fill=tk.BOTH, expand=True, pady=(0,5))
        self.live_preview = ttk.Label(right_panel, text="Live Camera", style='TLabel', anchor='center', background="#1e1e1e")
        self.live_preview.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(right_panel, text="External Preview", command=self._toggle_external_preview).pack(pady=5, fill=tk.X, padx=5)

        self.canvas.bind("<B1-Motion>", self._paint)
        self.canvas.bind("<ButtonPress-1>", self._start_paint)
        self.canvas.bind("<ButtonRelease-1>", self._stop_paint)
        self.canvas.bind("<Enter>", self._on_canvas_enter)
        self.canvas.bind("<Leave>", self._on_canvas_leave)
        self.canvas.bind("<Motion>", self._update_cursor_preview)
        self.bind("<Configure>", self._on_resize)
        self.canvas.bind("<ButtonPress-2>", self._start_pan)
        self.canvas.bind("<B2-Motion>", self._pan)
        self.canvas.bind("<ButtonRelease-2>", self._stop_pan)
        self.master.bind_all("<KeyPress-Control_L>", self._activate_eyedropper)
        self.master.bind_all("<KeyRelease-Control_L>", self._deactivate_eyedropper)
        self.canvas.bind("<ButtonPress-1>", self._canvas_click, add="+")
        self.master.bind_all("<Control-z>", self._undo_event)
        self.master.bind_all("<Control-y>", self._redo_event)
        self.canvas.bind("<Control-MouseWheel>", self._zoom_scroll)

    def _toggle_external_preview(self):
        if self.external_preview_window and self.external_preview_window.winfo_exists():
            self.external_preview_window.lift()
            self.external_preview_window.focus_force()
        else:
            self.external_preview_window = LivePreviewWindow(self.master, on_close=self._on_external_preview_close)

    def _on_external_preview_close(self):
        self.external_preview_window = None

    def _poll_core_queue(self):
        pil_img = None
        try:
            frame = self.core.ui_queue.get_nowait()
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            
            self.live_preview.update_idletasks()
            lbl_w, lbl_h = self.live_preview.winfo_width()-2, self.live_preview.winfo_height()-2
            if lbl_w > 1 and lbl_h > 1:
                resized = self._get_resized_image_for_label(pil_img, lbl_w, lbl_h)
                self.live_preview_photo = ImageTk.PhotoImage(resized)
                self.live_preview.configure(image=self.live_preview_photo)
        except queue.Empty: pass

        if self.external_preview_window and self.external_preview_window.winfo_exists() and pil_img:
             self.external_preview_window.update_image(pil_img)

        self.master.after(33, self._poll_core_queue)

    def _save_face_embedding(self):
        if not self.canvas_image_pil or not self.source_image_path:
            self.set_title_status("Save Canceled: No image loaded", is_temporary=True)
            return

        numpy_image = np.array(self.canvas_image_pil.convert('RGB'))
        bgr_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
        face = self.core.models.process_image_to_face(bgr_image, "PaintedFace.png")

        if face:
            source_basename = os.path.splitext(os.path.basename(self.source_image_path))[0]
            
            studio_version = 1
            while True:
                filename = f"{source_basename} (Studio {studio_version:02d}).safetensors"
                filepath = os.path.join(faceonstudiodefs.EMBEDDINGS_DIRECTORY, filename)
                
                if not os.path.exists(filepath):
                    break
                studio_version += 1
            
            try:
                face.name = filename
                dump_safe_face(face, filepath)
                clean_name = os.path.splitext(filename)[0]
                self.set_title_status(f"Saved: {clean_name}", is_temporary=True)
                print(f"SUCCESS: Saved new face embedding to '{filepath}'")
            except Exception as e:
                self.set_title_status("Save Failed!", is_temporary=True)
                print(f"ERROR: Failed to save face embedding file. Reason: {e}")
        else:
            self.set_title_status("Save Canceled: No face detected", is_temporary=True)
            print("WARN: Could not save embedding. No face was detected on the canvas.")

    def _on_resize(self, event=None):
        self.master.after(50, self.update_displays)

    def _load_image(self):
        filepath = filedialog.askopenfilename(initialdir=faceonstudiodefs.SOURCES_DIRECTORY)
        if not filepath: return
        self.canvas.delete("all")
        self.canvas_bg_id = None
        
        self.source_image_path = filepath
        basename = os.path.splitext(os.path.basename(filepath))[0]
        session_temp_dir = os.path.join(faceonstudiodefs.TEMP_DIRECTORY, f"{basename}_{int(time.time())}")
        os.makedirs(session_temp_dir, exist_ok=True)
        self.history = HistoryManager(session_temp_dir)
        self.source_image_pil = Image.open(filepath).convert("RGBA")
        
        self.zoom_level = 1.0
        img_w, img_h = self.source_image_pil.size
        self.pan_offset = np.array([img_w / 2.0, img_h / 2.0])

        self.canvas_image_pil = self.source_image_pil.copy()
        self.history.add_step(self.canvas_image_pil)
        self._schedule_core_processing() 
        self.master.after(100, self.update_displays)

    def _get_resized_image_for_label(self, pil_img, lbl_w, lbl_h):
        aspect = pil_img.width / pil_img.height
        if lbl_w / lbl_h > aspect: new_h, new_w = lbl_h, int(lbl_h * aspect)
        else: new_w, new_h = lbl_w, int(lbl_w / aspect)
        return pil_img.resize((new_w, new_h), Image.LANCZOS)
    
    def update_displays(self):
        if not self.canvas_image_pil: return
        self._render_canvas()
        label = self.updated_canvas_preview
        label.update_idletasks()
        lbl_w, lbl_h = label.winfo_width()-2, label.winfo_height()-2
        if lbl_w > 1 and lbl_h > 1:
            resized = self._get_resized_image_for_label(self.canvas_image_pil, lbl_w, lbl_h)
            self.updated_canvas_photo = ImageTk.PhotoImage(resized)
            label.configure(image=self.updated_canvas_photo)

    def _create_brush_stamp(self):
        size = int(self.brush_size)
        if size < 1: size = 1
        
        if self.symbol_index == 0:
            hardness = self.brush_hardness
            y, x = np.ogrid[-size//2:size//2, -size//2:size//2]
            dist_from_center = np.sqrt(x**2 + y**2)
            radius = size / 2.0
            falloff_start_radius = radius * hardness 
            falloff_width = radius - falloff_start_radius
            if falloff_width < 1e-6:
                mask = (dist_from_center <= radius).astype(float)
            else:
                mask = np.clip((radius - dist_from_center) / falloff_width, 0.0, 1.0)
            
            alpha_uint8 = (mask * 255 * self.brush_opacity).astype('uint8')
            stamp = np.zeros((size, size, 4), dtype=np.uint8)
            r, g, b = self.brush_color_rgb
            stamp[..., 0:3] = [r, g, b]
            stamp[..., 3] = alpha_uint8
            self.brush_stamp = Image.fromarray(stamp, 'RGBA')
        else:
            stamp = Image.new('RGBA', (size, size), (0,0,0,0))
            draw = ImageDraw.Draw(stamp)
            symbol = SYMBOLS[self.symbol_index]
            
            try:
                font = ImageFont.truetype("arial.ttf", int(size * 0.9))
            except IOError:
                font = ImageFont.load_default()

            l, t, r, b = draw.textbbox((0, 0), symbol, font=font)
            text_width, text_height = r - l, b - t
            x_pos = (size - text_width - l) / 2
            y_pos = (size - text_height - t) / 2
            
            fill_color = (*self.brush_color_rgb, int(255 * self.brush_opacity))
            draw.text((x_pos, y_pos), symbol, font=font, fill=fill_color)
            self.brush_stamp = stamp

    def _update_brush_props(self, event=None):
        self.brush_opacity = self.opacity_slider.get()
        self.brush_hardness = self.hardness_slider.get()
        self.brush_size = self.size_slider.get()
        self.brush_step = self.step_slider.get()
        self.symbol_index = int(self.symbol_slider.get())
        
        symbol_char = SYMBOLS[self.symbol_index]
        if symbol_char == 'Off':
            self.symbol_swatch.config(text="●")
        else:
            self.symbol_swatch.config(text=symbol_char)

        self._create_brush_stamp()

    def _on_color_picked(self, rgb_tuple):
        self.brush_color_rgb = rgb_tuple
        hex_color = f'#{rgb_tuple[0]:02x}{rgb_tuple[1]:02x}{rgb_tuple[2]:02x}'
        self.color_swatch.config(bg=hex_color)
        self._create_brush_stamp()
    
    def _activate_eyedropper(self, event=None):
        if not self.eyedropper_active: self.eyedropper_active = True; self.canvas.config(cursor="crosshair")
    
    def _deactivate_eyedropper(self, event=None):
        if self.eyedropper_active: self.eyedropper_active = False; self.canvas.config(cursor="none")

    def _canvas_click(self, event):
        if self.eyedropper_active:
            if not self.canvas_image_pil: return
            img_x, img_y = self._canvas_to_image_coords(event.x, event.y)
            img_w, img_h = self.canvas_image_pil.size
            if 0 <= img_x < img_w and 0 <= img_y < img_h:
                r, g, b, _ = self.canvas_image_pil.getpixel((img_x, img_y))
                self._on_color_picked((r, g, b))
                self.color_picker.set_color_from_rgb((r, g, b))

    def _start_paint(self, event):
        if not self.canvas_image_pil or self.eyedropper_active: return
        self.is_painting = True
        self.live_canvas = self.canvas_image_pil.copy()
        self.last_x, self.last_y = event.x, event.y
        self._draw_dab_at_canvas_coords(event.x, event.y)
        self._render_canvas()

    def _paint(self, event):
        if not self.is_painting: return
        
        self._update_cursor_preview(event)
        
        img_coords_last = self._canvas_to_image_coords(self.last_x, self.last_y)
        img_coords_now = self._canvas_to_image_coords(event.x, event.y)
        dist = np.linalg.norm(np.array(img_coords_now) - np.array(img_coords_last))
        
        steps = int(dist / max(1, self.brush_step))
        if steps > 0:
            for i in range(1, steps + 1):
                t = i / float(steps)
                x = int(img_coords_last[0] + (img_coords_now[0] - img_coords_last[0]) * t)
                y = int(img_coords_last[1] + (img_coords_now[1] - img_coords_last[1]) * t)
                self._draw_dab(x, y)
        
        self._render_canvas()
        self.last_x, self.last_y = event.x, event.y

    def _stop_paint(self, event):
        if not self.is_painting: return
        self.is_painting = False
        
        self.canvas_image_pil = self.live_canvas
        self.live_canvas = None
        
        if self.history: self.history.add_step(self.canvas_image_pil)
        self.update_displays()
        self._schedule_core_processing()
    
    def _draw_dab_at_canvas_coords(self, canvas_x, canvas_y):
        img_x, img_y = self._canvas_to_image_coords(canvas_x, canvas_y)
        self._draw_dab(img_x, img_y)

    def _draw_dab(self, img_x, img_y):
        if not self.live_canvas: return
        brush_w, brush_h = self.brush_stamp.size
        paste_x = img_x - brush_w // 2
        paste_y = img_y - brush_h // 2
        
        temp_brush_layer = Image.new('RGBA', self.live_canvas.size, (0,0,0,0))
        temp_brush_layer.paste(self.brush_stamp, (paste_x, paste_y))
        
        self.live_canvas = Image.alpha_composite(self.live_canvas, temp_brush_layer)

    def _schedule_core_processing(self):
        if self.core_update_job_id: self.master.after_cancel(self.core_update_job_id)
        self.core_update_job_id = self.master.after(500, self._send_to_core)

    def _send_to_core(self):
        if not self.canvas_image_pil: return
        job = {"image_pil": self.canvas_image_pil.copy(), "path": self.source_image_path}
        try:
            while not self.core.processing_queue.empty(): self.core.processing_queue.get_nowait()
            self.core.processing_queue.put_nowait(job)
        except (queue.Full, queue.Empty): pass

    def _undo(self):
        if self.history and (path := self.history.undo()):
            self.canvas_image_pil = Image.open(path).convert("RGBA")
            self.update_displays(); self._schedule_core_processing()

    def _redo(self):
        if self.history and (path := self.history.redo()):
            self.canvas_image_pil = Image.open(path).convert("RGBA")
            self.update_displays(); self._schedule_core_processing()

    def _undo_event(self, event): self._undo(); return "break"
    def _redo_event(self, event): self._redo(); return "break"

    def _open_color_chooser(self):
        color = colorchooser.askcolor(title="Choose Brush Color", initialcolor=self.brush_color_rgb)
        if color[0]:
            rgb = tuple(int(c) for c in color[0])
            self._on_color_picked(rgb)
            self.color_picker.set_color_from_rgb(rgb)

    def _on_canvas_enter(self, event): self.canvas.config(cursor="none")
    def _on_canvas_leave(self, event):
        self.canvas.config(cursor="");
        self.canvas.delete("cursor_preview")

    def _update_cursor_preview(self, event):
        self.canvas.delete("cursor_preview")
        if self.eyedropper_active or not self.canvas_image_pil: return
        
        display_size = self.brush_size * self.zoom_level
        x, y = event.x, event.y
        
        self.canvas.create_oval(x - display_size / 2, y - display_size / 2, x + display_size / 2, y + display_size / 2, outline="white", width=1, tags="cursor_preview")

        if self.symbol_index > 0:
            symbol_char = SYMBOLS[self.symbol_index]
            font_size = int(display_size * 0.75)
            self.canvas.create_text(x, y, text=symbol_char, fill="white", font=('Segoe UI', font_size), tags="cursor_preview")

    def on_closing(self):
        if self.external_preview_window:
            self.external_preview_window.destroy()
        self.core.shutdown()
        self.master.destroy()

    def _zoom_scroll(self, event):
        factor = 1.2 if event.delta > 0 else 1/1.2
        self._zoom(factor)
        return "break"

    def _zoom(self, factor):
        if not self.canvas_image_pil: return
        self.zoom_level = np.clip(self.zoom_level * factor, 0.1, 10.0)
        self._render_canvas()

    def _start_pan(self, event): self.last_pan_pos = np.array([event.x, event.y]); self.canvas.config(cursor="fleur")
    def _stop_pan(self, event): self.last_pan_pos = None; self.canvas.config(cursor="none")

    def _pan(self, event):
        if self.last_pan_pos is not None:
            new_pos = np.array([event.x, event.y])
            delta_canvas = new_pos - self.last_pan_pos
            
            self.pan_offset -= delta_canvas / self.zoom_level
            
            self.last_pan_pos = new_pos
            self._render_canvas()

    def _canvas_to_image_coords(self, cx, cy):
        canvas_w, canvas_h = self.canvas.winfo_width(), self.canvas.winfo_height()
        mouse_from_canvas_center = np.array([cx - canvas_w / 2.0, cy - canvas_h / 2.0])
        mouse_offset_img = mouse_from_canvas_center / self.zoom_level
        img_coords = self.pan_offset + mouse_offset_img
        return int(img_coords[0]), int(img_coords[1])

    def _render_canvas(self):
        if not self.canvas_image_pil: return
        canvas_w, canvas_h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if canvas_w <= 1 or canvas_h <= 1: return
        
        source_img = self.canvas_image_pil
        if self.is_painting and self.live_canvas:
            source_img = self.live_canvas

        view_w_img = canvas_w / self.zoom_level
        view_h_img = canvas_h / self.zoom_level
        
        center_x_img, center_y_img = self.pan_offset[0], self.pan_offset[1]
        
        left = int(center_x_img - view_w_img / 2.0)
        top = int(center_y_img - view_h_img / 2.0)
        right = int(center_x_img + view_w_img / 2.0)
        bottom = int(center_y_img + view_h_img / 2.0)
        
        cropped_img = source_img.crop((left, top, right, bottom))
        resized_img = cropped_img.resize((canvas_w, canvas_h), Image.LANCZOS)
        
        self.canvas_bg_photo = ImageTk.PhotoImage(resized_img)
        if self.canvas_bg_id: self.canvas.itemconfig(self.canvas_bg_id, image=self.canvas_bg_photo)
        else: self.canvas_bg_id = self.canvas.create_image(0, 0, anchor="nw", image=self.canvas_bg_photo)