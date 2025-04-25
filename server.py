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

# from flask import Flask, request
# import os

# app = Flask(__name__)

# @app.route('/upload', methods=['POST'])
# def upload():
#     if 'file' not in request.files:
#         return 'No file uploaded', 400

#     file = request.files['file']
#     filename = "uploaded_audio." + file.filename.rsplit('.', 1)[-1]
#     filepath = os.path.join("/path/to/save", filename)
#     file.save(filepath)

#     # Now call your audio processing logic
#     process_audio(filepath)  # <-- Your existing logic here

#     return 'File processed successfully', 200
