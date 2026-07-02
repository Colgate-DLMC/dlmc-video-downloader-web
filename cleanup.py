import os
import time
import shutil

folder = "/home/tobiloba/Desktop/DLMC-projects/dlmc-video-downloader-web/video_downloads"

if os.path.exists(folder):
    now = time.time()
    for filename in os.listdir(folder):
        file_path = os.path.join(folder,filename)


        if os.path.isdir(file_path):
            if now - os.path.getmtime(file_path) > 3600:
                shutil.rmtree(file_path)