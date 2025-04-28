from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import uuid
import io

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    download_format = request.form['format']
    # Generate a unique filename prefix
    unique_id = str(uuid.uuid4())
    output_template = f'/tmp/{unique_id}-%(title)s.%(ext)s'

    if download_format == 'mp3':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        file_ext = 'mp3'
    elif download_format == 'mp4_with_sound':
        ydl_opts = {
            'format': 'bestvideo*+bestaudio/best',
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
        }
        file_ext = 'mp4'
    elif download_format == 'mp4_with_sound':
        ydl_opts = {
            'format': 'bestvideo*+bestaudio/best',
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            },
            {   # ADD THIS POSTPROCESSOR!
                'key': 'FFmpegAudioConvertor',
                'preferredcodec': 'aac',
            }],
        }
        file_ext = 'mp4'
    # elif download_format == 'mp4_no_sound':
    #     ydl_opts = {
    #         'format': 'bestvideo[ext=mp4]/bestvideo',
    #         'outtmpl': output_template,
    #     }
    #     file_ext = 'mp4'
    else:
        return "Invalid format", 400

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(url, download=True)
        if 'entries' in result:
            # In case of playlist or similar
            result = result['entries'][0]
        file_path = f'/tmp/{unique_id}-{result["title"]}.{file_ext}'
        # Fallback: detect the downloaded file by globbing if the extension or title has special chars
        if not os.path.exists(file_path):
            import glob
            matches = glob.glob(f'/tmp/{unique_id}-*')
            if matches:
                file_path = matches[0]

    # Read file into memory and delete it before sending to avoid file lock issues
    with open(file_path, 'rb') as f:
        data = f.read()
    try:
        os.remove(file_path)
    except Exception as e:
        print(f"Error deleting file: {e}")

    return send_file(
        io.BytesIO(data),
        as_attachment=True,
        download_name=f"{result['title']}.{file_ext}",
        mimetype="application/octet-stream"
    )

if __name__ == "__main__":
    app.run(debug=True)