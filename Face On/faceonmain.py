# faceonmain.py (Final Polished Version)

import os
import sys
import time
import glob
import threading
import tkinter as tk
from PIL import Image,ImageTk
import cv2
import directport
import faceondefs as defs
import faceonui as ui
import faceonmodels as models
from faceonface import Face

def processing_thread_func():
    try:
        core=models.TegrityCore(defs.MODEL_PATHS)
    except Exception as e:
        print(f"FATAL ERROR in processing thread initialization: {e}")
        defs.running=False
        return
    source_basenames=set()
    for f in glob.glob(os.path.join(defs.SOURCES_DIRECTORY,"*")):
        source_basenames.add(os.path.splitext(os.path.basename(f))[0])
    for f in glob.glob(os.path.join(defs.EMBEDDINGS_DIRECTORY,"*.safetensors")):
        source_basenames.add(os.path.splitext(os.path.basename(f))[0])
    for basename in sorted(list(source_basenames)):
        potential_image_path=""
        for ext in ['.jpg','.jpeg','.png','.webp']:
            test_path=os.path.join(defs.SOURCES_DIRECTORY,basename+ext)
            if os.path.exists(test_path):
                potential_image_path=test_path
                break
        source_file_to_check=potential_image_path if potential_image_path else os.path.join(defs.SOURCES_DIRECTORY,basename)
        if face:=core.process_source(source_file_to_check):
            defs.ALL_SOURCE_FACES.append(face)
    if defs.ALL_SOURCE_FACES:
        defs.SELECTED_SOURCE_1=defs.ALL_SOURCE_FACES[0]
        defs.SELECTED_SOURCE_2=defs.ALL_SOURCE_FACES[1] if len(defs.ALL_SOURCE_FACES)>1 else defs.ALL_SOURCE_FACES[0]
        if defs.SELECTED_SOURCE_1.thumbnail is not None:
            img_rgb_A=cv2.cvtColor(defs.SELECTED_SOURCE_1.thumbnail,cv2.COLOR_BGR2RGB)
            defs.current_source_photo_A=ImageTk.PhotoImage(image=Image.fromarray(img_rgb_A))
        if defs.SELECTED_SOURCE_2.thumbnail is not None:
            img_rgb_B=cv2.cvtColor(defs.SELECTED_SOURCE_2.thumbnail,cv2.COLOR_BGR2RGB)
            defs.current_source_photo_B=ImageTk.PhotoImage(image=Image.fromarray(img_rgb_B))
    else:
        print(f"\n--- WARNING: No source faces found. Only EMAP mode is available. ---\n")
    webcam_cap=cv2.VideoCapture(0)
    if not webcam_cap.isOpened():
        print("FATAL: Could not open webcam.")
        defs.running=False
        return
    webcam_cap.set(cv2.CAP_PROP_FRAME_WIDTH,1280)
    webcam_cap.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
    dp_device=dp_texture=dp_producer=dp_window=None
    try:
        dp_device=directport.DeviceD3D11.create()
    except Exception as e:
        print(f"FATAL: Could not initialize DirectPort device. Error: {e}")
        defs.running=False
        return
    frame_number=0
    cached_faces=[]
    morph_timer=time.time()
    morph_idx_a,morph_idx_b=0,1
    while defs.running:
        if dp_producer is None:
            try:
                print("INFO: Main producer is offline. Initializing...")
                w,h=defs.PREVIEW_SIZE
                dp_texture=dp_device.create_texture(w,h,directport.DXGI_FORMAT.B8G8R8A8_UNORM)
                dp_producer=dp_device.create_producer("TegrityEngine_Output",dp_texture)
                print("INFO: DirectPort Producer 'TegrityEngine_Output' is broadcasting.")
            except Exception as e:
                print(f"FATAL: Could not re-initialize DirectPort producer. Error: {e}")
                defs.running=False
                return
        if defs.preview_window_visible and dp_window is None:
            try:
                preview_window_w = int(defs.PREVIEW_SIZE[0] * defs.PREVIEW_WINDOW_DISPLAY_SCALE)
                preview_window_h = int(defs.PREVIEW_SIZE[1] * defs.PREVIEW_WINDOW_DISPLAY_SCALE)
                dp_window=dp_device.create_window(preview_window_w, preview_window_h,"Tegrity Preview")
            except Exception as e:
                print(f"ERROR: Could not create DirectPort window: {e}")
                defs.preview_window_visible=False
        if not defs.preview_window_visible and dp_window is not None:
            dp_window=None
        if not defs.is_paused:
            ret,frame=webcam_cap.read()
            if not ret:break
            defs.paused_frame=frame.copy()
        else:
            if defs.paused_frame is None:time.sleep(0.1);continue
            frame=defs.paused_frame.copy()
        frame=cv2.flip(frame,1)
        if frame_number%defs.DETECTION_INTERVAL==0 or not cached_faces:
            cached_faces=core.find_target_faces(frame)
        frame_number+=1
        current_output_frame = frame.copy()
        active_source_face=None
        current_time=time.time()
        swapping_modes=["Swap","Blend","Morph","EMAP"]
        if defs.active_mode=="Off":
            pass
        elif defs.active_mode=="Pixdelate":
            if cached_faces:
                for face in cached_faces:
                    x1,y1,x2,y2=[int(c) for c in face.bbox]
                    x1,y1=max(0,x1),max(0,y1)
                    x2,y2=min(current_output_frame.shape[1],x2),min(current_output_frame.shape[0],y2)
                    if x1<x2 and y1<y2:
                        face_roi=current_output_frame[y1:y2,x1:x2]
                        h,w=face_roi.shape[:2]
                        temp=cv2.resize(face_roi,(16,16),interpolation=cv2.INTER_LINEAR)
                        pixelated_face=cv2.resize(temp,(w,h),interpolation=cv2.INTER_NEAREST)
                        current_output_frame[y1:y2,x1:x2]=pixelated_face
        elif defs.active_mode in swapping_modes:
            if defs.active_mode=="EMAP":
                active_source_face=Face(embedding=core.get_emap_vector(defs.current_emap_track))
            elif defs.active_mode=="Swap":
                if defs.SELECTED_SOURCE_1:active_source_face=defs.SELECTED_SOURCE_1
            elif defs.active_mode=="Blend":
                if defs.SELECTED_SOURCE_1 and defs.SELECTED_SOURCE_2:
                    emb1=defs.SELECTED_SOURCE_1.normed_embedding
                    emb2=defs.SELECTED_SOURCE_2.normed_embedding
                    active_source_face=Face(embedding=(1-defs.blend_alpha)*emb1+defs.blend_alpha*emb2,name="blended_face")
            elif defs.active_mode=='Morph':
                if len(defs.ALL_SOURCE_FACES)>=2:
                    alpha=min((current_time-morph_timer)/defs.MORPH_DURATION,1.0)
                    emb1=defs.ALL_SOURCE_FACES[morph_idx_a].normed_embedding
                    emb2=defs.ALL_SOURCE_FACES[morph_idx_b].normed_embedding
                    active_source_face=Face(embedding=(1-alpha)*emb1+alpha*emb2,name="morphed_face")
                    if alpha>=1.0:
                        morph_timer=current_time
                        morph_idx_a,morph_idx_b=morph_idx_b,(morph_idx_b+1)%len(defs.ALL_SOURCE_FACES)
            if active_source_face:
                current_output_frame=core.swap_face(frame,active_source_face,cached_faces)
        defs.CURRENT_ACTIVE_EMBEDDING=active_source_face.embedding if active_source_face is not None else None
        preview_frame=cv2.resize(current_output_frame,defs.PREVIEW_SIZE,interpolation=cv2.INTER_AREA)
        bgra_frame=cv2.cvtColor(preview_frame,cv2.COLOR_BGR2BGRA)
        temp_cpu_texture=dp_device.create_texture(defs.PREVIEW_SIZE[0],defs.PREVIEW_SIZE[1],directport.DXGI_FORMAT.B8G8R8A8_UNORM,bgra_frame)
        dp_device.copy_texture(temp_cpu_texture,dp_texture)
        dp_producer.signal_frame()
        if dp_window:
            if not dp_window.process_events():
                defs.preview_window_visible=False
                continue
            if defs.is_paused:
                paused_text_frame=preview_frame.copy()
                cv2.putText(paused_text_frame,"PAUSED",(20,40),cv2.FONT_HERSHEY_DUPLEX,1.2,(0,0,255),2)
                bgra_frame=cv2.cvtColor(paused_text_frame,cv2.COLOR_BGR2BGRA)
                temp_cpu_texture=dp_device.create_texture(defs.PREVIEW_SIZE[0],defs.PREVIEW_SIZE[1],directport.DXGI_FORMAT.B8G8R8A8_UNORM,bgra_frame)
                dp_device.copy_texture(temp_cpu_texture,dp_texture)
            dp_device.blit(dp_texture,dp_window)
            dp_window.present()
        else:
            time.sleep(0.001)
    webcam_cap.release()
    print("INFO: Processing thread has stopped.")

if __name__=="__main__":
    if not os.path.exists(defs.SOURCES_DIRECTORY):os.makedirs(defs.SOURCES_DIRECTORY)
    if not os.path.exists(defs.EMBEDDINGS_DIRECTORY):os.makedirs(defs.EMBEDDINGS_DIRECTORY)
    if not os.path.exists(defs.EMAP_DIRECTORY):os.makedirs(defs.EMAP_DIRECTORY)
    worker_thread=threading.Thread(target=processing_thread_func,daemon=True)
    worker_thread.start()
    root=tk.Tk()
    root.configure(bg="#2b2b2b")
    
    # --- THIS IS THE ONLY CHANGE ---
    # Adjusted height for a perfect fit.
    root.geometry("500x530")
    
    root.resizable(False,False)
    try:
        root.iconbitmap('Icon.ico')
    except tk.TclError:
        print("WARN: 'Icon.ico' not found. Using default icon.")
    app=ui.TegrityApp(master=root)
    root.protocol("WM_DELETE_WINDOW",app.on_closing)
    app.mainloop()
    worker_thread.join(timeout=1.0)
    print("INFO: Shutdown complete.")