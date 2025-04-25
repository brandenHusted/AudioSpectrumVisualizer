from flask import Flask, request, jsonify
import os
import subprocess

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filename = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filename)

    # Run the audio processing script
    subprocess.Popen(["python3", "process_audio.py", filename])

    return jsonify({"message": "File received and processing started."}), 200

if __name__ == "__main__":
    app.run(debug=True)
