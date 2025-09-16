# faceonui.py (Final Compact Layout)

import tkinter as tk
from tkinter import ttk,filedialog
import os
import cv2
import numpy as np
from PIL import Image,ImageTk
import faceondefs
from faceonface import Face,dump_safe_face

class TegrityApp(tk.Frame):
    def __init__(self,master=None):
        super().__init__(master)
        self.master=master
        self.master.title("Face On")
        self.master.configure(bg="#2b2b2b")
        self.active_scroll_target="A"
        self.setup_styles()
        self.pack(fill=tk.BOTH,expand=True,padx=10,pady=10)
        self.create_widgets()
        self.update_ui_components()

    def setup_styles(self):
        style=ttk.Style()
        style.theme_use('clam')
        self.bg,self.fg,self.trough,self.border,self.accent="#2b2b2b","#dcdcdc","#3c3f41","#555555","#555555"
        style.configure('.',background=self.bg,foreground=self.fg,font=('Segoe UI',9))
        style.configure('TFrame',background=self.bg)
        style.configure('TLabel',background=self.bg,foreground=self.fg,padding=2)
        style.configure('TLabelframe',background=self.bg,bordercolor=self.accent)
        style.configure('TLabelframe.Label',background=self.bg,foreground=self.fg)
        style.map('TButton',background=[('active','#4a4a4a')])
        style.configure('TButton',background=self.trough,foreground=self.fg,borderwidth=1)
        style.configure('TRadiobutton',background=self.bg,foreground=self.fg,indicatorcolor=self.bg)
        style.map('TRadiobutton',background=[('active',self.bg)],indicatorcolor=[('selected',self.accent),('active',self.accent)])
        style.configure('Horizontal.TScale',background=self.bg,troughcolor=self.trough,sliderthickness=15)
        style.map('TScale',background=[('active',self.accent)])
        style.configure('Active.TLabel',borderwidth=2,relief='solid',bordercolor=self.accent)

    def on_thumbnail_scroll(self,event):
        if not faceondefs.ALL_SOURCE_FACES:return
        direction=-1 if event.delta>0 else 1
        num_faces=len(faceondefs.ALL_SOURCE_FACES)
        if faceondefs.active_mode=="EMAP":
            faceondefs.current_emap_track=(faceondefs.current_emap_track+direction+512)%512
            self.master.after(0,self.update_status_bar)
            return
        target_photo=None
        if faceondefs.active_mode=="Blend" and self.active_scroll_target=="B":
            new_idx=(faceondefs.SELECTED_SOURCE_2_INDEX+direction)%num_faces
            faceondefs.SELECTED_SOURCE_2_INDEX=new_idx
            faceondefs.SELECTED_SOURCE_2=faceondefs.ALL_SOURCE_FACES[new_idx]
            target_photo=self.create_photo(faceondefs.SELECTED_SOURCE_2.thumbnail)
            faceondefs.current_source_photo_B=target_photo
        else:
            new_idx=(faceondefs.SELECTED_SOURCE_1_INDEX+direction)%num_faces
            faceondefs.SELECTED_SOURCE_1_INDEX=new_idx
            faceondefs.SELECTED_SOURCE_1=faceondefs.ALL_SOURCE_FACES[new_idx]
            target_photo=self.create_photo(faceondefs.SELECTED_SOURCE_1.thumbnail)
            faceondefs.current_source_photo_A=target_photo

    def create_widgets(self):
        self.grid_columnconfigure(0,weight=1)
        
        top_frame=ttk.Frame(self)
        top_frame.grid(row=0,column=0,sticky='nsew')
        top_frame.columnconfigure(1,weight=1)
        
        mode_frame=ttk.LabelFrame(top_frame,text="Mode")
        mode_frame.pack(side=tk.LEFT,padx=5,pady=5,fill=tk.Y)
        
        source_frame=ttk.LabelFrame(top_frame,text="Source Selection")
        source_frame.pack(side=tk.LEFT,padx=5,pady=5,expand=True,fill=tk.BOTH)
        
        self.mode_var=tk.StringVar(value=faceondefs.active_mode)
        modes=["Off","Pixdelate","Swap","Blend","Morph","EMAP"]
        for mode in modes:
            rb=ttk.Radiobutton(mode_frame,text=mode,variable=self.mode_var,value=mode,command=self.on_mode_change)
            rb.pack(anchor=tk.W,padx=10,pady=2)
            
        self.preview_frame=ttk.Frame(source_frame)
        self.preview_frame.pack(pady=(15, 5),padx=5)
        
        self.thumb_A=ttk.Label(self.preview_frame,style='TLabel')
        self.thumb_A.pack(side=tk.LEFT,padx=5)
        self.thumb_B=ttk.Label(self.preview_frame,style='TLabel')
        self.thumb_B.pack(side=tk.LEFT,padx=5)
        self.thumb_A.image=self.thumb_B.image=None
        self.thumb_A.bind("<Button-1>",lambda e:self.set_active_scroll_target("A"))
        self.thumb_B.bind("<Button-1>",lambda e:self.set_active_scroll_target("B"))
        self.master.bind_all("<MouseWheel>",self.on_thumbnail_scroll)
        
        self.blend_controls_frame=ttk.Frame(source_frame)
        blend_slider_container=ttk.Frame(self.blend_controls_frame)
        self.blend_var=tk.DoubleVar(value=50)
        ttk.Label(blend_slider_container,text="Blend").pack(side=tk.LEFT,padx=5,pady=2)
        blend_scale=ttk.Scale(blend_slider_container,from_=0,to=100,orient=tk.HORIZONTAL,variable=self.blend_var,command=self.update_blend_label)
        blend_scale.pack(side=tk.LEFT,expand=True,fill=tk.X,padx=5,pady=2)
        self.blend_value_label=ttk.Label(blend_slider_container,text="50%")
        self.blend_value_label.pack(side=tk.LEFT,padx=5,pady=2)
        blend_slider_container.pack(side=tk.LEFT,expand=True,fill=tk.X,padx=5)
        self.save_blend_button=ttk.Button(self.blend_controls_frame,text="Save Blend",command=self.save_blend)
        self.save_blend_button.pack(side=tk.RIGHT,padx=5)
        
        controls_pane=ttk.Frame(self)
        controls_pane.grid(row=1,column=0,sticky='ew')
        
        blending_frame=self.create_slider_group(controls_pane,"Blending Controls")
        self.roi_var=self.add_slider(blending_frame,"ROI Margin",0,152,faceondefs.ROI_MARGIN,"{:.0f}")
        self.feather_var=self.add_slider(blending_frame,"Feather Blur",3,199,faceondefs.MASK_FEATHER,"{:.0f}",self.enforce_odd_blur)
        self.tightness_var=self.add_slider(blending_frame,"Core Tightness",0,82,faceondefs.MASK_CORE_TIGHTNESS,"{:.0f}")
        self.expansion_var=self.add_slider(blending_frame,"Mask Expand",-100,0,faceondefs.MASK_EXPANSION,"{:.0f}")
        
        affine_frame=self.create_slider_group(controls_pane,"Affine Nudge Controls")
        self.affine_x_var=self.add_slider(affine_frame,"X Offset",-50,50,faceondefs.affine_x_offset,"{:.1f}")
        self.affine_y_var=self.add_slider(affine_frame,"Y Offset",-50,50,faceondefs.affine_y_offset,"{:.1f}")
        self.affine_scale_var=self.add_slider(affine_frame,"Scale",0.5,1.5,faceondefs.affine_scale_offset,"{:.2f}")
        self.mouth_y_var=self.add_slider(affine_frame,"Mouth Y Offset",-20,0,faceondefs.mouth_y_offset,"{:.1f}")
        
        # --- CHANGE 1: Moved the "Toggle Preview" button to the controls pane ---
        ttk.Button(controls_pane,text="Toggle Preview",command=self.toggle_preview).pack(fill=tk.X,padx=5,pady=(10,5))

        # --- CHANGE 2: Removed the old actions_frame and the status_label ---
        # The 'actions_frame' and 'status_label' widgets have been completely deleted.
        
        self.on_mode_change()
        self.set_active_scroll_target("A")

    def create_slider_group(self,parent,text):
        frame=ttk.LabelFrame(parent,text=text);frame.pack(fill=tk.X,pady=5,expand=True)
        frame.columnconfigure(1,weight=1)
        return frame

    def add_slider(self,parent,label,from_,to,initial_value,fmt_str,callback=None):
        row_index=len(parent.winfo_children())//3
        var=tk.DoubleVar(value=initial_value)
        ttk.Label(parent,text=label).grid(row=row_index,column=0,sticky='w',padx=5,pady=2)
        scale=ttk.Scale(parent,from_=from_,to=to,orient=tk.HORIZONTAL,variable=var)
        scale.grid(row=row_index,column=1,sticky='ew',padx=5,pady=2)
        value_label=ttk.Label(parent,text=fmt_str.format(initial_value))
        value_label.grid(row=row_index,column=2,padx=5,pady=2)
        def update_slider(value):
            value_label.config(text=fmt_str.format(float(value)))
            self.update_globals()
            if callback:callback(value)
        scale.config(command=update_slider)
        return var

    def update_blend_label(self,value):
        self.blend_value_label.config(text=f"{float(value):.0f}%")
        self.update_globals()

    def on_mode_change(self):
        new_mode=self.mode_var.get()
        faceondefs.active_mode=new_mode
        is_blend_mode=faceondefs.active_mode=="Blend"
        self.blend_controls_frame.pack_forget()
        if is_blend_mode:
            self.thumb_B.pack(side=tk.LEFT,padx=5)
            self.blend_controls_frame.pack(fill=tk.X,pady=(5,0))
        else:
            self.thumb_B.pack_forget()
        self.update_status_bar()
        if not faceondefs.ALL_SOURCE_FACES and faceondefs.active_mode not in ["Off","EMAP","Pixdelate"]:
            self.mode_var.set("EMAP");faceondefs.active_mode="EMAP"
        self.set_active_scroll_target(self.active_scroll_target)

    def set_active_scroll_target(self,target):
        self.active_scroll_target=target
        if faceondefs.active_mode == "Blend":
            self.thumb_A.config(style='Active.TLabel' if target == 'A' else 'TLabel')
            self.thumb_B.config(style='Active.TLabel' if target == 'B' else 'TLabel')
        else:
            self.thumb_A.config(style='Active.TLabel' if target == 'A' else 'TLabel')
            self.thumb_B.config(style='TLabel')

    def update_globals(self,*args):
        faceondefs.ROI_MARGIN=int(self.roi_var.get())
        faceondefs.MASK_FEATHER=int(self.feather_var.get())
        faceondefs.MASK_CORE_TIGHTNESS=int(self.tightness_var.get())
        faceondefs.MASK_EXPANSION=int(self.expansion_var.get())
        faceondefs.affine_x_offset=self.affine_x_var.get()
        faceondefs.affine_y_offset=self.affine_y_var.get()
        faceondefs.affine_scale_offset=self.affine_scale_var.get()
        faceondefs.mouth_y_offset=self.mouth_y_var.get()
        faceondefs.blend_alpha=self.blend_var.get()/100.0

    def enforce_odd_blur(self,value):
        val=int(float(value))
        if val%2==0:self.feather_var.set(val+1)

    def create_photo(self,cv2_img):
        if cv2_img is None:return faceondefs.placeholder_photo
        img_rgb=cv2.cvtColor(cv2_img,cv2.COLOR_BGR2RGB)
        pil_img=Image.fromarray(img_rgb)
        return ImageTk.PhotoImage(image=pil_img)

    def toggle_preview(self):faceondefs.preview_window_visible=not faceondefs.preview_window_visible

    def save_blend(self):
        if faceondefs.active_mode!="Blend" or faceondefs.CURRENT_ACTIVE_EMBEDDING is None:return
        name_a_base=os.path.splitext(faceondefs.SELECTED_SOURCE_1.name)[0]
        name_b_base=os.path.splitext(faceondefs.SELECTED_SOURCE_2.name)[0]
        new_name_base=f"{name_a_base.split(' ')[0]} {name_b_base.split(' ')[-1]}"
        filepath=os.path.join(faceondefs.EMBEDDINGS_DIRECTORY,f"{new_name_base}.safetensors")
        counter=1
        while os.path.exists(filepath):
            filepath=os.path.join(faceondefs.EMBEDDINGS_DIRECTORY,f"{new_name_base}_{counter}.safetensors");counter+=1
        final_name=os.path.basename(filepath)
        placeholder_thumb=np.full((faceondefs.THUMBNAIL_SIZE[1],faceondefs.THUMBNAIL_SIZE[0],3),60,dtype=np.uint8)
        cv2.putText(placeholder_thumb,"BLND",(faceondefs.THUMBNAIL_SIZE[0]//2-35,faceondefs.THUMBNAIL_SIZE[1]//2+10),cv2.FONT_HERSHEY_SIMPLEX,1,(210,210,210),2)
        face_to_save=Face(embedding=faceondefs.CURRENT_ACTIVE_EMBEDDING,name=final_name,thumbnail=placeholder_thumb)
        face_to_save.kps=np.zeros((5,2),dtype=np.float32);face_to_save.bbox=np.zeros(4,dtype=np.float32);face_to_save.det_score=1.0
        try:
            dump_safe_face(face_to_save,filepath)
            faceondefs.ALL_SOURCE_FACES.append(face_to_save)
            self.update_status_bar_timed_message(f"Saved: {os.path.splitext(final_name)[0]}")
        except Exception as e:
            self.update_status_bar_timed_message("Save Failed!")

    def update_ui_components(self):
        if faceondefs.placeholder_photo is None:faceondefs.placeholder_photo=faceondefs.get_placeholder_photo()
        if self.thumb_A.image!=faceondefs.current_source_photo_A:
            photo=faceondefs.current_source_photo_A if faceondefs.current_source_photo_A else faceondefs.placeholder_photo
            self.thumb_A.configure(image=photo);self.thumb_A.image=photo
        if self.thumb_B.image!=faceondefs.current_source_photo_B:
            photo=faceondefs.current_source_photo_B if faceondefs.current_source_photo_B else faceondefs.placeholder_photo
            self.thumb_B.configure(image=photo);self.thumb_B.image=photo
        self.master.after(100,self.update_ui_components)
    
    # --- CHANGE 3: These methods now do nothing, preventing errors. ---
    def update_status_bar(self):
        return

    def update_status_bar_timed_message(self,message,duration=3000):
        return

    def on_closing(self):
        print("INFO: Closing application...")
        faceondefs.running=False
        self.master.destroy()