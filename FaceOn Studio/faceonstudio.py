import os
import shutil
import tkinter as tk
import faceonstudioui
import faceonstudiodefs
import faceonstudioutils

if __name__ == "__main__":
    if os.path.exists(faceonstudiodefs.TEMP_DIRECTORY):
        shutil.rmtree(faceonstudiodefs.TEMP_DIRECTORY)
    os.makedirs(faceonstudiodefs.TEMP_DIRECTORY, exist_ok=True)
    if not os.path.exists(faceonstudiodefs.SOURCES_DIRECTORY):
        os.makedirs(faceonstudiodefs.SOURCES_DIRECTORY)
    if not os.path.exists(faceonstudiodefs.EMBEDDINGS_DIRECTORY):
        os.makedirs(faceonstudiodefs.EMBEDDINGS_DIRECTORY)

    faceonstudioutils.preprocess_source_images(faceonstudiodefs.SOURCES_DIRECTORY)

    root = tk.Tk()
    root.withdraw() 

    root.configure(bg="#2b2b2b")
    root.title("FaceOn Studio")
    root.geometry("1200x800")
    
    try:
        root.iconbitmap("icon.ico")
    except tk.TclError:
        print("WARN: 'icon.ico' not found. Skipping icon setting.")

    app = faceonstudioui.PaintShopApp(master=root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    root.deiconify()
    root.mainloop()