# -*- coding: utf-8 -*-
"""
محرك توليد تصاميم أخبار محافظات الكويت بدقة 1024×1536 (قوالب كانفا الرسمية)
يتيح التحكم الكامل في:
1. العنوان (Headline)
2. الوصف والتفاصيل (Description)
3. التاريخ (Date)
4. صورة الخبر (Photo)
5. المحافظة (العاصمة، حولي، الفروانية، الأحمدي، مبارك الكبير، الجهراء)
"""

import os
import re
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(BASE_DIR, "fonts")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates_overlay")
ASSETS_DIR = os.path.join(TEMPLATES_DIR, "assets")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

os.makedirs(FONTS_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# الأبعاد الرسمية لتصميم كانفا
CANVAS_WIDTH = 1024
CANVAS_HEIGHT = 1536

# إحداثيات إطار الصورة في كانفا
PHOTO_BOX = {
    "x1": 50,
    "y1": 250,
    "x2": 974,
    "y2": 744,
    "width": 924,
    "height": 494,
    "corner_radius": 22
}

# إحداثيات بادج التاريخ
DATE_BOX = {
    "x1": 704,
    "y1": 689,
    "width": 260,
    "height": 54,
    "bg_color": (1, 31, 76, 255),
    "border_color": (0, 20, 50, 255),
    "radius": 12
}

# إحداثيات بطاقة النصوص (الرق / Parchment)
TITLE_AREA = {
    "min_y": 780,
    "max_y": 932,
    "max_width": 820,
    "line_height": 50
}

BODY_AREA = {
    "min_y": 958,
    "max_y": 1165,
    "max_width": 840,
    "line_height": 38
}

# بيانات محافظات الكويت الست
GOVERNORATES = {
    "capital": {
        "id": "capital",
        "name": "محافظة العاصمة",
        "short_name": "العاصمة",
        "english": "Capital Governorate",
        "color_accent": (212, 175, 55),
        "color_primary": (13, 37, 63)
    },
    "hawalli": {
        "id": "hawalli",
        "name": "محافظة حولي",
        "short_name": "حولي",
        "english": "Hawalli Governorate",
        "color_accent": (46, 204, 113),
        "color_primary": (16, 75, 58)
    },
    "farwaniya": {
        "id": "farwaniya",
        "name": "محافظة الفروانية",
        "short_name": "الفروانية",
        "english": "Farwaniya Governorate",
        "color_accent": (231, 76, 60),
        "color_primary": (120, 24, 38)
    },
    "ahmadi": {
        "id": "ahmadi",
        "name": "محافظة الأحمدي",
        "short_name": "الأحمدي",
        "english": "Al Ahmadi Governorate",
        "color_accent": (52, 152, 219),
        "color_primary": (18, 64, 118)
    },
    "mubarak": {
        "id": "mubarak",
        "name": "محافظة مبارك الكبير",
        "short_name": "مبارك الكبير",
        "english": "Mubarak Al-Kabeer Governorate",
        "color_accent": (26, 188, 156),
        "color_primary": (38, 50, 72)
    },
    "jahra": {
        "id": "jahra",
        "name": "محافظة الجهراء",
        "short_name": "الجهراء",
        "english": "Al Jahra Governorate",
        "color_accent": (230, 149, 39),
        "color_primary": (95, 62, 38)
    }
}

def get_font(font_name="arabic_bold.ttf", size=32):
    """تحميل الخط مع نظام بدائل موثوق يدعم التشكيل والعربية بنسبة 100%"""
    font_path = os.path.join(FONTS_DIR, font_name)
    if os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
            
    # بدائل الخطوط النظامية في ويندوز
    win_map = {
        "arabic_title.ttf": ["tahomabd.ttf", "arialbd.ttf", "segoeuib.ttf"],
        "arabic_bold.ttf": ["arialbd.ttf", "tahomabd.ttf", "segoeuib.ttf"],
        "arabic_regular.ttf": ["arial.ttf", "tahoma.ttf", "segoeui.ttf"]
    }
    candidates = win_map.get(font_name, ["arialbd.ttf", "tahomabd.ttf", "arial.ttf"])
    for wf in candidates:
        wp = os.path.join(r"C:\Windows\Fonts", wf)
        if os.path.exists(wp):
            try:
                return ImageFont.truetype(wp, size)
            except Exception:
                continue
                
    return ImageFont.load_default()

def shape_arabic_text(text):
    """تشكيل وعكس اتجاه النص العربي ليتصل بشكل طبيعي في مكتبة PIL"""
    if not text:
        return ""
    # إزالة أي فراغات زائدة
    clean = text.strip()
    reshaped = arabic_reshaper.reshape(clean)
    return get_display(reshaped)

def wrap_arabic_lines(text, font, max_width, draw):
    """تقسيم النص العربي لعدة أسطر متناغمة دون كسر الكلمات"""
    words = text.strip().split()
    if not words:
        return []
        
    lines = []
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        shaped = shape_arabic_text(test_line)
        bbox = draw.textbbox((0, 0), shaped, font=font)
        width = bbox[2] - bbox[0]
        
        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
                current_line = []
                
    if current_line:
        lines.append(" ".join(current_line))
        
    return lines

def fit_crop_photo(img, target_w, target_h):
    """تكبير وقص الصورة لتملأ الإطار المخصص في كانفا مع الحفاظ على التوسيط"""
    img = img.convert("RGBA")
    src_w, src_h = img.size
    ratio = max(target_w / src_w, target_h / src_h)
    new_w = int(src_w * ratio)
    new_h = int(src_h * ratio)
    
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    
    return resized.crop((left, top, left + target_w, top + target_h))

def create_top_rounded_mask(width, height, radius=22):
    """إنشاء قناع بزوايا علوية منحنية وزوايا سفلية مستقيمة لمطابقة إطار كانفا"""
    mask = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(mask)
    
    # الزاوية العلوية اليسرى
    draw.rectangle([(0, 0), (radius, radius)], fill=0)
    draw.pieslice([(0, 0), (radius * 2, radius * 2)], 180, 270, fill=255)
    
    # الزاوية العلوية اليمنى
    draw.rectangle([(width - radius, 0), (width, radius)], fill=0)
    draw.pieslice([(width - radius * 2, 0), (width, radius * 2)], 270, 360, fill=255)
    
    return mask

def draw_date_badge(canvas, date_str=None):
    """رسم شارة التاريخ مع أيقونة التقويم في الركن السفلي الأيمن للصورة"""
    if not date_str or not date_str.strip():
        date_str = datetime.now().strftime("%Y/%m/%d")
    else:
        date_str = date_str.strip().replace("-", "/")
        
    bw = DATE_BOX["width"]
    bh = DATE_BOX["height"]
    bx = DATE_BOX["x1"]
    by = DATE_BOX["y1"]
    
    badge = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(badge)
    
    # رسم الخلفية الكحلية الداكنة المستديرة
    b_draw.rounded_rectangle(
        [(0, 0), (bw - 2, bh - 2)],
        radius=DATE_BOX["radius"],
        fill=DATE_BOX["bg_color"],
        outline=DATE_BOX["border_color"],
        width=1
    )
    
    # دمج أيقونة التقويم
    cal_path = os.path.join(ASSETS_DIR, "calendar_icon.png")
    if os.path.exists(cal_path):
        try:
            icon = Image.open(cal_path).convert("RGBA")
            badge.paste(icon, (14, 8), icon)
        except Exception:
            pass
            
    # كتابة التاريخ
    date_font = get_font("arabic_bold.ttf", 30)
    date_bbox = b_draw.textbbox((0, 0), date_str, font=date_font)
    tw = date_bbox[2] - date_bbox[0]
    th = date_bbox[3] - date_bbox[1]
    
    # محاذاة التاريخ بجانب الأيقونة
    tx = 75
    ty = (bh - th) // 2 - 2
    b_draw.text((tx, ty), date_str, font=date_font, fill=(255, 255, 255, 255))
    
    canvas.paste(badge, (bx, by), badge)

def render_content_texts(canvas, headline, body_text=""):
    """
    كتابة العنوان في المنطقة المخصصة أعلى الفاصل الذهبي
    وكتابة الوصف/التفاصيل في المنطقة أسفل الفاصل
    مع ضبط المحاذاة والظلال الخفيفة الأنيقة
    """
    draw = ImageDraw.Draw(canvas, "RGBA")
    
    # 1. العنوان الرئيسي
    title_font_size = 38 if len(headline) < 85 else 34
    title_font = get_font("arabic_title.ttf", title_font_size)
    title_lines = wrap_arabic_lines(headline, title_font, TITLE_AREA["max_width"], draw)
    
    line_h_title = title_font_size + 14
    total_title_h = len(title_lines) * line_h_title
    
    # توسيط العنوان عمودياً في المنطقة المخصصة له
    avail_title_h = TITLE_AREA["max_y"] - TITLE_AREA["min_y"]
    title_start_y = TITLE_AREA["min_y"] + max(0, (avail_title_h - total_title_h) // 2)
    
    for i, line in enumerate(title_lines):
        sh = shape_arabic_text(line)
        bbox = draw.textbbox((0, 0), sh, font=title_font)
        tw = bbox[2] - bbox[0]
        tx = (CANVAS_WIDTH - tw) // 2
        ty = title_start_y + (i * line_h_title)
        
        # ظل خفيف بلون داكن دافئ لتعزيز القراءة
        draw.text((tx + 1, ty + 2), sh, font=title_font, fill=(115, 90, 55, 180))
        # النص الأبيض العريض مع stroke_width خفيف
        draw.text(
            (tx, ty),
            sh,
            font=title_font,
            fill=(255, 255, 255, 255),
            stroke_width=1,
            stroke_fill=(255, 255, 255, 255)
        )
        
    # 2. الوصف والتفاصيل أسفل الفاصل الذهبي
    if body_text and body_text.strip():
        body_font_size = 25 if len(body_text) < 180 else 23
        body_font = get_font("arabic_bold.ttf", body_font_size)
        
        body_lines = []
        for para in body_text.strip().split("\n"):
            if para.strip():
                body_lines.extend(wrap_arabic_lines(para.strip(), body_font, BODY_AREA["max_width"], draw))
                
        # اقتصار السطور على المتاح في المساحة المخصصة (بحد أقصى 5 أسطر)
        body_lines = body_lines[:5]
        
        line_h_body = body_font_size + 13
        total_body_h = len(body_lines) * line_h_body
        
        avail_body_h = BODY_AREA["max_y"] - BODY_AREA["min_y"]
        body_start_y = BODY_AREA["min_y"] + max(0, (avail_body_h - total_body_h) // 2)
        
        for i, line in enumerate(body_lines):
            sh = shape_arabic_text(line)
            bbox = draw.textbbox((0, 0), sh, font=body_font)
            tw = bbox[2] - bbox[0]
            tx = (CANVAS_WIDTH - tw) // 2
            ty = body_start_y + (i * line_h_body)
            
            # ظل النص
            draw.text((tx + 1, ty + 2), sh, font=body_font, fill=(125, 100, 65, 160))
            # النص الأبيض الناصع
            draw.text((tx, ty), sh, font=body_font, fill=(255, 255, 255, 255))

def generate_news_image(
    gov_id,
    headline,
    body_text="",
    image_input=None,
    date_str=None,
    tag="خبر رسمي",
    output_filename=None,
    canvas_size=(CANVAS_WIDTH, CANVAS_HEIGHT)
):
    """
    الدالة الشاملة لتوليد التصميم الإخباري بمطابقة 100% لتصميم كانفا:
    - تحميل قالب المحافظة المختار (العاصمة، حولي، الفروانية، الأحمدي، مبارك الكبير، الجهراء)
    - إدراج صورة الخبر في الإطار المخصص بزواياه العلوية المنحنية
    - وضع بادج التاريخ في المكان المحدد مع أيقونة التقويم
    - تنسيق العنوان أعلى الفاصل الزخرفي والوصف أسفله
    - تصدير الصورة بدقة 1024×1536 الأصلية
    """
    if gov_id not in GOVERNORATES:
        gov_id = "capital"
        
    gov = GOVERNORATES[gov_id]
    
    # 1. استدعاء قالب المحافظة الأساسي بدقة 1024×1536
    template_path = os.path.join(TEMPLATES_DIR, f"{gov_id}.png")
    if not os.path.exists(template_path):
        # محاولة استخدام أي قالب متوفر كقالب احتياطي
        candidate_paths = [os.path.join(TEMPLATES_DIR, f"{k}.png") for k in GOVERNORATES.keys()]
        found = next((p for p in candidate_paths if os.path.exists(p)), None)
        if found:
            template_path = found
        else:
            raise FileNotFoundError(f"تعذر العثور على قالب المحافظة: {template_path}")
            
    base_canvas = Image.open(template_path).convert("RGBA")
    if base_canvas.size != (CANVAS_WIDTH, CANVAS_HEIGHT):
        base_canvas = base_canvas.resize((CANVAS_WIDTH, CANVAS_HEIGHT), Image.Resampling.LANCZOS)
        
    # 2. معالجة وإدراج صورة الخبر
    pw = PHOTO_BOX["width"]
    ph = PHOTO_BOX["height"]
    px = PHOTO_BOX["x1"]
    py = PHOTO_BOX["y1"]
    
    photo_img = None
    if image_input is not None:
        if isinstance(image_input, str) and os.path.exists(image_input):
            try:
                photo_img = Image.open(image_input)
            except Exception:
                photo_img = None
        elif isinstance(image_input, Image.Image):
            photo_img = image_input
            
    if photo_img is not None:
        cropped_photo = fit_crop_photo(photo_img, pw, ph)
        mask = create_top_rounded_mask(pw, ph, radius=PHOTO_BOX["corner_radius"])
        base_canvas.paste(cropped_photo, (px, py), mask)
        
    # 3. وضع شارة التاريخ
    draw_date_badge(base_canvas, date_str=date_str)
    
    # 4. كتابة العنوان وتفاصيل الخبر على البطاقة
    render_content_texts(base_canvas, headline=headline, body_text=body_text)
    
    # 5. حفظ الصورة بدقة فائقة
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"news_{gov_id}_{timestamp}.png"
        
    out_path = os.path.join(OUTPUT_DIR, output_filename)
    base_canvas.convert("RGB").save(out_path, "PNG", quality=95)
    
    return out_path
