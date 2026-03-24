from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import uuid
import subprocess
import pathlib
import soundfile as sf
from werkzeug.utils import secure_filename
import sys
sys.path.append(str(pathlib.Path(__file__).parent))
from config import check_device
from services.VocalRemovalModelHandler import vocalRemovalModelHandler

UPLOAD_VIDEO_DIR = pathlib.Path(__file__).parent / "uploads" / "video"
UPLOAD_AUDIO_DIR = pathlib.Path(__file__).parent / "uploads" / "audio"
OUTPUT_DIR       = pathlib.Path(__file__).parent / "uploads" / "output"

app = Flask(__name__)

# Load model once at startup so it stays in memory between requests
device = check_device()
removal_handler = vocalRemovalModelHandler(device=device)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/upload-video', methods=['POST'])
def upload_video():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    f = request.files['file']
    if not f.filename:
        return jsonify({'error': 'Empty filename'}), 400
    safe_name = secure_filename(f.filename)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    save_path = UPLOAD_VIDEO_DIR / unique_name
    f.save(str(save_path))
    return jsonify({'filename': unique_name})


@app.route('/api/remove-vocals', methods=['POST'])
def remove_vocals_route():
    data = request.get_json()
    if not data or 'filename' not in data:
        return jsonify({'error': 'No filename provided'}), 400

    safe_name = secure_filename(data['filename'])
    video_path = UPLOAD_VIDEO_DIR / safe_name
    if not video_path.exists() or not video_path.is_file():
        return jsonify({'error': 'File not found'}), 404

    # Extract audio from video with ffmpeg
    audio_filename = f"{video_path.stem}_audio.wav"
    audio_path = UPLOAD_AUDIO_DIR / audio_filename
    result = subprocess.run(
        [
            'ffmpeg', '-y', '-i', str(video_path),
            '-vn', '-ar', str(removal_handler.model.samplerate), '-ac', '2',
            str(audio_path)
        ],
        capture_output=True
    )
    if result.returncode != 0:
        return jsonify({'error': 'Audio extraction failed — make sure ffmpeg is installed and in PATH'}), 500

    try:
        instrumental = removal_handler.remove_vocals(str(audio_path))
    except Exception as e:
        return jsonify({'error': f'Vocal removal failed: {e}'}), 500

    output_filename = f"{video_path.stem}_instrumental.wav"
    output_path = OUTPUT_DIR / output_filename
    sf.write(str(output_path), instrumental.T, removal_handler.model.samplerate)

    return jsonify({'download_url': f'/api/download/{output_filename}'})


@app.route('/api/download/<filename>')
def download_file(filename):
    safe_name = secure_filename(filename)
    return send_from_directory(str(OUTPUT_DIR), safe_name, as_attachment=True)


if __name__ == '__main__':
    # debug=false in prod later, change the port adequatly to the pc(if possible)
    # use_reloader=False prevents WinError 10038 (socket inheritance issue on Windows)
    # and avoids loading the heavy ML model twice
    app.run(debug=True, port=5000, use_reloader=False)