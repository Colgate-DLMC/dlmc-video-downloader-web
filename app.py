from flask import Flask, request, jsonify, render_template, send_file
from downloader import run_download

import uuid
import threading

app = Flask(__name__)


downloads_log= {}

#route to launch the webpage
@app.route("/")
def index():
    return render_template("index.html")

#route to start a download
@app.route("/download", methods= ["POST"])
def start_download(url):


#route to show status  
@app.route("/status/<download_id>", methods= ["GET"])
def check_status(download_id):
    get_url = request.url
    run_download(get_url, downloads, downloads_log, download_id)
    


#route to get the finished file    
@app.route("/file", methods= ["GET"])
def get_finished_file():

def createUniqueID():
    