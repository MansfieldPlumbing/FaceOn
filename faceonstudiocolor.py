import tkinter as tk
from tkinter import ttk
import colorsys
from PIL import Image, ImageDraw, ImageTk
import math
import faceonstudiodefs

class ColorPicker(ttk.Frame):
    def __init__(self, master=None, size=200, initial_color=(255, 0, 0), callback=None):
        super().__init__(master)
        self.size = size
        self.callback = callback
        self.center = self.size // 2
        self.wheel_radius = self.size // 2
        self.triangle_radius = int(self.wheel_radius * 0.75)
        
        self.rgb = initial_color
        self.hsv = colorsys.rgb_to_hsv(*(c/255.0 for c in self.rgb))

        self.canvas = tk.Canvas(self, width=self.size, height=self.size, bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack()
        
        self._create_assets()
        self._draw_widgets()

        self.canvas.bind("<Button-1>", self._on_mouse_event)
        self.canvas.bind("<B1-Motion>", self._on_mouse_event)

    def _create_assets(self):
        self.wheel_image = Image.new("RGBA", (self.size, self.size), (0,0,0,0))
        self.triangle_image = Image.new("RGBA", (self.size, self.size), (0,0,0,0))
        
        draw = ImageDraw.Draw(self.wheel_image)
        for y in range(self.size):
            for x in range(self.size):
                dx, dy = x - self.center, y - self.center
                dist = math.sqrt(dx**2 + dy**2)
                if self.wheel_radius * 0.8 < dist < self.wheel_radius:
                    angle = math.atan2(dy, dx)
                    hue = (angle / (2 * math.pi)) % 1.0
                    r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1, 1)]
                    draw.point((x, y), fill=(r, g, b, 255))
        
        self.wheel_photo = ImageTk.PhotoImage(self.wheel_image)
        self._update_triangle()

    def _update_triangle(self):
        self.triangle_image.paste((0,0,0,0), (0,0,self.size,self.size))
        draw = ImageDraw.Draw(self.triangle_image)
        
        p1 = (self.center, self.center - self.triangle_radius)
        p2 = (self.center - int(self.triangle_radius * math.sqrt(3)/2), self.center + self.triangle_radius//2)
        p3 = (self.center + int(self.triangle_radius * math.sqrt(3)/2), self.center + self.triangle_radius//2)

        min_x, max_x = min(p1[0], p2[0], p3[0]), max(p1[0], p2[0], p3[0])
        min_y, max_y = min(p1[1], p2[1], p3[1]), max(p1[1], p2[1], p3[1])

        hue = self.hsv[0]
        c_v1, c_v2, c_v3 = colorsys.hsv_to_rgb(hue, 0, 1), (0,0,0), colorsys.hsv_to_rgb(hue, 1, 1)
        
        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                w1, w2, w3 = self._barycentric((x,y), p1, p2, p3)
                if w1 >= 0 and w2 >= 0 and w3 >= 0:
                    r = int((w1*c_v1[0] + w2*c_v2[0] + w3*c_v3[0]) * 255)
                    g = int((w1*c_v1[1] + w2*c_v2[1] + w3*c_v3[1]) * 255)
                    b = int((w1*c_v1[2] + w2*c_v2[2] + w3*c_v3[2]) * 255)
                    draw.point((x, y), fill=(r, g, b, 255))
        
        self.triangle_photo = ImageTk.PhotoImage(self.triangle_image)

    def _draw_widgets(self):
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.wheel_photo)
        self.canvas.create_image(0, 0, anchor="nw", image=self.triangle_photo)
        self._draw_selectors()

    def _draw_selectors(self):
        angle = self.hsv[0] * 2 * math.pi
        r = self.wheel_radius * 0.9
        x_wheel, y_wheel = self.center + r * math.cos(angle), self.center + r * math.sin(angle)
        self.canvas.create_oval(x_wheel-5, y_wheel-5, x_wheel+5, y_wheel+5, outline="white", width=2, tags="selectors")
        
        s, v = self.hsv[1], self.hsv[2]
        p_white = (self.center, self.center - self.triangle_radius)
        p_black = (self.center - int(self.triangle_radius * math.sqrt(3)/2), self.center + self.triangle_radius//2)
        p_color = (self.center + int(self.triangle_radius * math.sqrt(3)/2), self.center + self.triangle_radius//2)
        
        w_white, w_black, w_color = v * (1-s), (1-v), v * s
        x_tri = w_white * p_white[0] + w_black * p_black[0] + w_color * p_color[0]
        y_tri = w_white * p_white[1] + w_black * p_black[1] + w_color * p_color[1]
        self.canvas.create_oval(x_tri-5, y_tri-5, x_tri+5, y_tri+5, outline="white", width=2, tags="selectors")

    def _on_mouse_event(self, event):
        x, y = event.x, event.y
        dx, dy = x - self.center, y - self.center
        dist = math.sqrt(dx**2 + dy**2)
        
        if self.wheel_radius * 0.8 < dist < self.wheel_radius:
            angle = math.atan2(dy, dx)
            hue = (angle / (2 * math.pi)) % 1.0
            self.hsv = (hue, self.hsv[1], self.hsv[2])
            self._update_triangle()
            self._draw_widgets() 
        else:
            p1 = (self.center, self.center - self.triangle_radius)
            p2 = (self.center - int(self.triangle_radius * math.sqrt(3)/2), self.center + self.triangle_radius//2)
            p3 = (self.center + int(self.triangle_radius * math.sqrt(3)/2), self.center + self.triangle_radius//2)
            w_white, w_black, w_color = self._barycentric((x,y), p1, p2, p3)
            
            if w_white >= 0 and w_black >= 0 and w_color >= 0:
                v = w_white + w_color
                s = w_color / v if v > 1e-6 else 0
                self.hsv = (self.hsv[0], s, v)
            self.canvas.delete("selectors")
            self._draw_selectors()

        self.rgb = tuple(int(c * 255) for c in colorsys.hsv_to_rgb(*self.hsv))
        if self.callback: self.callback(self.rgb)
    
    def _barycentric(self, p, a, b, c):
        try:
            det = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            w_a = ((b[1] - c[1]) * (p[0] - c[0]) + (c[0] - b[0]) * (p[1] - c[1])) / det
            w_b = ((c[1] - a[1]) * (p[0] - c[0]) + (a[0] - c[0]) * (p[1] - c[1])) / det
            w_c = 1 - w_a - w_b
            return w_a, w_b, w_c
        except ZeroDivisionError: return -1,-1,-1

    def set_color_from_rgb(self, rgb):
        self.rgb = rgb
        self.hsv = colorsys.rgb_to_hsv(*(c/255.0 for c in self.rgb))
        self._update_triangle()
        self._draw_widgets()

class LivePreviewWindow(tk.Toplevel):
    def __init__(self, master=None, on_close=None):
        super().__init__(master)
        self.title("FaceOn Studio Preview")
        
        try:
            self.iconbitmap("icon.ico")
        except tk.TclError:
            print("WARN: 'icon.ico' not found for preview window.")

        self.geometry("960x720")
        self.minsize(640, 480)
        self.configure(bg="#2b2b2b")
        self.on_close_callback = on_close
        
        controls_pane = ttk.Frame(self)
        controls_pane.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)
        
        self.preview_label = ttk.Label(self, anchor='center', background="#1e1e1e")
        self.preview_label.pack(fill=tk.BOTH, expand=True, side=tk.TOP, padx=5, pady=(5,0))
        self.image = None
        
        self._style_preview_widgets()
        self._create_sliders(controls_pane)
        
        self.protocol("WM_DELETE_WINDOW", self._handle_close)

    def _style_preview_widgets(self):
        style = ttk.Style(self)
        style.configure('Preview.TLabelframe', borderwidth=0)
        style.configure('Preview.TLabelframe.Label', foreground='#dcdcdc', background='#2b2b2b')

    def _create_sliders(self, parent):
        parent.columnconfigure((0,1), weight=1)

        blending_frame = self.create_slider_group(parent, "Blending Controls")
        blending_frame.grid(row=0, column=0, sticky='nsew', padx=(0,5))
        self.roi_var = self.add_slider(blending_frame, "ROI Margin", 0, 152, faceonstudiodefs.ROI_MARGIN, "{:.0f}")
        self.feather_var = self.add_slider(blending_frame, "Feather Blur", 3, 199, faceonstudiodefs.MASK_FEATHER, "{:.0f}", self.enforce_odd_blur)
        self.tightness_var = self.add_slider(blending_frame, "Core Tightness", 0, 82, faceonstudiodefs.MASK_CORE_TIGHTNESS, "{:.0f}")
        self.expansion_var = self.add_slider(blending_frame, "Mask Expand", -100, 0, faceonstudiodefs.MASK_EXPANSION, "{:.0f}")
        
        affine_frame = self.create_slider_group(parent, "Affine Nudge Controls")
        affine_frame.grid(row=0, column=1, sticky='nsew', padx=(5,0))
        self.affine_x_var = self.add_slider(affine_frame, "X Offset", -50, 50, faceonstudiodefs.affine_x_offset, "{:.1f}")
        self.affine_y_var = self.add_slider(affine_frame, "Y Offset", -50, 50, faceonstudiodefs.affine_y_offset, "{:.1f}")
        self.affine_scale_var = self.add_slider(affine_frame, "Scale", 0.5, 1.5, faceonstudiodefs.affine_scale_offset, "{:.2f}")
        self.mouth_y_var = self.add_slider(affine_frame, "Mouth Y Offset", -20, 0, faceonstudiodefs.mouth_y_offset, "{:.1f}")

    def create_slider_group(self, parent, text):
        frame = ttk.LabelFrame(parent, text=text, style='Preview.TLabelframe')
        frame.columnconfigure(1, weight=1)
        return frame

    def add_slider(self, parent, label, from_, to, initial_value, fmt_str, callback=None):
        row_index = len(parent.winfo_children())
        var = tk.DoubleVar(value=initial_value)
        ttk.Label(parent, text=label).grid(row=row_index, column=0, sticky='w', padx=5, pady=2)
        scale = ttk.Scale(parent, from_=from_, to=to, orient=tk.HORIZONTAL, variable=var)
        scale.grid(row=row_index, column=1, sticky='ew', padx=5, pady=2)
        value_label = ttk.Label(parent, text=fmt_str.format(initial_value), width=5)
        value_label.grid(row=row_index, column=2, padx=5, pady=2)
        
        def update_slider(value):
            value_label.config(text=fmt_str.format(float(value)))
            self.update_globals()
            if callback: callback(value)
        
        scale.config(command=update_slider)
        return var

    def update_globals(self, *args):
        faceonstudiodefs.ROI_MARGIN = int(self.roi_var.get())
        faceonstudiodefs.MASK_FEATHER = int(self.feather_var.get())
        faceonstudiodefs.MASK_CORE_TIGHTNESS = int(self.tightness_var.get())
        faceonstudiodefs.MASK_EXPANSION = int(self.expansion_var.get())
        faceonstudiodefs.affine_x_offset = self.affine_x_var.get()
        faceonstudiodefs.affine_y_offset = self.affine_y_var.get()
        faceonstudiodefs.affine_scale_offset = self.affine_scale_var.get()
        faceonstudiodefs.mouth_y_offset = self.mouth_y_var.get()

    def enforce_odd_blur(self, value):
        val = int(float(value))
        if val % 2 == 0: self.feather_var.set(val + 1)

    def _handle_close(self):
        if self.on_close_callback:
            self.on_close_callback()
        self.destroy()

    def update_image(self, pil_image):
        if not self.winfo_exists(): return
        
        w, h = self.preview_label.winfo_width(), self.preview_label.winfo_height()
        if w <= 1 or h <= 1:
            self.after(50, lambda: self.update_image(pil_image))
            return

        aspect = pil_image.width / pil_image.height
        if w / h > aspect:
            new_h, new_w = h, int(h * aspect)
        else:
            new_w, new_h = w, int(w / aspect)
        
        resized_img = pil_image.resize((new_w, new_h), Image.LANCZOS)
        self.image = ImageTk.PhotoImage(resized_img)
        self.preview_label.configure(image=self.image)