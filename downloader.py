import os
from datetime import datetime
import subprocess

ffmpeg_path = "ffmpeg"
yt_dlp_path ="yt_dlp"



def build_command(url, output_dir, format_choice, subtitle_choice):
    command = ["yt-dlp"]

    if format_choice == "video_audio":
        video_audio_cmd = [
            "-f", 
            "bestvideo[vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[vcodec^=avc1]/best",
            "--merge-output-format",
            "mp4",
            "--restrict-filenames",
            "-o",
            os.path.join(output_dir, "%(title)s.%(ext)s"),
            url
        ]
        command.extend(video_audio_cmd)

    elif format_choice == "video_only":
        video_only_cmd = [
            "-f",
            "bestvideo[vcodec^=avc1][ext=mp4]/best[vcodec^=avc1]",
            "--restrict-filenames",
            "-o",
            os.path.join(output_dir, "%(title)s.%(ext)s"),
            url
        ]
        command.extend(video_only_cmd)

    elif format_choice == "audio_only":
        audio_only_cmd = [
            "-x",
            "--audio-format",
            "mp3",
            "--restrict-filenames",
            "-o",
            os.path.join(output_dir, "%(title)s.%(ext)s"),
            url
        ]
        command.extend(audio_only_cmd)

    #For future wav file
    # elif format_choice == "audio_only_wav":
    #     audio_only_cmd = [
    #         "-x",
    #         "--audio-format",
    #         "wav",
    #         "--restrict-filenames",
    #         "-o",
    #         os.path.join(output_dir, "%(title)s.%(ext)s"),
    #         url
    #     ]
    #     command.extend(audio_only_cmd)

    if subtitle_choice == "none":
        pass

    elif subtitle_choice == "embed":
        embed_cmd = [
            "--write-subs",
            "--write-auto-subs",
            "--embed-subs"
        ]
        command.extend(embed_cmd)

    elif subtitle_choice == "separate":
        separate_cmd = [
            "--write-subs",
            "--write-auto-subs",
        ]
        command.extend(separate_cmd)



    return command


def run_download(command, output_dir, downloads_log, download_id):
    

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

            """
            main_files catches everything that isnt a subtitle file such as 
            .mp4 (video_audio or video_only downloads) and .mp3(audio_only downloads)

            down below is a filtering of everything besides subtitles (.vtt & .srt): video and audio files
            because video and audio files are considered my "Main Files"
            """
            subtitle_endings = (".srt", ".vtt")
            main_files = [
                os.path.join(output_dir, filename)
                for filename in os.listdir(output_dir)
                if not filename.endswith(subtitle_endings)
            ]

            """
            sub_files represents the case where user choose
            to Download subtitles as separate file. When these choose that option,
            those files will be added as part of the download
            """
            sub_files = [
                os.path.join(output_dir, filename)
                for filename in os.listdir(output_dir)
                if filename.endswith(subtitle_endings)
            ]
        
            if main_files:
                downloads_log[download_id]["log"].append("✅ Download completed successfully".strip())
                downloads_log[download_id]["status"] = "done"
                downloads_log[download_id]["error"] = None
                downloads_log[download_id]["file_path"] = main_files[0]
                downloads_log[download_id]["subtitle_path"] = sub_files[0] if sub_files else None
                downloads_log[download_id]["time_completed"] = datetime.now()

            else:
                downloads_log[download_id]["status"] = "error"
                downloads_log[download_id]["error"] = f"yt-dlp failed with exit code {process.returncode}."
                downloads_log[download_id]["log"].append(f"❌ Download failed with exit code {process.returncode} ".strip())
        else:
            # the subprocess itself failed
            downloads_log[download_id]["status"] = "error"
            downloads_log[download_id]["error"] = f"yt-dlp failed with exit code {process.returncode}."
            downloads_log[download_id]["log"].append(f"❌ Download failed with exit code {process.returncode}")
    
    except Exception as e:
        downloads_log[download_id]["status"] = "error"
        downloads_log[download_id]["error"] = str(e)
        downloads_log[download_id]["log"].append(f"⚠️ Unexpected error:  {str(e)}")