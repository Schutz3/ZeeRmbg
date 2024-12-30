import os, base64
from flask import Flask, render_template, request, send_file, jsonify
from rembg import remove, new_session
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import numpy as np
import cv2

load_dotenv()

app = Flask(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 mb dalam bytes
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# definisiin model yang dipake
MODELS = {
    'general': 'u2net',
    'massive': 'birefnet-general',
    'anime': 'isnet-anime',
    'default': 'u2net'
}

def improve_mask(mask, erosion_factor=5):
    from scipy import ndimage
    mask = ndimage.binary_erosion(mask, iterations=erosion_factor)
    mask = ndimage.binary_dilation(mask, iterations=erosion_factor)
    return mask

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_image_type(image):
    # ngubah pil image ke opencv image
    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # cek apakah dia wibu? kalo iya make model anime
    edge_image = cv2.Canny(cv_image, 100, 200)
    if np.mean(edge_image) > 10:  # Adjust this threshold as needed
        return 'anime'
    
    # cek apakah gambarnya kompleks? jika iya maka akan menggukakan model massive
    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    if variance > 95:  # Adjust this threshold as needed
        return 'massive'
    
    # balik ke general
    return 'general'

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'GET':
        encoded_webhook = base64.b64encode(WEBHOOK_URL.encode()).decode()
        return render_template('index.html', webhook=encoded_webhook)
    
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed types are png, jpg, jpeg'}), 400
        
        if request.content_length > MAX_FILE_SIZE:
            return jsonify({'error': 'File size exceeds the maximum limit of 10 MB'}), 400
        
        if file:
            try:
                input_image = Image.open(file.stream)
                
                # deteksi gambar dan milih model yang sesuai
                image_type = detect_image_type(input_image)
                model_path = MODELS.get(image_type, MODELS['default'])
                print(model_path)
                
                # bikin sesi baru bersarkan tipe gambar yang terdeteksi
                session = new_session(model_path)
                
                # hapus background make parameter tambahan
                output = remove(
                    input_image,
                    session=session,
                    alpha_matting=True,
                    alpha_matting_foreground_threshold=240,
                    alpha_matting_background_threshold=10,
                    post_process_mask=improve_mask
                )
                
                output_array = np.array(output)
                output_array[:, :, 3] = np.clip(output_array[:, :, 3] * 1.2, 0, 255)
                output_image = Image.fromarray(output_array)
                
                img_io = BytesIO()
                output_image.save(img_io, 'PNG')
                img_io.seek(0)
                downName = file.filename+'_Zee-rmbg.png'
                return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=downName)
            except Exception as e:
                return jsonify({'error': f'Error processing image: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5100)