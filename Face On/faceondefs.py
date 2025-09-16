import os
import cv2
import numpy as np
from PIL import Image,ImageTk

SOURCES_DIRECTORY="sources"
EMBEDDINGS_DIRECTORY="embeddings"
EMAP_DIRECTORY="emap"
PREVIEW_SIZE=(1920,1080)
DETECTION_INTERVAL=1
THUMBNAIL_SIZE=(128,128)
MORPH_DURATION=3.0

MODEL_PATHS={
    "swap":os.path.join("models","inswapper_128.onnx"),
    "det":os.path.join("models","det_10g.onnx"),
    "rec":os.path.join("models","w600k_r50.onnx")
}

ALL_SOURCE_FACES=[]
SELECTED_SOURCE_1,SELECTED_SOURCE_2=None,None
SELECTED_SOURCE_1_INDEX,SELECTED_SOURCE_2_INDEX=0,0
is_paused=False
paused_frame=None
active_mode="Off"
running=True
preview_window_visible=False
current_emap_track=0
blend_alpha=0.5
CURRENT_ACTIVE_EMBEDDING=None

current_source_photo_A=None
current_source_photo_B=None
placeholder_photo=None

ROI_MARGIN=76
MASK_FEATHER=101
MASK_CORE_TIGHTNESS=41
MASK_EXPANSION=-50
affine_x_offset=0.0
affine_y_offset=0.0
affine_scale_offset=1.0
mouth_y_offset=-20.0

PREVIEW_WINDOW_DISPLAY_SCALE = 0.25

def get_placeholder_photo():
    placeholder=np.full((THUMBNAIL_SIZE[1],THUMBNAIL_SIZE[0],3),40,dtype=np.uint8)
    cv2.putText(placeholder,"EMPTY",(THUMBNAIL_SIZE[0]//2-30,THUMBNAIL_SIZE[1]//2+10),
                cv2.FONT_HERSHEY_SIMPLEX,0.8,(200,200,200),2)
    img_rgb=cv2.cvtColor(placeholder,cv2.COLOR_BGR2RGB)
    pil_img=Image.fromarray(img_rgb)
    return ImageTk.PhotoImage(image=pil_img)