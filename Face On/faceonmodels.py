import os
import sys
import cv2
import numpy as np
import onnx
import onnxruntime
import skimage.transform as trans
from numpy.linalg import norm as l2norm
from onnx import numpy_helper
from typing import List,Dict
import directport
import faceondefs as defs
from faceonface import Face,dump_safe_face,load_safe_face
from faceonfiles import dump_emap_cache,load_emap_cache

arcface_dst=np.array([[38.2946,51.6963],[73.5318,51.5014],[56.0252,71.7366],[41.5493,92.3655],[70.7299,92.2041]],dtype=np.float32)

def estimate_norm(lmk,image_size=112):
    tform=trans.SimilarityTransform()
    adjusted_dst=arcface_dst.copy()
    adjusted_dst[3,1]+=defs.mouth_y_offset
    adjusted_dst[4,1]+=defs.mouth_y_offset
    tform.estimate(lmk,adjusted_dst*(float(image_size)/112.0))
    return tform.params[0:2,:]

def norm_crop2(engine,img,landmark,image_size=112):
    M=estimate_norm(landmark,image_size)
    warped=engine.warp_affine(img,M,(image_size,image_size))
    return warped,M

def distance2bbox(points,distance):
    x1,y1=points[:,0]-distance[:,0],points[:,1]-distance[:,1]
    x2,y2=points[:,0]+distance[:,2],points[:,1]+distance[:,3]
    return np.stack([x1,y1,x2,y2],axis=-1)

def distance2kps(points,distance):
    preds=[points[:,i%2]+distance[:,i] for i in range(distance.shape[1])]
    return np.stack(preds,axis=-1)

class TegrityEngine:
    def __init__(self):
        print("INFO: Initializing Python-native TegrityEngine.")
    def warp_affine(self,src_image_np:np.ndarray,M:np.ndarray,dsize:tuple)->np.ndarray:
        return cv2.warpAffine(src_image_np,M,dsize,borderValue=0.0)
    def process_and_paste_face(self,frame_np:np.ndarray,face_np:np.ndarray,M_inv:np.ndarray,roi:tuple)->np.ndarray:
        roi_x,roi_y,roi_w,roi_h=map(int,roi)
        target_roi_img=frame_np[roi_y:roi_y+roi_h,roi_x:roi_x+roi_w]
        M_inv_roi=M_inv.copy()
        M_inv_roi[0,2]-=roi_x
        M_inv_roi[1,2]-=roi_y
        warped_face_roi=cv2.warpAffine(face_np,M_inv_roi,(roi_w,roi_h))
        mask_roi=np.full(face_np.shape[:2],255,dtype=np.uint8)
        warped_mask_roi=cv2.warpAffine(mask_roi,M_inv_roi,(roi_w,roi_h))
        if defs.MASK_EXPANSION>0:
            expand_kernel=np.ones((defs.MASK_EXPANSION,defs.MASK_EXPANSION),np.uint8)
            processed_mask=cv2.dilate(warped_mask_roi,expand_kernel,iterations=1)
        elif defs.MASK_EXPANSION<0:
            contract_kernel=np.ones((-defs.MASK_EXPANSION,-defs.MASK_EXPANSION),np.uint8)
            processed_mask=cv2.erode(warped_mask_roi,contract_kernel,iterations=1)
        else:
            processed_mask=warped_mask_roi
        feather_ksize=defs.MASK_FEATHER
        if feather_ksize<3:feather_ksize=3
        if feather_ksize%2==0:feather_ksize+=1
        feathered_mask=cv2.GaussianBlur(processed_mask,(feather_ksize,feather_ksize),0)
        if defs.MASK_CORE_TIGHTNESS>0:
            erosion_kernel=np.ones((defs.MASK_CORE_TIGHTNESS,defs.MASK_CORE_TIGHTNESS),np.uint8)
            eroded_core_mask=cv2.erode(processed_mask,erosion_kernel,iterations=1)
            final_mask_roi=np.maximum(feathered_mask,eroded_core_mask)
        else:
            final_mask_roi=feathered_mask
        mask_float=(final_mask_roi.astype(np.float32)/255.0)[:,:,np.newaxis]
        blended_roi=(warped_face_roi*mask_float+target_roi_img*(1-mask_float)).astype(np.uint8)
        frame_np[roi_y:roi_y+roi_h,roi_x:roi_x+roi_w]=blended_roi
        return frame_np

class RetinaFace:
    def __init__(self,model_file=None,providers=None):
        self.session=onnxruntime.InferenceSession(model_file,providers=providers)
        self.center_cache,self.nms_thresh,self.det_thresh={},0.4,0.5
        input_cfg=self.session.get_inputs()[0]
        input_shape=list(input_cfg.shape)
        if not all(isinstance(dim,int) for dim in input_shape[2:]):input_shape[2],input_shape[3]=640,640
        self.input_size=tuple(input_shape[2:4][::-1])
        self.input_name=input_cfg.name
        outputs=self.session.get_outputs()
        self.output_names=[o.name for o in outputs]
        self.use_kps,self.fmc,self._feat_stride_fpn,self._num_anchors=len(outputs)==9,3,[8,16,32],2
    def detect(self,img):
        im_ratio=float(img.shape[0])/img.shape[1]
        model_ratio=float(self.input_size[1])/self.input_size[0]
        new_height,new_width=(self.input_size[1],int(self.input_size[1]/im_ratio)) if im_ratio>model_ratio else (int(self.input_size[0]*im_ratio),self.input_size[0])
        det_scale=float(new_height)/img.shape[0]
        resized_img=cv2.resize(img,(new_width,new_height))
        det_img=np.zeros((self.input_size[1],self.input_size[0],3),dtype=np.uint8)
        det_img[:new_height,:new_width,:]=resized_img
        scores_list,bboxes_list,kpss_list=self.forward(det_img)
        if not scores_list or not bboxes_list:return np.array([]),np.array([])
        scores,order=np.vstack(scores_list).ravel().argsort()[::-1],np.vstack(scores_list).ravel().argsort()[::-1]
        pre_det=np.hstack((np.vstack(bboxes_list)/det_scale,np.vstack(scores_list))).astype(np.float32,copy=False)[order,:]
        keep=self.nms(pre_det)
        det=pre_det[keep,:]
        kpss=np.vstack(kpss_list)[order,:][keep,:]/det_scale if self.use_kps else None
        if kpss is not None:kpss=kpss.reshape((-1,5,2))
        return det,kpss
    def forward(self,img):
        scores_list,bboxes_list,kpss_list=[],[],[]
        blob=cv2.dnn.blobFromImage(img,1.0/128.0,self.input_size,(127.5,127.5,127.5),swapRB=True)
        net_outs=self.session.run(self.output_names,{self.input_name:blob})
        for idx,stride in enumerate(self._feat_stride_fpn):
            height,width=blob.shape[2]//stride,blob.shape[3]//stride
            anchor_centers=self.center_cache.get((height,width,stride))
            if anchor_centers is None:
                anchor_centers=np.stack(np.mgrid[:height,:width][::-1],axis=-1).astype(np.float32)
                anchor_centers=np.stack([(anchor_centers*stride).reshape((-1,2))]*self._num_anchors,axis=1).reshape((-1,2))
                self.center_cache[(height,width,stride)]=anchor_centers
            pos_inds=np.where(net_outs[idx]>=self.det_thresh)[0]
            if not pos_inds.any():continue
            bboxes_list.append(distance2bbox(anchor_centers[pos_inds],(net_outs[idx+self.fmc]*stride)[pos_inds]))
            scores_list.append(net_outs[idx][pos_inds])
            if self.use_kps:kpss_list.append(distance2kps(anchor_centers[pos_inds],(net_outs[idx+self.fmc*2]*stride)[pos_inds]))
        return scores_list,bboxes_list,kpss_list
    def nms(self,dets):
        x1,y1,x2,y2,scores=dets[:,0],dets[:,1],dets[:,2],dets[:,3],dets[:,4]
        areas,order,keep=(x2-x1+1)*(y2-y1+1),scores.argsort()[::-1],[]
        while order.size>0:
            i=order[0];keep.append(i)
            xx1,yy1=np.maximum(x1[i],x1[order[1:]]),np.maximum(y1[i],y1[order[1:]])
            xx2,yy2=np.minimum(x2[i],x2[order[1:]]),np.minimum(y2[i],y2[order[1:]])
            w,h=np.maximum(0.0,xx2-xx1+1),np.maximum(0.0,yy2-yy1+1)
            ovr=(w*h)/(areas[i]+areas[order[1:]]-(w*h))
            order=order[np.where(ovr<=self.nms_thresh)[0]+1]
        return keep

class ArcFaceONNX:
    def __init__(self,model_file,providers,engine):
        self.engine,self.session=engine,onnxruntime.InferenceSession(model_file,providers=providers)
        self.input_name=self.session.get_inputs()[0].name
        self.input_size=tuple(self.session.get_inputs()[0].shape[2:4][::-1])
    def get(self,img,face):
        warped,_=norm_crop2(self.engine,img,landmark=face.kps,image_size=self.input_size[0])
        blob=cv2.dnn.blobFromImage(warped,1.0/127.5,self.input_size,(127.5,127.5,127.5),swapRB=True)
        face.embedding=self.session.run(None,{self.input_name:blob})[0].flatten()

class INSwapper:
    def __init__(self,model_file,providers,engine):
        self.engine=engine
        self.session=onnxruntime.InferenceSession(model_file,providers=providers)
        cache_path=os.path.join(defs.EMAP_DIRECTORY,"emap_cache.safetensors")
        if os.path.exists(cache_path):
            try:
                self.emap=load_emap_cache(cache_path)
            except Exception as e:
                self.emap=numpy_helper.to_array(onnx.load(model_file).graph.initializer[-1])
                dump_emap_cache(self.emap,cache_path)
        else:
            self.emap=numpy_helper.to_array(onnx.load(model_file).graph.initializer[-1])
            try:
                dump_emap_cache(self.emap,cache_path)
            except Exception as e:
                print(f"WARN: Could not save EMAP cache. Error: {e}")
        inputs=self.session.get_inputs()
        self.input_names=[inp.name for inp in inputs]
        self.input_size=tuple(inputs[0].shape[2:4][::-1])
    def get(self,img,target_face,source_face):
        aimg,M=norm_crop2(self.engine,img,target_face.kps,self.input_size[0])
        blob=cv2.dnn.blobFromImage(aimg,1.0/255.0,self.input_size,(0.0,0.0,0.0),swapRB=True)
        latent=source_face.normed_embedding.reshape((1,-1))
        if source_face.name!='Emap Archetype':
            latent_dot=np.dot(latent,self.emap)
            latent=latent_dot/np.linalg.norm(latent)
        pred=self.session.run(None,{self.input_names[0]:blob,self.input_names[1]:latent})[0]
        img_fake=np.clip(255*pred.transpose((0,2,3,1))[0],0,255).astype(np.uint8)[:,:,::-1]
        M_inv=cv2.invertAffineTransform(M)
        M_adjusted=M_inv.copy()
        M_adjusted[0:2,0:2]*=defs.affine_scale_offset
        M_adjusted[0,2]+=defs.affine_x_offset
        M_adjusted[1,2]+=defs.affine_y_offset
        x1,y1,x2,y2=target_face.bbox.astype(int)
        roi_x=max(0,x1-defs.ROI_MARGIN)
        roi_y=max(0,y1-defs.ROI_MARGIN)
        roi_w=min(img.shape[1],x2+defs.ROI_MARGIN)-roi_x
        roi_h=min(img.shape[0],y2+defs.ROI_MARGIN)-roi_y
        roi=(roi_x,roi_y,roi_w,roi_h)
        return self.engine.process_and_paste_face(img,img_fake,M_adjusted,roi)

class TegrityCore:
    def __init__(self,model_paths:Dict[str,str]):
        self.engine=TegrityEngine()
        providers=['DmlExecutionProvider','CPUExecutionProvider']
        print("--- LOADING TEGRITY CORE ---")
        try:
            self.face_detector=RetinaFace(model_file=model_paths['det'],providers=providers)
            self.face_recognizer=ArcFaceONNX(model_file=model_paths['rec'],providers=providers,engine=self.engine)
            self.face_swapper=INSwapper(model_file=model_paths['swap'],providers=providers,engine=self.engine)
            print(f"INFO: All models loaded via {onnxruntime.get_device()}")
        except Exception as e:print(f"--- FATAL ERROR: Failed to load models: {e} ---");raise e
    def get_emap_vector(self,index:int):return self.face_swapper.emap[index]
    def process_source(self,source_path:str):
        base_filename=os.path.splitext(os.path.basename(source_path))[0]
        cache_path=os.path.join(defs.EMBEDDINGS_DIRECTORY,base_filename+".safetensors")
        if os.path.exists(cache_path):
            try:
                face=load_safe_face(cache_path)
                return face
            except Exception as e:
                print(f"WARN: Could not load cache file. Re-processing. Error: {e}")
        if not os.path.isfile(source_path):return None
        img=cv2.imread(source_path)
        if img is None:return None
        bboxes,kpss=self.face_detector.detect(img)
        if bboxes.shape[0]==0:
            return None
        face=Face(bbox=bboxes[0][:4],kps=kpss[0],det_score=bboxes[0][4])
        self.face_recognizer.get(img,face)
        face.name=os.path.basename(source_path)
        x1,y1,x2,y2=face.bbox.astype(int)
        face_crop=img[max(0,y1):y2,max(0,x1):x2]
        if face_crop.size>0:
            face.thumbnail=cv2.resize(face_crop,defs.THUMBNAIL_SIZE)
        try:
            dump_safe_face(face,cache_path)
        except Exception as e:
            print(f"WARN: Could not save cache file. Error: {e}")
        return face
    def find_target_faces(self,frame:np.ndarray):
        bboxes,kpss=self.face_detector.detect(frame)
        if bboxes.shape[0]==0:return[]
        return[Face(bbox=bboxes[i][:4],kps=kpss[i],det_score=bboxes[i][4]) for i in range(len(kpss))]
    def swap_face(self,frame:np.ndarray,source_face:Face,faces_to_swap:List[Face]):
        if source_face is None or not faces_to_swap:return frame
        result=frame.copy()
        for target in faces_to_swap:result=self.face_swapper.get(result,target,source_face)
        return result