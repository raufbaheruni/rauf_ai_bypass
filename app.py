import cv2
import numpy as np
import os
import io
import tempfile
from datetime import datetime
from PIL import Image
from flask import Flask, render_template, request, send_file

try:
    import piexif
except ImportError:
    os.system("pip install piexif")
    import piexif

app = Flask(__name__)

def ultimate_ai_bypass(file_bytes):
    # अब हम सीधे बाइट्स (Bytes) पढ़ रहे हैं, यह एरर को ठीक कर देगा
    pil_img = Image.open(io.BytesIO(file_bytes))
    if pil_img.mode in ("RGBA", "P"):
        pil_img = pil_img.convert("RGB")
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # RAM SAVE: Image Auto-Resize
    max_size = 1000
    h, w = img.shape[:2]
    if max(h, w) > max_size:
        scale = max_size / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    if img.shape[0] > 10 and img.shape[1] > 10:
        img = img[2:-2, 2:-2]

    h, w = img.shape[:2]

    # JPEG GHOST ATTACK
    _, enc_img = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 40])
    img_ghost = cv2.imdecode(enc_img, 1)

    # HEAVY CHROMA BLUR
    ycrcb = cv2.cvtColor(img_ghost, cv2.COLOR_BGR2YCrCb)
    y, cr, cb = cv2.split(ycrcb)
    cr_blur = cv2.GaussianBlur(cr, (7, 7), 0)
    cb_blur = cv2.GaussianBlur(cb, (7, 7), 0)
    ycrcb_attacked = cv2.merge((y, cr_blur, cb_blur))
    img_color_attack = cv2.cvtColor(ycrcb_attacked, cv2.COLOR_YCrCb2BGR)

    # EDGE-TARGETED SENSOR NOISE
    gray = cv2.cvtColor(img_color_attack, cv2.COLOR_BGR2GRAY)
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    edges = np.sqrt(sobelx**2 + sobely**2)
    if edges.max() > 0:
        edges = (edges / edges.max() * 255).astype(np.uint8)
    else:
        edges = edges.astype(np.uint8)

    _, mask = cv2.threshold(edges, 30, 255, cv2.THRESH_BINARY)
    mask = cv2.dilate(mask, np.ones((3,3), np.uint8), iterations=1)

    noise_2d = np.random.normal(0, 6.0, (h, w)).astype(np.float32)
    noise_2d = np.where(mask == 255, noise_2d, 0)
    
    img_final = img_color_attack.astype(np.int16)
    img_final[:, :, 0] += noise_2d.astype(np.int16)
    img_final[:, :, 1] += noise_2d.astype(np.int16)
    img_final[:, :, 2] += noise_2d.astype(np.int16)
    img_final = np.clip(img_final, 0, 255).astype(np.uint8)

    # EXIF METADATA INJECTION
    now = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
    exif_dict = {
        "0th": {
            piexif.ImageIFD.Make: b"Apple",
            piexif.ImageIFD.Model: b"iPhone 16 Pro",
            piexif.ImageIFD.Software: b"17.4.1",
            piexif.ImageIFD.DateTime: now.encode('utf-8'),
            piexif.ImageIFD.XResolution: (72, 1),
            piexif.ImageIFD.YResolution: (72, 1),
            piexif.ImageIFD.ResolutionUnit: 2
        },
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: now.encode('utf-8'),
            piexif.ExifIFD.DateTimeDigitized: now.encode('utf-8'),
            piexif.ExifIFD.LensModel: b"iPhone 16 Pro back triple camera 24mm f/1.78",
            piexif.ExifIFD.LensMake: b"Apple",
            piexif.ExifIFD.ExposureTime: (1, 120),
            piexif.ExifIFD.FNumber: (18, 10),
            piexif.ExifIFD.ISOSpeedRatings: 64,
            piexif.ExifIFD.PixelXDimension: w,
            piexif.ExifIFD.PixelYDimension: h
        }
    }
    exif_bytes = piexif.dump(exif_dict)

    img_rgb = cv2.cvtColor(img_final, cv2.COLOR_BGR2RGB)
    pil_final_img = Image.fromarray(img_rgb)

    temp_dir = tempfile.gettempdir()
    out_path = os.path.join(temp_dir, "BAHERUNI.jpg")
    pil_final_img.save(out_path, "JPEG", quality=95, subsampling=2, exif=exif_bytes)
    
    return out_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "No file uploaded", 400
    file = request.files['file']
    if file.filename == '':
        return "No file selected", 400
    
    try:
        # सुधार: फाइल को सीधे स्ट्रीम करने के बजाय बाइट्स में पढ़ लें
        file_bytes = file.read()
        output_path = ultimate_ai_bypass(file_bytes)
        return send_file(output_path, as_attachment=True, download_name='BAHERUNI.jpg')
    except Exception as e:
        import traceback
        return traceback.format_exc(), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
