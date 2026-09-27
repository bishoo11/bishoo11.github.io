# -*- coding: utf-8 -*-
"""
توليد 6 قوالب إطارات شفافة كأمثلة لقوالب كانفا (Overlay PNGs)
يمكن للمستخدم استبدال أي منها بتصميمه المفرغ المصدّر من كانفا.
"""

import os
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(BASE_DIR, "fonts")
OVERLAY_DIR = os.path.join(BASE_DIR, "templates_overlay")

GOVERNORATES = {
    "capital": {"name": "محافظة العاصمة", "accent": (212, 175, 55), "badge_bg": (13, 37, 63)},
    "hawalli": {"name": "محافظة حولي", "accent": (46, 204, 113), "badge_bg": (16, 75, 58)},
    "farwaniya": {"name": "محافظة الفروانية", "accent": (231, 76, 60), "badge_bg": (120, 24, 38)},
    "ahmadi": {"name": "محافظة الأحمدي", "accent": (52, 152, 219), "badge_bg": (18, 64, 118)},
    "mubarak": {"name": "محافظة مبارك الكبير", "accent": (26, 188, 156), "badge_bg": (38, 50, 72)},
    "jahra": {"name": "محافظة الجهراء", "accent": (230, 149, 39), "badge_bg": (95, 62, 38)}
}

def get_font(size=36):
    fp = os.path.join(FONTS_DIR, "arabic_bold.ttf")
    if os.path.exists(fp):
        return ImageFont.truetype(fp, size)
    return ImageFont.load_default()

def shape(t):
    return get_display(arabic_reshaper.reshape(t))

def generate_overlays():
    w, h = 1080, 1080
    os.makedirs(OVERLAY_DIR, exist_ok=True)
    font = get_font(34)
    
    for gid, info in GOVERNORATES.items():
        # صورة شفافة تماماً
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, "RGBA")
        
        # 1. إطار محيطي ناعم
        border_color = (*info["accent"], 180)
        draw.rectangle([12, 12, w - 12, h - 12], outline=border_color, width=4)
        
        # 2. الهيدر العلوي
        header_h = 100
        # خلفية متدرجة شبه شفافة للهيدر
        for y in range(header_h):
            alpha = int(220 * (1 - (y / header_h) * 0.3))
            draw.line([(14, 14 + y), (w - 14, 14 + y)], fill=(*info["badge_bg"], alpha))
            
        # شريط ألوان علم الكويت أعلى الهيدر
        bar_w = (w - 28) // 3
        draw.rectangle([14, 14, 14 + bar_w, 20], fill=(0, 122, 61, 255))
        draw.rectangle([14 + bar_w, 14, 14 + bar_w * 2, 20], fill=(255, 255, 255, 255))
        draw.rectangle([14 + bar_w * 2, 14, w - 14, 20], fill=(206, 17, 38, 255))
        
        # كتابة اسم المحافظة بالهيدر
        gov_title = shape(info["name"])
        bbox = draw.textbbox((0, 0), gov_title, font=font)
        tw = bbox[2] - bbox[0]
        tx = w - tw - 45
        ty = 42
        
        # رقعة لون التمييز
        draw.rectangle([w - 30, ty + 2, w - 24, ty + 38], fill=info["accent"])
        draw.text((tx, ty), gov_title, font=font, fill=(255, 255, 255, 255))
        
        # علامة كويتية أنيقة بالطرف الآخر
        kw_title = shape("دولة الكويت")
        draw.text((45, ty + 4), kw_title, font=get_font(24), fill=(*info["accent"], 240))
        
        # 3. شريط الفوتر السفلي الشفاف
        footer_h = 60
        fy = h - footer_h - 14
        draw.rectangle([14, fy, w - 14, h - 14], fill=(*info["badge_bg"], 235))
        draw.line([(14, fy), (w - 14, fy)], fill=info["accent"], width=2)
        
        # حفظ كـ PNG شفاف
        save_path = os.path.join(OVERLAY_DIR, f"{gid}.png")
        overlay.save(save_path, "PNG")
        print(f"تم إنشاء القالب: {save_path}")

if __name__ == "__main__":
    generate_overlays()
