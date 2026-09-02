from flask import Flask, request, jsonify, render_template, send_file          
from downloader import run_download
from concurrent.futures import ThreadPoolExecutor
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from urllib.parse import urlparse

import uuid
import threading
import os
import datetime
from downloader import  build_command
import re
from mailer import send_email



app = Flask(__name__)


# This single object manages BOTH the 5 active slots AND the invisible waiting queue
executor = ThreadPoolExecutor(max_workers=5) 

limiter = Limiter(
    get_remote_address,   # tells Flask-Limiter to key limits by request.remote_addr
    app=app,
    default_limits=[]     # no global default — we'll set it per-route below
)

downloads_log= {}
DOWNLOADS_ROOT = "video_downloads"
EMAIL_PATTERN = re.compile(r'^[\w.+-]+@[\w-]+\.[\w.-]+$')


#create video job id
def create_unique_id():
    return str(uuid.uuid4())

def validate_url(url_string):
    # Parse the URL
    parsed_url = urlparse(url_string)
    # Check scheme requirements
    if parsed_url.scheme not in ('http', 'https') or not parsed_url.netloc:
        return False
    return True

#route to launch the webpage
@app.route("/")
def index():
    return render_template("index.html")



#route to start a download
@app.route("/download", methods= ["POST"])
@limiter.limit("10 per minute")
def start_download():
    parse_data_request = request.get_json()
    url = parse_data_request.get('url')

    #URL scheme allowlist
    if not validate_url(url):
        return jsonify({"error": "Invalid URL scheme or missing host"}), 400

    #3 create unique ID for THIS download
    download_id = create_unique_id()

    #4 create video download output directory for that id
    output_dir = os.path.join(DOWNLOADS_ROOT, download_id)
    os.makedirs(output_dir, exist_ok=True)

    #5 grab format elements for build command + grab email
    format = parse_data_request.get('format')
    subtitles = parse_data_request.get('subtitles')
    command = build_command(url, output_dir, format, subtitles)
    email = parse_data_request.get('email')

    if email and not EMAIL_PATTERN.match(email):
        return {"error": "Invalid email format"}, 400



    # 1. Initialize the log entry exactly ONCE here in the main route.
    # This immediately saves the state as "queued" while it waits for a thread.
    downloads_log[download_id] = {
        "status": "queued",
        "current_message": "Waiting to start...",
        "log": [],
        "email": email,
        "file_path": None,
        "subtitle_path": None,
        "error": None,
    }

    # 2. Submits the job to the thread pool executor
    executor.submit(
        handle_background_download,
        download_id,
        command,
        output_dir,
        downloads_log
    )


    return jsonify({
        "download_id": download_id,
        "status": "queued" 
    })

def handle_background_download(download_id, command, output_dir, downloads_log):
    # The exact millisecond a worker is free and picks up this task, 
    # i dynamically flip the status to "downloading".
    if download_id in downloads_log:
        downloads_log[download_id]["status"] = "downloading"
        downloads_log[download_id]["current_message"] = "Download started..."

    # Calls the actual heavy yt-dlp download function
    run_download(command, output_dir, downloads_log, download_id)


#route to show status  
@app.route("/status/<download_id>", methods= ["GET"])
def check_status(download_id):
    if download_id in downloads_log:
        return jsonify(downloads_log[download_id])
    return jsonify({"error": "Download ID not Found"}), 404



#route to get the finished file    
@app.route("/file/<download_id>", methods= ["GET"])
@app.route("/file/<download_id>/<file_type>", methods=["GET"])
def get_finished_file(download_id, file_type='main'):
    download_job = downloads_log.get(download_id)

    if download_job is None:
        return jsonify({"error" : "Download NOT Found"}), 404
    
    if download_job["status"] != "done" :
        return jsonify({"error" : "Download NOT ready yet"}), 409
    
    if file_type == "subtitle":
        file_path = download_job.get("subtitle_path")
    else:
        file_path = download_job.get("file_path")

    if file_path is None or not os.path.exists(file_path):
        return jsonify({"error" : "File not Found"}), 404
    
    return send_file(file_path, as_attachment=True) #sends as a downloadable attachment
 
if __name__ == "__main__":
    is_production = os.environ.get("ENV") == "production"
    app.run(debug=not is_production, port=5001)