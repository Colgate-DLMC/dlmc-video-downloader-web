import os
from datetime import datetime
import subprocess
from mailer import send_email
import threading
import yt_dlp

ffmpeg_path = "ffmpeg"
yt_dlp_path ="yt_dlp"
YTDLP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "bin", "yt-dlp")

 
def detect_subtitle_languages(url):
    """
    Queries yt-dlp for available subtitles on a video WITHOUT downloading it.
    Returns a dict with manual and auto-generated caption language codes,
    plus the full list of unique languages available (either type).
    """
    ydl_opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "cookiesfrombrowser": ("chrome",),
        "extractor_args": {"youtube": {"player_client": ["ios"]}},
    }
 
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
 
    manual_subs = info.get("subtitles", {})       # official/manual captions
    auto_subs = info.get("automatic_captions", {}) # auto-generated captions
 
    manual_langs = sorted(manual_subs.keys())
    auto_langs = sorted(auto_subs.keys())
    all_langs = sorted(set(manual_langs) | set(auto_langs))
 
    return {
        "manual_languages": manual_langs,
        "auto_languages": auto_langs,
        "all_available_languages": all_langs,
    }
 
 
def check_language_available(url, language_code):
    """
    Checks whether a SPECIFIC language is available for a video,
    and whether it's manual, auto-generated, both, or not found.
    """
    result = detect_subtitle_languages(url)
 
    has_manual = language_code in result["manual_languages"]
    has_auto = language_code in result["auto_languages"]
 
    if has_manual and has_auto:
        found_as = "both"
    elif has_manual:
        found_as = "manual"
    elif has_auto:
        found_as = "auto"
    else:
        found_as = None
 
    return {
        "language_code": language_code,
        "found": found_as is not None,
        "found_as": found_as,  # "manual", "auto", "both", or None
        "all_available_languages": result["all_available_languages"],
    }



def build_command(url, output_dir, format_choice, subtitle_choice, language=None):
    command = [YTDLP_PATH, "--cookies", "cookies.txt"]

    if format_choice == "video_audio":
        command.extend([
            "-f",
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
            "--merge-output-format",
            "mp4",
            "--restrict-filenames",
            "-o",
            os.path.join(output_dir, "%(title)s.%(ext)s"),
        ])

    elif format_choice == "video_only":
        command.extend([
            "-f",
            "bestvideo[vcodec^=avc1][ext=mp4]/best[vcodec^=avc1]",
            "--restrict-filenames",
            "-o",
            os.path.join(output_dir, "%(title)s.%(ext)s"),
        ])

    elif format_choice == "audio_only":
        command.extend([
            "-x",
            "--audio-format",
            "mp3",
            "--restrict-filenames",
            "-o",
            os.path.join(output_dir, "%(title)s.%(ext)s"),
        ])

    elif format_choice == "audio_only_wav":
        command.extend([
            "-x",
            "--audio-format",
            "wav",
            "--restrict-filenames",
            "-o",
            os.path.join(output_dir, "%(title)s.%(ext)s"),
        ])

    if subtitle_choice == "none":
        pass
    elif subtitle_choice == "embed":
        command.extend([
            "--write-subs",
            "--write-auto-subs",
            "--embed-subs",
        ])
        if language:
            command.extend(["--sub-langs", language])

    elif subtitle_choice == "separate":
        command.extend([
            "--write-subs",
            "--write-auto-subs",
        ])
        if language:
            command.extend(["--sub-langs", language])

    # url is untrusted input. "--" tells yt-dlp's argument parser that
    # everything after this point is positional data, never a flag —
    # even if url is literally the string "--exec=...". This must be
    # the LAST thing appended, after every flag, so nothing downstream
    # of it accidentally gets swallowed as "positional data" too.
    command.extend(["--", url])

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

                    # Email send thread
                if downloads_log[download_id]["email"]:
                    email_thread = threading.Thread(
                        target = send_email,
                        daemon=True,
                        args = (download_id, downloads_log)
                    ) 
                    #starts the email send thread
                    email_thread.start()
                
                


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