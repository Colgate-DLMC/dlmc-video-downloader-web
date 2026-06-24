import os

ffmpeg_path = "ffmpeg"
yt_dlp_path ="yt_dlp"


def run_download(url, output_dir, downloads, download_id):
    
    command = [
        "yt-dlp", 
        "-f", 
        "bestvideo+bestaudio/best",
        "--merge-output-format",
        "mp4",
        "-o",
        os.path.join(output_dir, "%(title)s.%(ext)s"),
        url
    ]