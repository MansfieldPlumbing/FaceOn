# faceonstudiofiles.py

import json
import struct
import numpy as np

def dump_emap_cache(emap_array:np.ndarray,filepath:str):
    metadata={
        'emap':{
            'dtype':str(emap_array.dtype),
            'shape':list(emap_array.shape),
            'offsets':(0,emap_array.nbytes)
        }
    }
    header_bytes=json.dumps(metadata).encode('utf-8')
    header_len_bytes=struct.pack('<Q',len(header_bytes))
    data_blob=emap_array.tobytes()
    with open(filepath,'wb') as f:
        f.write(header_len_bytes)
        f.write(header_bytes)
        f.write(data_blob)

def load_emap_cache(filepath:str)->np.ndarray:
    with open(filepath,'rb') as f:
        header_len=struct.unpack('<Q',f.read(8))[0]
        metadata=json.loads(f.read(header_len).decode('utf-8'))
        tensor_info=metadata['emap']
        dtype=np.dtype(tensor_info['dtype'])
        shape=tuple(tensor_info['shape'])
        data_blob=f.read()
        return np.frombuffer(data_blob,dtype=dtype).reshape(shape)