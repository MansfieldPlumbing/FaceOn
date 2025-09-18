# faceonstudioface.py

import json
import struct
import numpy as np
from numpy.linalg import norm as l2norm

class Face(dict):
    def __init__(self,d=None,**kwargs):
        if d is None:d={}
        if kwargs:d.update(**kwargs)
        for k,v in d.items():setattr(self,k,v)
        if 'name' not in d and 'name' not in kwargs:self.name='Emap Archetype'
        if 'thumbnail' not in d and 'thumbnail' not in kwargs:self.thumbnail=None
    def __setattr__(self,name,value):
        if isinstance(value,(list,tuple)):value=[self.__class__(x) if isinstance(x,dict) else x for x in value]
        elif isinstance(value,dict) and not isinstance(value,self.__class__):value=self.__class__(value)
        super(Face,self).__setattr__(name,value)
        super(Face,self).__setitem__(name,value)
    __setitem__=__setattr__
    def __getattr__(self,name):return None
    @property
    def normed_embedding(self):
        if self.embedding is None:return None
        norm=l2norm(self.embedding)
        return self.embedding/norm if norm!=0 else self.embedding

def dump_safe_face(face:Face,filepath:str):
    metadata={}
    tensor_data={}
    simple_metadata={'name':face.name,'det_score':float(face.det_score)}
    metadata['__metadata__']=simple_metadata
    for key,value in face.items():
        if isinstance(value,np.ndarray):
            tensor_data[key]=value
    data_blob_parts=[]
    current_offset=0
    for key,tensor in tensor_data.items():
        tensor_bytes=tensor.tobytes()
        byte_len=len(tensor_bytes)
        metadata[key]={
            'dtype':str(tensor.dtype),
            'shape':list(tensor.shape),
            'offsets':(current_offset,current_offset+byte_len)
        }
        data_blob_parts.append(tensor_bytes)
        current_offset+=byte_len
    data_blob=b''.join(data_blob_parts)
    header_bytes=json.dumps(metadata,indent=4).encode('utf-8')
    header_len_bytes=struct.pack('<Q',len(header_bytes))
    with open(filepath,'wb') as f:
        f.write(header_len_bytes)
        f.write(header_bytes)
        f.write(data_blob)

def load_safe_face(filepath:str)->Face:
    with open(filepath,'rb') as f:
        header_len=struct.unpack('<Q',f.read(8))[0]
        header_bytes=f.read(header_len)
        metadata=json.loads(header_bytes.decode('utf-8'))
        data_start_offset=f.tell()
        face_args={}
        face_args.update(metadata.get('__metadata__',{}))
        tensor_keys=[k for k in metadata.keys() if k!='__metadata__']
        for key in tensor_keys:
            tensor_info=metadata[key]
            dtype=np.dtype(tensor_info['dtype'])
            shape=tuple(tensor_info['shape'])
            offsets=tensor_info['offsets']
            num_bytes=offsets[1]-offsets[0]
            f.seek(data_start_offset+offsets[0])
            tensor_bytes=f.read(num_bytes)
            array=np.frombuffer(tensor_bytes,dtype=dtype).reshape(shape)
            face_args[key]=array
        return Face(**face_args)