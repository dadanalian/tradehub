"""Seed script - populate TradeHub with sample data"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app, db
from models import User, Category, Product

def seed():
    with app.app_context():
        db.create_all()

        # Admin user
        if not User.query.filter_by(email="admin@tradehub.com").first():
            admin = User(username="admin", email="admin@tradehub.com", company="TradeHub Inc", phone="+86-400-888-9999")
            admin.set_password("admin123")
            admin.is_admin = True
            db.session.add(admin)
            print("Created admin: admin@tradehub.com / admin123")

        # Test user
        if not User.query.filter_by(email="buyer@test.com").first():
            buyer = User(username="buyer", email="buyer@test.com", company="Global Trade Co", phone="+1-555-0123")
            buyer.set_password("buyer123")
            db.session.add(buyer)
            print("Created buyer: buyer@test.com / buyer123")

        # Categories
        categories_data = [
            ("electronics", "电子产品", "Electronics", "💻"),
            ("machinery", "机械设备", "Machinery", "⚙️"),
            ("textiles", "纺织服装", "Textiles & Apparel", "👕"),
            ("home_garden", "家居园艺", "Home & Garden", "🏠"),
            ("sports", "运动户外", "Sports & Outdoors", "⚽"),
            ("beauty", "美容个护", "Beauty & Personal Care", "💄"),
        ]
        cats = {}
        for slug, name_zh, name_en, icon in categories_data:
            cat = Category.query.filter_by(slug=slug).first()
            if not cat:
                cat = Category(slug=slug, name_zh=name_zh, name_en=name_en, image_url=icon)
                db.session.add(cat)
            cats[slug] = cat

        db.session.commit()
        print(f"Created {len(cats)} categories")

        # Products
        if Product.query.count() == 0:
            products_data = [
                # Electronics
                ("蓝牙耳机 Pro", "Bluetooth Earphones Pro", "高品质降噪蓝牙耳机，续航30小时，IPX5防水", "Premium noise-cancelling Bluetooth earphones, 30hr battery, IPX5 waterproof", 12.99, "electronics", 500, 100, True),
                ("智能手表 S10", "Smart Watch S10", "1.8英寸AMOLED屏幕，心率血氧监测，IP68防水", "1.8-inch AMOLED display, heart rate & SpO2 monitoring, IP68 waterproof", 28.50, "electronics", 300, 50, True),
                ("USB-C 快充数据线 2m", "USB-C Fast Charging Cable 2m", "100W PD快充，尼龙编织，兼容所有USB-C设备", "100W PD fast charging, nylon braided, compatible with all USB-C devices", 3.99, "electronics", 2000, 200, True),
                ("无线充电板 15W", "Wireless Charging Pad 15W", "Qi认证15W快充，超薄设计，LED指示灯", "Qi-certified 15W fast charge, ultra-slim design, LED indicator", 8.99, "electronics", 800, 100, False),
                ("便携蓝牙音箱", "Portable Bluetooth Speaker", "20W输出，360°环绕立体声，IPX7防水，12小时续航", "20W output, 360° surround sound, IPX7 waterproof, 12hr battery", 15.99, "electronics", 400, 50, True),
                # Machinery
                ("工业热风枪 2000W", "Industrial Heat Gun 2000W", "2000W大功率，双温档，过载保护，LCD温度显示", "2000W high power, dual temperature, overload protection, LCD display", 45.00, "machinery", 200, 10, True),
                ("电动螺丝刀套装 48合1", "Electric Screwdriver Set 48-in-1", "3.6V锂电池，磁吸批头，LED照明，扭矩可调", "3.6V lithium battery, magnetic bits, LED light, adjustable torque", 22.99, "machinery", 350, 20, True),
                ("CNC雕刻机 3018 Pro", "CNC Engraving Machine 3018 Pro", "工作面积300x180mm，支持木材/亚克力/PCB雕刻", "Working area 300x180mm, supports wood/acrylic/PCB engraving", 189.00, "machinery", 50, 5, False),
                # Textiles
                ("纯棉T恤 定制印刷", "Custom Printed Cotton T-Shirt", "100%纯棉，220g重磅，支持定制LOGO/图案", "100% cotton, 220g heavyweight, custom LOGO/design supported", 4.50, "textiles", 5000, 100, True),
                ("瑜伽运动套装 女款", "Yoga Activewear Set Women", "高弹力面料，吸湿排汗，四针六线工艺", "High-stretch fabric, moisture-wicking, flatlock stitching", 18.99, "textiles", 600, 50, True),
                ("帆布手提袋 定制", "Custom Canvas Tote Bag", "12oz帆布，多色可选，支持丝印/数码印", "12oz canvas, multiple colors, screen/digital printing", 2.99, "textiles", 10000, 500, True),
                # Home & Garden
                ("LED植物生长灯 1000W", "LED Grow Light 1000W", "全光谱，覆盖面积4x4ft，菊花链连接", "Full spectrum, coverage 4x4ft, daisy chain connection", 79.99, "home_garden", 150, 10, True),
                ("不锈钢真空保温杯 500ml", "Stainless Steel Vacuum Flask 500ml", "316不锈钢，12小时保温，激光雕刻定制", "316 stainless steel, 12hr insulation, laser engraving custom", 6.50, "home_garden", 3000, 200, True),
                ("硅胶厨房烘焙垫套装", "Silicone Baking Mat Set", "食品级硅胶，不粘防滑，耐温-40~230°C", "Food-grade silicone, non-stick, temperature -40~230°C", 5.99, "home_garden", 1500, 100, False),
                # Sports
                ("碳纤维羽毛球拍", "Carbon Fiber Badminton Racket", "全碳素，重量85g，穿线22-28lbs", "Full carbon, weight 85g, string tension 22-28lbs", 24.99, "sports", 250, 20, True),
                ("折叠露营椅 承重150kg", "Folding Camping Chair 150kg", "铝合金框架，600D牛津布，杯架扶手", "Aluminum frame, 600D Oxford fabric, cup holder armrest", 16.99, "sports", 400, 30, False),
                # Beauty
                ("超声波美容仪", "Ultrasonic Facial Device", "5MHz超声波，离子导入导出，红光蓝光", "5MHz ultrasonic, iontophoresis, red & blue light therapy", 32.00, "beauty", 300, 20, True),
                ("天然竹炭洗脸巾 100片", "Natural Bamboo Charcoal Face Towel 100pcs", "100%天然竹纤维，可降解，加厚设计", "100% natural bamboo fiber, biodegradable, extra thick", 3.50, "beauty", 5000, 300, True),
            ]
            for name_zh, name_en, desc_zh, desc_en, price, cat_slug, stock, moq, featured in products_data:
                p = Product(
                    name_zh=name_zh, name_en=name_en,
                    description_zh=desc_zh, description_en=desc_en,
                    price=price, currency="USD", stock=stock, moq=moq,
                    category_id=cats[cat_slug].id,
                    is_featured=featured, is_active=True,
                    image_url=f"https://placehold.co/600x600/667eea/ffffff?text={name_en.replace(' ', '+')}"
                )
                db.session.add(p)
            db.session.commit()
            print(f"Created {len(products_data)} products")

        print("\n=== Seed Complete! ===")
        print("Admin: admin@tradehub.com / admin123")
        print("Buyer: buyer@test.com / buyer123")

if __name__ == "__main__":
    seed()
