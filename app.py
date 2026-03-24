from flask import Flask, request, jsonify, send_from_directory
from cryptography import encrypt, decrypt, psnr, normxcorr2D
from PIL import Image
import numpy as np
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    # Serve frontend static assets
    if filename in ('style.css', 'script.js', 'favicon.ico'):
        return send_from_directory('frontend', filename)

    if filename.startswith('frontend/'):
        return send_from_directory('frontend', filename[len('frontend/'):])

    # Fallback
    return send_from_directory('.', filename)

@app.route('/encrypt', methods=['POST'])
def encrypt_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        share_size = int(request.form.get('shares', 2))
        if share_size < 2 or share_size > 8:
            return jsonify({'error': 'Invalid number of shares'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid shares parameter'}), 400

    # Save uploaded file
    filename = secure_filename(file.filename)
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(input_path)

    # Load and process image
    input_image = Image.open(input_path)

    # Encrypt
    shares, _ = encrypt(input_image, share_size)

    # Save shares
    share_paths = []
    for i in range(share_size):
        share_image = Image.fromarray(shares[:,:,:,i].astype(np.uint8))
        share_filename = f'XOR_Share_{i+1}.png'
        share_path = os.path.join(app.config['OUTPUT_FOLDER'], share_filename)
        share_image.save(share_path)
        share_paths.append(f'/outputs/{share_filename}')

    # Decrypt to calculate metrics
    output_image, output_matrix = decrypt(shares)
    input_matrix = np.asarray(input_image)
    psnr_value = psnr(input_matrix, output_matrix)
    nxcorr_value = normxcorr2D(input_matrix, output_matrix)

    # Save output
    output_filename = 'Output_XOR.png'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
    output_image.save(output_path)

    # Clean up input file
    os.remove(input_path)

    return jsonify({
        'shares': share_paths,
        'metrics': {
            'psnr': psnr_value,
            'nxcorr': nxcorr_value
        }
    })

@app.route('/decrypt', methods=['POST'])
def decrypt_image():
    if 'shares' not in request.files:
        return jsonify({'error': 'No share files provided'}), 400

    files = request.files.getlist('shares')
    if len(files) == 0:
        return jsonify({'error': 'No share files selected'}), 400

    try:
        num_shares = int(request.form.get('num_shares', len(files)))
    except ValueError:
        return jsonify({'error': 'Invalid num_shares parameter'}), 400

    if len(files) != num_shares:
        return jsonify({'error': f'Expected {num_shares} share files, got {len(files)}'}), 400

    # Load all share images
    share_images = []
    for file in files:
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type in shares'}), 400

        filename = secure_filename(file.filename)
        share_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(share_path)

        share_img = Image.open(share_path)
        share_images.append(np.asarray(share_img))

        # Clean up
        os.remove(share_path)

    # Stack shares
    shares = np.stack(share_images, axis=-1)

    # Decrypt
    output_image, output_matrix = decrypt(shares)

    # Calculate metrics (assuming we have the original, but we don't, so maybe skip or return without)
    # For decrypt, we don't have the original to compare, so just return the reconstructed

    # Save output
    output_filename = 'Output_XOR.png'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
    output_image.save(output_path)

    return jsonify({'reconstructed': f'/outputs/{output_filename}'})

@app.route('/outputs/<filename>')
def serve_output(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)