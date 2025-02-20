from flask import Flask, request, send_file, jsonify
from PIL import Image
import os
import uuid
import threading
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['https://converter-green-xi.vercel.app'])

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

MAX_FILE_SIZE_MB = 10
ALLOWED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff")

def allowed_file(filename):
    return filename.endswith(ALLOWED_EXTENSIONS)

def delete_file_after_delay(file_path, delay=10):
    """Deletes a file after a delay (default: 10 seconds)."""
    threading.Timer(delay, lambda: os.remove(file_path) if os.path.exists(file_path) else None).start()

@app.route('/convert', methods=['POST'])
def convert():
    if 'images' not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    images = []
    
    for file in request.files.getlist("images"):
        if not file.filename:
            return jsonify({"error": "Empty filename"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": f"Invalid file type: {file.filename}"}), 400
        
        file.seek(0, os.SEEK_END)
        file_size = file.tell() / (1024 * 1024)  
        file.seek(0)  
        
        if file_size > MAX_FILE_SIZE_MB:
            return jsonify({"error": f"File too large: {file.filename} ({file_size:.2f}MB). Max {MAX_FILE_SIZE_MB}MB allowed."}), 400

        try:
            img = Image.open(file)
            img = img.convert("RGB")
            images.append(img)
        except Exception as e:
            return jsonify({"error": f"Error processing image {file.filename}: {str(e)}"}), 400

    if images:
        output_pdf_name = f"converted_{uuid.uuid4().hex}.pdf"  
        output_pdf_path = os.path.join(OUTPUT_FOLDER, output_pdf_name)
        
        images[0].save(output_pdf_path, save_all=True, append_images=images[1:])
        
        # Schedule file deletion after 10 seconds
        delete_file_after_delay(output_pdf_path, delay=300)

        return send_file(output_pdf_path, as_attachment=True)

    return jsonify({"error": "No valid images uploaded!"}), 400

if __name__ == "__main__":
    app.run(debug=True, threaded=True)