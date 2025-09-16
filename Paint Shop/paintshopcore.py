import os
import cv2
import time
import queue
import threading
import numpy as np
import directport
import paintshopdefs
import paintshopmodels
from paintshopface import load_safe_face

class PaintShopCore:
    def __init__(self):
        self.is_running = True
        self.processing_queue = queue.Queue(maxsize=1)
        self.face_lock = threading.Lock()
        self.current_source_face = None
        self.models = paintshopmodels.TegrityCore(paintshopdefs.MODEL_PATHS)
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self.thread.start()

    def shutdown(self):
        self.is_running = False
        self.processing_queue.put(None) # Unblock the queue if it's waiting
        self.thread.join(timeout=2.0)

    def run(self):
        dp_device, webcam_cap = None, None
        try:
            dp_device = directport.DeviceD3D11.create()
            w, h = 1280, 720
            dp_texture = dp_device.create_texture(w, h, directport.DXGI_FORMAT.B8G8R8A8_UNORM)
            producer_name = f"PaintShopStudio_{os.getpid()}"
            dp_producer = dp_device.create_producer(producer_name, dp_texture)
            print(f"INFO: Broadcasting as Producer '{producer_name}'.")

            webcam_cap = cv2.VideoCapture(0)
            webcam_cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            webcam_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
            if not webcam_cap.isOpened():
                print("ERROR: Core could not open webcam.")
                return

            while self.is_running:
                try:
                    image_to_process = self.processing_queue.get_nowait()
                    if image_to_process is None: break
                    
                    image_cv = cv2.cvtColor(np.array(image_to_process["image_pil"]), cv2.COLOR_RGBA2BGR)
                    new_face = self.models.process_image_to_face(image_cv, image_to_process["path"])
                    if new_face:
                        with self.face_lock:
                            self.current_source_face = new_face
                except queue.Empty:
                    pass

                ret, frame = webcam_cap.read()
                if not ret:
                    time.sleep(0.01)
                    continue
                
                frame = cv2.flip(frame, 1)
                
                processed_frame = frame
                with self.face_lock:
                    if self.current_source_face:
                        target_faces = self.models.find_target_faces(frame)
                        processed_frame = self.models.swap_face(frame, self.current_source_face, target_faces)

                # FIX: Resize the final frame to match the producer's dimensions exactly.
                # This resolves stride/resolution mismatch issues.
                resized_frame = cv2.resize(processed_frame, (w, h), interpolation=cv2.INTER_AREA)
                
                bgra_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2BGRA)
                
                temp_tex = dp_device.create_texture(w, h, directport.DXGI_FORMAT.B8G8R8A8_UNORM, bgra_frame)
                dp_device.copy_texture(temp_tex, dp_texture)
                dp_producer.signal_frame()

        except Exception as e:
            print(f"ERROR in PaintShopCore thread: {e}")
        finally:
            if webcam_cap: webcam_cap.release()
            print("INFO: Core thread has stopped.")