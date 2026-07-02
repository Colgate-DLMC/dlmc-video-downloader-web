from flask import Flask, request, jsonify, render_template, send_file
from downloader import run_download

import uuid
import threading
import os
import datetime


app = Flask(__name__)


downloads_log= {}
DOWNLOADS_ROOT = "video_downloads"



#create video job id
def create_unique_id():
    return str(uuid.uuid4())

#route to launch the webpage
@app.route("/")
def index():
    return render_template("index.html")

#route to start a download
@app.route("/download", methods= ["POST"])
def start_download():
    #Steps to get video url

    #1. Parse the incoming JSON data
    parse_data_request = request.get_json()
    #2. Access the element like a standard python dictionary
    url = parse_data_request.get('url')
    #3 create unique ID for THIS download
    download_id = create_unique_id()

    #4 create video download output directory for that id
    output_dir = os.path.join(DOWNLOADS_ROOT, download_id)
    os.makedirs(output_dir, exist_ok=True)

    #3. create the dict entry
    downloads_log[download_id] = {
        "status": "queued",
        "current_message": "Waiting to start...",
        "log" : [],
        "file_path" : None,
        "error" : None,

    }

    # start background thread
    download_thread = threading.Thread(
        target = run_download,
        daemon=True,
        args = (url, output_dir, downloads_log, download_id)
    )
    #start the download via thread
    download_thread.start()

    #below is important because it is the first response my backend sends back to the front end after starting the download job 
    return jsonify({
        "download_id": download_id, 
        "status": "downloading"
    })


#route to show status  
@app.route("/status/<download_id>", methods= ["GET"])
def check_status(download_id):
    if download_id in downloads_log:
        return jsonify(downloads_log[download_id])
    return jsonify({"error": "Download ID not Found"}), 404



#route to get the finished file    
@app.route("/file/<download_id>", methods= ["GET"])
def get_finished_file(download_id):
    download_job = downloads_log.get(download_id)

    if download_job is None:
        return jsonify({"error" : "Download NOT Found"}), 404
    
    if download_job["status"] != "done" :
        return jsonify({"error" : "Download NOT ready yet"}), 409
    
    file_path = download_job.get("file_path")

    if file_path is None or not os.path.exists(file_path):
        return jsonify({"error" : "File not Found"}), 404
    
    return send_file(file_path, as_attachment=True) #sends as a downloadable attachment

if __name__ == "__main__":
    app.run(debug=True)