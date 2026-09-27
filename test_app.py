# -*- coding: utf-8 -*-
"""
اختبارات آلية لضمان عمل تطبيق الويب ومحرك التوليد بنسبة 100%
"""
import io
import os
import unittest
from app import app
import engine

class TestKuwaitNewsGenerator(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('أتمتة تصاميم أخبار محافظات الكويت'.encode('utf-8'), response.data)

    def test_generate_news_api(self):
        # اختبار توليد خبر لمحافظة العاصمة
        data = {
            'gov_id': 'capital',
            'headline': 'محافظة العاصمة تطلق حملة تشجير وتجميل كبرى في الحدائق العامة',
            'body_text': 'المبادرة تهدف إلى زيادة المساحات الخضراء والارتقاء بالمظهر الجمالي للعاصمة.',
            'tag': 'عاجل',
            'use_sample': 'true'
        }
        response = self.client.post('/generate', data=data)
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data['success'])
        self.assertTrue(os.path.exists(os.path.join(engine.OUTPUT_DIR, json_data['filename'])))

    def test_all_governorates_generation(self):
        # اختبار التوليد لجميع المحافظات الست
        sample_img = os.path.join(engine.BASE_DIR, "sample_images", "kuwait_sample.jpg")
        for gid, gdata in engine.GOVERNORATES.items():
            out = engine.generate_news_image(
                gov_id=gid,
                headline=f"خبر تجريبي لمحافظة {gdata['name']}: إنجاز مشروع جديد بنجاح",
                body_text="متابعة مستمرة لكافة الخدمات الميدانية لخدمة أهالي المحافظة.",
                image_input=sample_img,
                tag="متابعات"
            )
            self.assertTrue(os.path.exists(out), f"فشل إنشاء صورة لمحافظة {gid}")
            print(f"✓ نجح توليد تصميم: {gdata['name']}")

    def test_save_canvas_api(self):
        # اختبار حفظ صورة الكانفاس المباشرة
        import base64
        # 1x1 transparent PNG base64
        dummy_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        response = self.client.post('/save_canvas', json={
            'image_data': dummy_base64,
            'gov_id': 'capital'
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertTrue(os.path.exists(os.path.join(engine.OUTPUT_DIR, data['filename'])))

if __name__ == '__main__':
    unittest.main()
