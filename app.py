import os, base64
from flask import Flask, render_template, request, send_file, jsonify
from rembg import remove
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# max file 
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 mb dalam bytes
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
# extensi file yang diperbolehkan
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
                output_image = remove(input_image, post_process_mask=True)
                img_io = BytesIO()
                output_image.save(img_io, 'PNG')
                img_io.seek(0)
                downName = file.filename+'_Zee-rmbg.png'
                return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=downName)
            except Exception as e:
                return jsonify({'error': f'Error processing image: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5100)