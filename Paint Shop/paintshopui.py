import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, colorchooser
import numpy as np
from PIL import Image, ImageDraw, ImageTk
import paintshopdefs
import paintshopcore
import queue

class HistoryManager:
    def __init__(self, temp_dir):
        self.temp_dir = temp_dir
        self.steps = []
        self.current_step = -1
    def add_step(self, image_pil):
        step_index = len(self.steps)
        filepath = os.path.join(self.temp_dir, f"step_{step_index:04d}.png")
        image_pil.save(filepath)
        if self.current_step < len(self.steps) -1:
            self.steps = self.steps[:self.current_step + 1]
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
        self.core = paintshopcore.PaintShopCore()
        self.core.start()
        self.history = None
        self.source_image_path = None
        self.source_image_pil = None
        self.canvas_image_pil = None
        self.last_x, self.last_y = None, None
        self.brush_color_rgb = (255, 0, 0)
        self.brush_size = 20.0
        self.brush_opacity = 1.0
        self.brush_hardness = 0.5
        self.brush_stamp = None
        self.eyedropper_active = False
        self.paint_save_job_id = None
        self.canvas_image_id = None
        self.is_painting = False
        self.paint_update_job_id = None
        self._setup_styles()
        self._create_widgets()
        self._create_brush_stamp()

    def _setup_styles(self):
        self.bg, self.fg, self.trough, self.accent = "#2b2b2b", "#dcdcdc", "#3c3f41", "#555555"
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background=self.bg, foreground=self.fg, font=('Segoe UI', 9))
        style.configure('TFrame', background=self.bg)
        style.configure('TLabel', background=self.bg, foreground=self.fg)
        style.map('TButton', background=[('active', '#4a4a4a')])
        style.configure('TButton', background=self.trough, foreground=self.fg, borderwidth=1)
        style.configure('Horizontal.TScale', background=self.bg, troughcolor=self.trough, sliderthickness=15)
        style.map('TScale', background=[('active', self.accent)])
        style.configure('TPanedWindow', background=self.bg)
        self.configure(bg=self.bg)

    def _create_widgets(self):
        top_frame = ttk.Frame(self, style='TFrame')
        top_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(top_frame, text="Load Image", command=self._load_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Undo", command=self._undo).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Redo", command=self._redo).pack(side=tk.LEFT, padx=5)
        ttk.Label(top_frame, text="Opacity:").pack(side=tk.LEFT, padx=(10, 2))
        self.opacity_slider = ttk.Scale(top_frame, from_=0, to=1, value=1, command=self._update_brush_props)
        self.opacity_slider.pack(side=tk.LEFT, padx=2)
        ttk.Label(top_frame, text="Hardness:").pack(side=tk.LEFT, padx=(10, 2))
        self.hardness_slider = ttk.Scale(top_frame, from_=0, to=1, value=0.5, command=self._update_brush_props)
        self.hardness_slider.pack(side=tk.LEFT, padx=2)
        ttk.Label(top_frame, text="Size:").pack(side=tk.LEFT, padx=(10, 2))
        self.size_slider = ttk.Scale(top_frame, from_=1, to=200, value=20, command=self._update_brush_props)
        self.size_slider.pack(side=tk.LEFT, padx=2)
        self.color_swatch = tk.Label(top_frame, bg="#ff0000", width=3, height=1, relief="sunken")
        self.color_swatch.pack(side=tk.LEFT, padx=(10,5))
        self.color_swatch.bind("<Button-1>", self._pick_color)
        self.eyedropper_button = ttk.Button(top_frame, text="Eyedropper", command=self._toggle_eyedropper)
        self.eyedropper_button.pack(side=tk.LEFT, padx=5)
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, pady=5)
        self.canvas = tk.Canvas(main_pane, bg="#1e1e1e", highlightthickness=0)
        right_pane = ttk.Frame(main_pane, style='TFrame')
        self.original_preview = ttk.Label(right_pane, text="Original", style='TLabel', anchor='center', background="#1e1e1e")
        self.original_preview.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self.live_preview = ttk.Label(right_pane, text="Live Preview", style='TLabel', anchor='center', background="#1e1e1e")
        self.live_preview.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        main_pane.add(self.canvas, weight=3)
        main_pane.add(right_pane, weight=1)
        self.canvas.bind("<B1-Motion>", self._paint)
        self.canvas.bind("<ButtonPress-1>", self._canvas_click)
        self.canvas.bind("<ButtonRelease-1>", self._stop_paint)
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event=None):
        self.master.after(50, self._update_all_views)

    def _load_image(self):
        filepath = filedialog.askopenfilename(initialdir=paintshopdefs.SOURCES_DIRECTORY)
        if not filepath: return
        self.canvas.delete("all")
        self.canvas_image_id = None
        self.source_image_path = filepath
        basename = os.path.splitext(os.path.basename(filepath))[0]
        session_temp_dir = os.path.join(paintshopdefs.TEMP_DIRECTORY, f"{basename}_{int(time.time())}")
        os.makedirs(session_temp_dir, exist_ok=True)
        self.history = HistoryManager(session_temp_dir)
        self.source_image_pil = Image.open(filepath).convert("RGBA")
        self.canvas_image_pil = self.source_image_pil.copy()
        self._schedule_processing() 
        self.master.after(100, self._update_all_views)
        
    def _update_all_views(self):
        if not self.canvas_image_pil: return
        self.canvas.update_idletasks()
        canvas_w, canvas_h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if canvas_w > 1 and canvas_h > 1:
            resized_canvas_img = self.canvas_image_pil.resize((canvas_w, canvas_h), Image.LANCZOS)
            self.canvas_photo = ImageTk.PhotoImage(resized_canvas_img)
            if self.canvas_image_id:
                self.canvas.itemconfig(self.canvas_image_id, image=self.canvas_photo)
            else:
                self.canvas_image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.canvas_photo)
        for label, img_pil in [(self.original_preview, self.source_image_pil), (self.live_preview, self.canvas_image_pil)]:
            if not img_pil: continue
            w, h = img_pil.width, img_pil.height
            label.update_idletasks()
            lbl_w, lbl_h = label.winfo_width()-2, label.winfo_height()-2
            if lbl_w <= 1 or lbl_h <= 1: continue
            aspect = w / h
            if lbl_w / lbl_h > aspect: new_h = lbl_h; new_w = int(new_h * aspect)
            else: new_w = lbl_w; new_h = int(new_w / aspect)
            resized_img = img_pil.resize((new_w, new_h), Image.LANCZOS)
            photo = ImageTk.PhotoImage(resized_img)
            label.configure(image=photo)
            label.image = photo

    def _create_brush_stamp(self):
        size = int(self.brush_size)
        if size < 1: size = 1
        hardness = self.brush_hardness
        
        y, x = np.ogrid[-size//2:size//2, -size//2:size//2]
        dist_from_center = np.sqrt(x**2 + y**2)
        
        radius = size / 2.0
        falloff_start = radius * hardness
        
        if radius - falloff_start < 1e-6:
            mask = (dist_from_center <= radius).astype(float)
        else:
            mask = (radius - dist_from_center) / (radius - falloff_start)
            
        mask = np.clip(mask, 0.0, 1.0)
        
        mask_alpha = (mask * 255 * self.brush_opacity).astype('uint8')
        stamp = Image.new('RGBA', (size, size), (*self.brush_color_rgb, 0))
        stamp.putalpha(Image.fromarray(mask_alpha, 'L'))
        self.brush_stamp = stamp

    def _update_brush_props(self, event=None):
        self.brush_opacity = self.opacity_slider.get()
        self.brush_hardness = self.hardness_slider.get()
        self.brush_size = self.size_slider.get()
        self._create_brush_stamp()

    def _pick_color(self, event):
        color = colorchooser.askcolor(title="Choose Brush Color")
        if color[1]:
            self.color_swatch.config(bg=color[1])
            self.brush_color_rgb = tuple(int(c) for c in color[0])
            self._create_brush_stamp()
    
    def _toggle_eyedropper(self):
        self.eyedropper_active = not self.eyedropper_active
        if self.eyedropper_active:
            self.canvas.config(cursor="crosshair")
            self.eyedropper_button.config(relief="sunken")
        else:
            self.canvas.config(cursor="")
            self.eyedropper_button.config(relief="raised")

    def _canvas_click(self, event):
        if self.eyedropper_active:
            canvas_w, canvas_h = self.canvas.winfo_width(), self.canvas.winfo_height()
            img_w, img_h = self.canvas_image_pil.size
            img_x, img_y = int(event.x * (img_w / canvas_w)), int(event.y * (img_h / canvas_h))
            r, g, b, a = self.canvas_image_pil.getpixel((img_x, img_y))
            self.brush_color_rgb = (r, g, b)
            hex_color = f'#{r:02x}{g:02x}{b:02x}'
            self.color_swatch.config(bg=hex_color)
            self._create_brush_stamp()
            self._toggle_eyedropper()
        else:
            self._start_paint(event)

    def _start_paint(self, event):
        if not self.canvas_image_pil: return
        self.is_painting = True
        self.last_x, self.last_y = event.x, event.y
        self._paint(event)
        self._start_periodic_update()

    def _start_periodic_update(self):
        if self.is_painting:
            self._update_all_views()
            self.paint_update_job_id = self.master.after(33, self._start_periodic_update)

    def _paint(self, event):
        if self.last_x is not None and self.canvas_image_pil and self.brush_stamp:
            canvas_w, canvas_h = self.canvas.winfo_width(), self.canvas.winfo_height()
            img_w, img_h = self.canvas_image_pil.size
            x0, y0, x1, y1 = self.last_x, self.last_y, event.x, event.y
            dist = max(abs(x1-x0), abs(y1-y0))
            steps = int(dist / (self.brush_size / 4)) + 1
            for i in range(steps):
                t = i / steps if steps > 1 else 1.0
                x, y = int(x0 + (x1-x0) * t), int(y0 + (y1-y0) * t)
                img_x, img_y = int(x * (img_w / canvas_w)), int(y * (img_h / canvas_h))
                brush_w, brush_h = self.brush_stamp.size
                paste_x, paste_y = (img_x - brush_w // 2, img_y - brush_h // 2)
                
                # Define the region of interest (ROI)
                roi_box = (paste_x, paste_y, paste_x + brush_w, paste_y + brush_h)
                
                # Crop the destination canvas in the ROI
                dest_roi = self.canvas_image_pil.crop(roi_box)
                
                # Composite the brush stamp over the cropped destination
                composited_roi = Image.alpha_composite(dest_roi, self.brush_stamp)
                
                # Paste the result back onto the canvas
                self.canvas_image_pil.paste(composited_roi, roi_box)

            self.last_x, self.last_y = event.x, event.y

    def _stop_paint(self, event):
        self.is_painting = False
        if self.paint_update_job_id:
            self.master.after_cancel(self.paint_update_job_id)
            self.paint_update_job_id = None
        
        self.last_x, self.last_y = None, None
        self._update_all_views()
        
        if self.paint_save_job_id:
            self.master.after_cancel(self.paint_save_job_id)
        self.paint_save_job_id = self.master.after(1000, self._schedule_processing)

    def _schedule_processing(self):
        if self.paint_save_job_id:
            self.master.after_cancel(self.paint_save_job_id)
            self.paint_save_job_id = None
        if not self.history or not self.canvas_image_pil: return
        self.history.add_step(self.canvas_image_pil)
        job = {"image_pil": self.canvas_image_pil.copy(), "path": self.source_image_path}
        try:
            while not self.core.processing_queue.empty(): self.core.processing_queue.get_nowait()
        except queue.Empty:
            pass
        try: self.core.processing_queue.put_nowait(job)
        except queue.Full:
            pass

    def _undo(self):
        if self.history:
            path = self.history.undo()
            if path:
                self.canvas_image_pil = Image.open(path).convert("RGBA")
                self._update_all_views()
                self._schedule_processing()

    def _redo(self):
        if self.history:
            path = self.history.redo()
            if path:
                self.canvas_image_pil = Image.open(path).convert("RGBA")
                self._update_all_views()
                self._schedule_processing()

    def on_closing(self):
        self.core.shutdown()
        self.master.destroy()