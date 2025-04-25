from flask import Flask, request
import os

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file uploaded', 400

    file = request.files['file']
    filename = "uploaded_audio." + file.filename.rsplit('.', 1)[-1]
    filepath = os.path.join("/path/to/save", filename)
    file.save(filepath)

    # Now call your audio processing logic
    process_audio(filepath)  # <-- Your existing logic here

    return 'File processed successfully', 200
