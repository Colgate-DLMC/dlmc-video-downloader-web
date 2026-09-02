import os
import time
import shutil

base_dir = os.path.dirname(os.path.abspath(__file__))

# Dynamic path to the downloads folder
folder = os.path.join(base_dir, "video_downloads")

if os.path.exists(folder):
    now = time.time()
    for filename in os.listdir(folder):
        file_path = os.path.join(folder,filename)


        if os.path.isdir(file_path):
            if now - os.path.getmtime(file_path) > 86400:
                shutil.rmtree(file_path)