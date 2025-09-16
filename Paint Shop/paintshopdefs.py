import os

SOURCES_DIRECTORY="sources"
EMBEDDINGS_DIRECTORY="embeddings"
EMAP_DIRECTORY="emap"
TEMP_DIRECTORY="temp_paintshop"
THUMBNAIL_SIZE=(128,128)

MODEL_PATHS={
    "swap":os.path.join("models","inswapper_128.onnx"),
    "det":os.path.join("models","det_10g.onnx"),
    "rec":os.path.join("models","w600k_r50.onnx")
}

ROI_MARGIN=76
MASK_FEATHER=101
MASK_CORE_TIGHTNESS=41
MASK_EXPANSION=-50
affine_x_offset=0.0
affine_y_offset=0.0
affine_scale_offset=1.0
mouth_y_offset=-20.0