from flask import Flask, render_template, request, redirect, send_file, send_from_directory, url_for
import os
from moviepy.editor import VideoFileClip
import uuid
import shutil
import yt_dlp

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
CLIPS_FOLDER = "static/clips"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CLIPS_FOLDER, exist_ok=True)

# def download_video_from_url(url, filename):
#    ydl_opts = {
#        'outtmpl': os.path.join(UPLOAD_FOLDER, filename),
#        'format': 'bestvideo+bestaudio/best',
#        'quiet': True
#    }
#    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#        ydl.download([url])
#    return os.path.join(UPLOAD_FOLDER, filename)

def download_video_from_url(url, filename):
    output_path = os.path.join(UPLOAD_FOLDER, filename + ".mp4")
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        'outtmpl': output_path,
        'merge_output_format': 'mp4',  # force mp4 merge
        'quiet': False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path


def get_max_duration(platform):
    return {
        'tiktok': 60,
        'youtube': 60,
        'instagram': 90
    }.get(platform, 60)

def split_video(path, max_duration, out_dir):
    clip = VideoFileClip(path)
    duration = int(clip.duration)
    clips = []
    for i in range(0, duration, max_duration):
        end = min(i + max_duration, duration)
        subclip = clip.subclip(i, end)
        filename = f"clip_{i}_{end}.mp4"
        out_path = os.path.join(out_dir, filename)
        subclip.write_videofile(out_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)
        clips.append(filename)
    return clips

@app.route('/', methods=['GET'])
def index():
    return render_template("index.html", clips=None)

@app.route('/process', methods=['POST'])
def process():
    shutil.rmtree(CLIPS_FOLDER)
    os.makedirs(CLIPS_FOLDER, exist_ok=True)

    video_file = request.files.get("video_file")
    video_url = request.form.get("video_url")
    platform = request.form.get("platform")

    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    if video_file and video_file.filename != '':
        video_file.save(filepath)
    elif video_url:
        filename = f"{uuid.uuid4()}.mp4"
        filepath = download_video_from_url(video_url, filename)
    else:
        return "No video provided.", 400

    max_duration = get_max_duration(platform)
    clips = split_video(filepath, max_duration, CLIPS_FOLDER)

    return render_template("index.html", clips=clips)

@app.route('/download_all')
def download_all():
    shutil.make_archive("static/all_clips", 'zip', CLIPS_FOLDER)
    return send_file("static/all_clips.zip", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
