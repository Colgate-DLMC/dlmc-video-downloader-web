On the app version of the video-downlaoder it used os imports for"
``` 
yt_dlp_path = "yt-dlp"
ffmpeg_path = "ffmpeg"
ffmpeg_available = os.path.exists(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK)
```
so the app checks: path.exists("bin/ffmpeg") -> does this path exist on the systems file manager


For the web version, you do not need the old os.path.exists("bin/ffmpeg") because:

DLMC server / Docker container will already have ffmpeg installed
Python environment will already have yt-dlp installed

command = [
        "yt-dlp", <---yt-dlp
        "-f",     <--- -x
        "bestvideo+bestaudio/best", <---audio
        "--merge-output-format",    <--- format
        "mp4",                      <--- mp3
        "-o",                       <--- output file command
        os.path.join(output_dir, "%(title)s.%(ext)s"),    <--- output file name
        url                          <--- URL
    ]

    This command represent yt-dlp -x --audio-format mp3 "URL"
    yt-dlp -f "bestvideo+bestaudio/best" --merge-output-format mp4 -o "/path/to/output_dir/%(title)s.%(ext)s" "YOUR_URL_HERE"                      


stdout means standard output.

    That is the normal text a program prints to the terminal.
    For example, when yt-dlp runs, it prints stuff like:
    [youtube] Extracting URL
    [download] 12.5% of 40.60MiB
    [download] 50.3% of 40.60MiB
    [Merger] Merging formats into mp4

    but stdout=subprocess.PIPE print the output to the terminal. Give that output back to my Python program so I can read it.


stderr means standard error.
    Programs usually have two output streams:
        -stdout = normal messages
        -stderr = error/warning messages

    stderr=subprocess.STDOUT 
    - Send error messages into the same place as normal output
    So instead of having to read two separate streams:
        process.stdout
        process.stderr

        you combine them into one stream:
         -> process.stdout

By default, subprocess output comes back as bytes, not normal Python strings. so i need to apply text=True


command is the command list i built, and subprocess.Popen(command, ...) starts it.

What process.stdout.close() means:
    stdout=subprocess.PIPE

    creates a pipe between yt-dlp and your Python program.
    yt-dlp output ───► pipe ───► Python reads lines

    So this -> process.stdout.close()
    means:
    I am done reading from this output pipe. Close it.

    What happens now that the video download has been successful?
        -where will the video go or be stored so that the user can have access to download it?
        -and whats a good way of deigning this?

    In my downloads folder:
        i can have subfolders that are unique to each donwload_id:
            this is optimal because if individuals where to download a video simultaneously, we dont have to worry about duplicate name because files can have the same name as long as they exist in different folders

    app.py format:


    ```# 1. IMPORTS
    #    - Flask itself (the framework)
    #    - your own downloader module (to call run_download)
    #    - whatever you use to generate unique IDs
    #    - maybe threading (remember the desktop app ran downloads on a background thread...)

    # 2. CREATE THE FLASK APP OBJECT
    #    app = Flask(__name__)

    # 3. GLOBAL STATE
    #    downloads = {}   <-- the one shared dict, lives for the server's lifetime

    # 4. ROUTES (the coordinator's actual jobs):
    #    - a route to SHOW the webpage (serves index.html)
    #    - a route to START a download (POST: generate id, make dict entry, make folder, kick off run_download)
    #    - a route to CHECK status (GET: look up id in downloads, return status + log as JSON)
    #    - a route to GET the finished file (GET: send the actual file back)

    # 5. RUN THE SERVER
    #    app.run(...)
    ```

    