# -*- coding: utf-8 -*-
"""
تطبيق الويب التفاعلي لتوليد تصاميم أخبار محافظات الكويت
يوفر واجهة عربية أنيقة وسهلة جداً تدعم السحب والإفلات والمعاينة الفورية.
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from werkzeug.utils import secure_filename
import engine

if sys.platform.startswith("win"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = engine.OUTPUT_DIR
TEMPLATES_OVERLAY_DIR = engine.TEMPLATES_DIR

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMPLATES_OVERLAY_DIR, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

import socket

def get_local_ip():
    """اكتشاف عنوان IP المحلي للشبكة لتمكين فتح التطبيق من الهاتف"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    # التحقق من حالة القوالب الحالية (هل هي قوالب كانفا مخصصة أم افتراضية)
    gov_status = {}
    for gid, data in engine.GOVERNORATES.items():
        overlay_file = os.path.join(TEMPLATES_OVERLAY_DIR, f"{gid}.png")
        gov_status[gid] = {
            "name": data["name"],
            "english": data["english"],
            "has_custom": os.path.exists(overlay_file),
            "accent": f"rgb({data['color_accent'][0]}, {data['color_accent'][1]}, {data['color_accent'][2]})",
            "primary": f"rgb({data['color_primary'][0]}, {data['color_primary'][1]}, {data['color_primary'][2]})"
        }
    local_ip = get_local_ip()
    return render_template('index.html', governorates=gov_status, local_ip=local_ip)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        gov_id = request.form.get('gov_id', 'capital')
        headline = request.form.get('headline', '').strip()
        body_text = request.form.get('body_text', '').strip()
        tag = request.form.get('tag', 'خبر').strip()
        use_sample = request.form.get('use_sample') == 'true'

        if not headline:
            return jsonify({'success': False, 'error': 'يرجى كتابة عنوان الخبر'}), 400

        image_path = None
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename and allowed_file(file.filename):
                fname = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_name = f"upload_{timestamp}_{fname}"
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], save_name)
                file.save(image_path)

        if not image_path and use_sample:
            sample_candidate = os.path.join(BASE_DIR, "sample_images", "kuwait_sample.jpg")
            if os.path.exists(sample_candidate):
                image_path = sample_candidate

        date_str = request.form.get('date_str', '').strip()

        # استدعاء محرك التوليد
        output_file_name = f"news_{gov_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        result_path = engine.generate_news_image(
            gov_id=gov_id,
            headline=headline,
            body_text=body_text,
            image_input=image_path,
            date_str=date_str,
            tag=tag,
            output_filename=output_file_name
        )

        return jsonify({
            'success': True,
            'image_url': f"/output/{output_file_name}",
            'filename': output_file_name
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/upload_template', methods=['POST'])
def upload_template():
    """رفع قالب مفرغ من كانفا لمحافظة معينة واستبدال القالب الحالي"""
    try:
        gov_id = request.form.get('gov_id')
        if gov_id not in engine.GOVERNORATES:
            return jsonify({'success': False, 'error': 'معرف المحافظة غير صحيح'}), 400

        if 'template_file' not in request.files:
            return jsonify({'success': False, 'error': 'لم يتم اختيار ملف'}), 400

        file = request.files['template_file']
        if file and file.filename and allowed_file(file.filename):
            target_path = os.path.join(TEMPLATES_OVERLAY_DIR, f"{gov_id}.png")
            file.save(target_path)
            return jsonify({'success': True, 'message': f"تم تحديث قالب {engine.GOVERNORATES[gov_id]['name']} بنجاح!"})
        else:
            return jsonify({'success': False, 'error': 'صيغة الملف غير مدعومة (يجب أن يكون PNG شفاف)'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/save_canvas', methods=['POST'])
def save_canvas():
    """حفظ الصورة المصدرة مباشرة من كانفاس المتصفح في مجلد output"""
    try:
        import base64
        data = request.get_json() or {}
        image_data = data.get('image_data', '')
        gov_id = data.get('gov_id', 'capital')
        if not image_data or ',' not in image_data:
            return jsonify({'success': False, 'error': 'بيانات الصورة غير صالحة'}), 400

        header, encoded = image_data.split(',', 1)
        file_bytes = base64.b64decode(encoded)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"news_{gov_id}_{timestamp}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(file_bytes)

        return jsonify({
            'success': True,
            'filename': filename,
            'image_url': f"/output/{filename}"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/output/<filename>')
def serve_output(filename):
    return send_from_directory(OUTPUT_DIR, filename)

@app.route('/templates_overlay/<filename>')
def serve_overlay(filename):
    return send_from_directory(TEMPLATES_OVERLAY_DIR, filename)

@app.route('/sample_images/<filename>')
def serve_sample(filename):
    return send_from_directory(os.path.join(BASE_DIR, "sample_images"), filename)

if __name__ == '__main__':
    local_ip = get_local_ip()
    print("=====================================================")
    print("★ أستوديو تصاميم أخبار محافظات الكويت يعمل بنجاح!")
    print(f"للفتح من الكمبيوتر: http://127.0.0.1:5000")
    print(f"للفتح من الموبايل (نفس شبكة الواي فاي): http://{local_ip}:5000")
    print("=====================================================")
    app.run(host='0.0.0.0', port=5000, debug=False)
