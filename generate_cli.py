# -*- coding: utf-8 -*-
"""
أداة سطر الأوامر (CLI) لتوليد صور أخبار محافظات الكويت بسرعة
الاستخدام:
  python generate_cli.py --gov capital --title "عنوان الخبر" --image "مسار_الصورة"
"""

import argparse
import sys
import os

# ضبط مخرجات التيرمينال لتدعم UTF-8 على ويندوز
if sys.platform.startswith("win"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import engine

def main():
    parser = argparse.ArgumentParser(description="توليد تصاميم أخبار محافظات الكويت الست آلياً")
    parser.add_argument("--gov", "-g", required=True, choices=list(engine.GOVERNORATES.keys()),
                        help="معرف المحافظة: capital, hawalli, farwaniya, ahmadi, mubarak, jahra")
    parser.add_argument("--title", "-t", required=True, help="عنوان الخبر الرئيسي")
    parser.add_argument("--body", "-b", default="", help="تفاصيل الخبر (اختياري)")
    parser.add_argument("--image", "-i", default=None, help="مسار صورة الخبر (jpg/png)")
    parser.add_argument("--date", "-d", default=None, help="تاريخ الخبر بصيغة YYYY/MM/DD (اختياري، الافتراضي تاريخ اليوم)")
    parser.add_argument("--tag", default="خبر رسمي", help="تصنيف الخبر (مثال: خبر رسمي، عاجل، إعلان)")
    parser.add_argument("--output", "-o", default=None, help="اسم ملف المخرج (اختياري)")

    args = parser.parse_args()

    print(f"جاري معالجة وتوليد التصميم لمحافظة: {engine.GOVERNORATES[args.gov]['name']}...")
    try:
        out_path = engine.generate_news_image(
            gov_id=args.gov,
            headline=args.title,
            body_text=args.body,
            image_input=args.image,
            date_str=args.date,
            tag=args.tag,
            output_filename=args.output
        )
        print("✓ تم توليد التصميم بنجاح!")
        print(f"المسار: {out_path}")
    except Exception as e:
        print(f"حدث خطأ أثناء التوليد: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
