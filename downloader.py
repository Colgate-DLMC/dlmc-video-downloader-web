import os
from datetime import datetime
import subprocess

ffmpeg_path = "ffmpeg"
yt_dlp_path ="yt_dlp"


def run_download(url, output_dir, downloads_log, download_id):
    
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
    
    
    #Command execution process
    # There are 2 places where failure can happen: 
    #   - process when it is executed immediately
    #   - yt-dlp process starts but finishes with an error

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in iter(process.stdout.readline,''):
            #this is where i will create the logic to
            #add the message line to show on the front end
            clean_line = line.strip()
            downloads_log[download_id]["current_message"] = clean_line

            downloads_log[download_id]["log"].append(clean_line)

            if len(downloads_log[download_id]["log"]) > 50:
                    downloads_log[download_id]["log"] = downloads_log[download_id]["log"][-50:]

        process.stdout.close() #does not mean the process succeeded. It only means that yt-dlp finished and closed its outout stream. yt-dlp output stream could have been successfully or an error happened. in which both closes the output steam. It simply means I am done reading from this output pipe. Close it. 
        process.wait()

        if process.returncode == 0:
            downloaded_files = [
                 os.path.join(output_dir, filename)
                 for filename in os.listdir(output_dir)
                 if filename.endswith(".mp4")
            ]

            if downloaded_files:
                downloads_log[download_id]["log"].append("✅ Download completed successfully".strip())
                downloads_log[download_id]["status"] = "done"
                downloads_log[download_id]["error"] = None
                downloads_log[download_id]["file_path"] = downloaded_files[0]
                downloads_log[download_id]["time_completed"] = datetime.now()


        else:
            downloads_log[download_id]["status"] = "error"
            downloads_log[download_id]["error"] = f"yt-dlp failed with exit code {process.returncode}."
            downloads_log[download_id]["log"].append(f"❌ Download failed with exit code {process.returncode} ".strip())
    
    except Exception as e:
        downloads_log[download_id]["status"] = "error"
        downloads_log[download_id]["error"] = str(e)
        downloads_log[download_id]["log"].append(f"⚠️ Unexpected error:  {str(e)}")