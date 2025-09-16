import os
import shutil
import tkinter as tk
import paintshopui
import paintshopdefs

if __name__ == "__main__":
    if os.path.exists(paintshopdefs.TEMP_DIRECTORY):
        shutil.rmtree(paintshopdefs.TEMP_DIRECTORY)
    os.makedirs(paintshopdefs.TEMP_DIRECTORY, exist_ok=True)
    if not os.path.exists(paintshopdefs.SOURCES_DIRECTORY):
        os.makedirs(paintshopdefs.SOURCES_DIRECTORY)
    if not os.path.exists(paintshopdefs.EMBEDDINGS_DIRECTORY):
        os.makedirs(paintshopdefs.EMBEDDINGS_DIRECTORY)

    root = tk.Tk()
    root.title("PaintShop Studio")
    root.geometry("1200x800")
    
    app = paintshopui.PaintShopApp(master=root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()