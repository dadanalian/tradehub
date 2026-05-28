import os, random, sys
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, User, Category, Product, CartItem, Order, OrderItem, Inquiry
from datetime import datetime

def create_app():
    app = Flask(__name__, instance_path=r"C:\\Users\\19668\\Documents\\Codex\\tradehub_instance")
    app.config.from_object(Config)
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Please login first"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_globals():
        lang = session.get("lang", "zh")
        categories = Category.query.all()
        return dict(lang=lang, get_categories=lambda: categories)

    def t(zh_text, en_text):
        lang = session.get("lang", "zh")
        return zh_text if lang == "zh" else en_text

    # ===== Home =====
    @app.route("/")
    def index():
        featured = Product.query.filter_by(is_featured=True, is_active=True).limit(8).all()
        categories = Category.query.all()
        return render_template("index.html", featured=featured, categories=categories)

    # ===== Language =====
    @app.route("/lang/<lang>")
    def set_lang(lang):
        if lang in ["zh", "en"]:
            session["lang"] = lang
        return redirect(request.referrer or url_for("index"))

    # ===== Auth =====
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            company = request.form.get("company", "").strip()
            phone = request.form.get("phone", "").strip()
            if User.query.filter_by(username=username).first():
                flash(t("Username already exists", "Username already exists"), "danger")
                return redirect(url_for("register"))
            if User.query.filter_by(email=email).first():
                flash(t("Email already registered", "Email already registered"), "danger")
                return redirect(url_for("register"))
            user = User(username=username, email=email, company=company, phone=phone)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash(t("Welcome to TradeHub!", "Welcome to TradeHub!"), "success")
            return redirect(url_for("index"))
        return render_template("auth/register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                login_user(user)
                flash(t("Login successful", "Login successful"), "success")
                next_page = request.args.get("next")
                return redirect(next_page or url_for("index"))
            flash(t("Invalid email or password", "Invalid email or password"), "danger")
        return render_template("auth/login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash(t("Logged out", "Logged out"), "info")
        return redirect(url_for("index"))

    # ===== Products =====
    @app.route("/products")
    def products():
        page = request.args.get("page", 1, type=int)
        category_slug = request.args.get("category")
        search = request.args.get("search", "").strip()
        sort = request.args.get("sort", "newest")
        query = Product.query.filter_by(is_active=True)
        if category_slug:
            cat = Category.query.filter_by(slug=category_slug).first()
            if cat:
                query = query.filter_by(category_id=cat.id)
        if search:
            query = query.filter(db.or_(
                Product.name_zh.contains(search),
                Product.name_en.contains(search),
                Product.description_zh.contains(search),
                Product.description_en.contains(search)
            ))
        if sort == "price_asc":
            query = query.order_by(Product.price.asc())
        elif sort == "price_desc":
            query = query.order_by(Product.price.desc())
        else:
            query = query.order_by(Product.created_at.desc())
        products_list = query.paginate(page=page, per_page=12)
        categories = Category.query.all()
        return render_template("products/list.html", products=products_list, categories=categories,
                             current_category=category_slug, search=search, sort=sort)

    @app.route("/product/<int:product_id>")
    def product_detail(product_id):
        product = Product.query.get_or_404(product_id)
        related = Product.query.filter_by(category_id=product.category_id, is_active=True)\
                              .filter(Product.id != product.id).limit(4).all()
        return render_template("products/detail.html", product=product, related=related)

    # ===== Cart =====
    @app.route("/cart")
    @login_required
    def cart():
        items = CartItem.query.filter_by(user_id=current_user.id).all()
        total = sum(item.product.price * item.quantity for item in items)
        return render_template("cart/cart.html", items=items, total=total)

    @app.route("/cart/count")
    @login_required
    def cart_count():
        count = CartItem.query.filter_by(user_id=current_user.id).count()
        return jsonify({"count": count})

    @app.route("/cart/add/<int:product_id>", methods=["POST"])
    @login_required
    def cart_add(product_id):
        quantity = request.form.get("quantity", 1, type=int)
        existing = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if existing:
            existing.quantity += quantity
        else:
            item = CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity)
            db.session.add(item)
        db.session.commit()
        flash(t("Added to cart", "Added to cart"), "success")
        return redirect(url_for("cart"))

    @app.route("/cart/update/<int:item_id>", methods=["POST"])
    @login_required
    def cart_update(item_id):
        item = CartItem.query.get_or_404(item_id)
        if item.user_id != current_user.id:
            return jsonify({"error": "Unauthorized"}), 403
        quantity = request.json.get("quantity", 1)
        if quantity < 1:
            quantity = 1
        item.quantity = quantity
        db.session.commit()
        total = sum(i.product.price * i.quantity for i in CartItem.query.filter_by(user_id=current_user.id).all())
        subtotal = item.product.price * item.quantity
        return jsonify({"success": True, "subtotal": f"{subtotal:.2f}", "total": f"{total:.2f}"})

    @app.route("/cart/remove/<int:item_id>", methods=["POST"])
    @login_required
    def cart_remove(item_id):
        item = CartItem.query.get_or_404(item_id)
        if item.user_id != current_user.id:
            return jsonify({"error": "Unauthorized"}), 403
        db.session.delete(item)
        db.session.commit()
        return redirect(url_for("cart"))

    # ===== Checkout =====
    @app.route("/checkout", methods=["GET", "POST"])
    @login_required
    def checkout():
        items = CartItem.query.filter_by(user_id=current_user.id).all()
        if not items:
            flash(t("Cart is empty", "Cart is empty"), "warning")
            return redirect(url_for("cart"))
        total = sum(item.product.price * item.quantity for item in items)
        if request.method == "POST":
            order = Order(
                user_id=current_user.id, total_amount=total,
                shipping_address=request.form.get("shipping_address", ""),
                contact_name=request.form.get("contact_name", current_user.username),
                contact_email=request.form.get("contact_email", current_user.email),
                contact_phone=request.form.get("contact_phone", current_user.phone or ""),
                notes=request.form.get("notes", "")
            )
            db.session.add(order)
            for item in items:
                oi = OrderItem(order=order, product_id=item.product_id, quantity=item.quantity, price=item.product.price)
                db.session.add(oi)
                db.session.delete(item)
            db.session.commit()
            flash(t("Order submitted! We will process it soon", "Order submitted! We will process it soon"), "success")
            return redirect(url_for("order_detail", order_id=order.id))
        return render_template("orders/checkout.html", items=items, total=total)

    @app.route("/orders")
    @login_required
    def orders():
        orders_list = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
        return render_template("orders/list.html", orders=orders_list)

    @app.route("/order/<int:order_id>")
    @login_required
    def order_detail(order_id):
        order = Order.query.get_or_404(order_id)
        if order.user_id != current_user.id and not current_user.is_admin:
            flash("Unauthorized", "danger")
            return redirect(url_for("index"))
        return render_template("orders/detail.html", order=order)

    # ===== Inquiry =====
    @app.route("/inquiry/<int:product_id>", methods=["POST"])
    def inquiry(product_id):
        inquiry = Inquiry(
            name=request.form.get("name", ""), email=request.form.get("email", ""),
            company=request.form.get("company", ""), phone=request.form.get("phone", ""),
            product_id=product_id, message=request.form.get("message", "")
        )
        db.session.add(inquiry)
        db.session.commit()
        flash(t("Inquiry sent!", "Inquiry sent!"), "success")
        return redirect(url_for("product_detail", product_id=product_id))

    # ===== Chat =====
    @app.route("/chat")
    def chat():
        return render_template("chat/chat.html")

    @app.route("/api/chat", methods=["POST"])
    def api_chat():
        data = request.json
        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({"reply": t("Please enter a question", "Please enter a question")})
        reply = get_chatbot_response(user_message)
        return jsonify({"reply": reply})

    # ===== Admin =====
    @app.route("/admin")
    @login_required
    def admin():
        if not current_user.is_admin:
            flash("Unauthorized", "danger")
            return redirect(url_for("index"))
        stats = {
            "products": Product.query.count(), "orders": Order.query.count(),
            "users": User.query.count(), "inquiries": Inquiry.query.filter_by(is_read=False).count(),
            "recent_orders": Order.query.order_by(Order.created_at.desc()).limit(5).all(),
            "recent_inquiries": Inquiry.query.filter_by(is_read=False).order_by(Inquiry.created_at.desc()).limit(5).all()
        }
        return render_template("admin/dashboard.html", stats=stats)

    @app.route("/admin/products")
    @login_required
    def admin_products():
        if not current_user.is_admin: return redirect(url_for("index"))
        products = Product.query.order_by(Product.created_at.desc()).all()
        return render_template("admin/products.html", products=products)

    @app.route("/admin/product/add", methods=["GET", "POST"])
    @login_required
    def admin_product_add():
        if not current_user.is_admin: return redirect(url_for("index"))
        if request.method == "POST":
            product = Product(
                name_zh=request.form.get("name_zh", ""), name_en=request.form.get("name_en", ""),
                description_zh=request.form.get("description_zh", ""), description_en=request.form.get("description_en", ""),
                price=float(request.form.get("price", 0)), stock=int(request.form.get("stock", 0)),
                image_url=request.form.get("image_url", ""), category_id=int(request.form.get("category_id", 1)),
                moq=int(request.form.get("moq", 1)), is_featured="is_featured" in request.form
            )
            db.session.add(product)
            db.session.commit()
            flash("Product added!", "success")
            return redirect(url_for("admin_products"))
        categories = Category.query.all()
        return render_template("admin/product_form.html", categories=categories, product=None)

    @app.route("/admin/product/edit/<int:product_id>", methods=["GET", "POST"])
    @login_required
    def admin_product_edit(product_id):
        if not current_user.is_admin: return redirect(url_for("index"))
        product = Product.query.get_or_404(product_id)
        if request.method == "POST":
            product.name_zh = request.form.get("name_zh", "")
            product.name_en = request.form.get("name_en", "")
            product.description_zh = request.form.get("description_zh", "")
            product.description_en = request.form.get("description_en", "")
            product.price = float(request.form.get("price", 0))
            product.stock = int(request.form.get("stock", 0))
            product.image_url = request.form.get("image_url", "")
            product.category_id = int(request.form.get("category_id", 1))
            product.moq = int(request.form.get("moq", 1))
            product.is_featured = "is_featured" in request.form
            product.is_active = "is_active" in request.form
            db.session.commit()
            flash("Product updated!", "success")
            return redirect(url_for("admin_products"))
        categories = Category.query.all()
        return render_template("admin/product_form.html", categories=categories, product=product)

    @app.route("/admin/orders")
    @login_required
    def admin_orders():
        if not current_user.is_admin: return redirect(url_for("index"))
        orders_list = Order.query.order_by(Order.created_at.desc()).all()
        return render_template("admin/orders.html", orders=orders_list)

    @app.route("/admin/order/<int:order_id>/status", methods=["POST"])
    @login_required
    def admin_order_status(order_id):
        if not current_user.is_admin: return jsonify({"error": "Unauthorized"}), 403
        order = Order.query.get_or_404(order_id)
        status = request.form.get("status")
        if status in ["pending", "confirmed", "shipped", "delivered", "cancelled"]:
            order.status = status
            db.session.commit()
        return redirect(url_for("admin_orders"))

    @app.route("/admin/inquiries")
    @login_required
    def admin_inquiries():
        if not current_user.is_admin: return redirect(url_for("index"))
        inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
        return render_template("admin/inquiries.html", inquiries=inquiries)

    @app.route("/admin/inquiry/<int:inquiry_id>/read", methods=["POST"])
    @login_required
    def admin_inquiry_read(inquiry_id):
        if not current_user.is_admin: return jsonify({"error": "Unauthorized"}), 403
        inquiry = Inquiry.query.get_or_404(inquiry_id)
        inquiry.is_read = True
        db.session.commit()
        return redirect(url_for("admin_inquiries"))

    return app

def get_chatbot_response(message):
    msg = message.lower()
    if any(w in msg for w in ["hello", "hi", "hey"]):
        return random.choice([
            "Hello! I am LobsterBot \U0001f99e, your TradeHub assistant. I can help with products, pricing, shipping, payment, and more!\n\nHow can I help you today?",
            "Hi there! \U0001f44b I am LobsterBot, here to help with your sourcing needs. What are you looking for?"
        ])
    if any(w in msg for w in ["product", "products"]):
        products = Product.query.filter_by(is_active=True).limit(5).all()
        if products:
            lines = ["Here are some popular products:\n"]
            for p in products:
                lines.append(f"\u2022 {p.name_en} / {p.name_zh} - ${p.price:.2f} {p.currency}")
            return "\n".join(lines)
        return "We offer electronics, machinery, textiles, and more. Browse our Products page!"
    if any(w in msg for w in ["price", "pricing", "moq", "minimum"]):
        return "Prices vary by product and quantity. Most products have MOQ requirements. Bulk orders get competitive discounts. Check product pages or send an inquiry!"
    if any(w in msg for w in ["ship", "shipping", "delivery"]):
        return "We ship worldwide via sea freight, air freight, and express (DHL, FedEx, UPS). Delivery: 7-30 days. Free shipping on orders over $5000!"
    if any(w in msg for w in ["pay", "payment", "tt", "l/c", "paypal"]):
        return "Accepted: T/T, L/C, PayPal, Western Union, Alibaba Trade Assurance. New customers: 30% deposit, 70% before shipment."
    if any(w in msg for w in ["about", "company"]):
        return "TradeHub is a leading B2B platform connecting global buyers with quality Chinese manufacturers. All suppliers verified. Making global trade simple!"
    if any(w in msg for w in ["contact", "email", "phone"]):
        return "Email: support@tradehub.com | Phone: +86-400-888-9999 | Address: Shenzhen, Guangdong, China"
    return "I am LobsterBot! I can help with: products, pricing, shipping, payment, company info, contact. What would you like to know?"


def auto_seed():
    from models import User, Category, Product
    if User.query.first() is not None:
        return
    admin = User(username="admin", email="admin@tradehub.com", company="TradeHub Inc", phone="+86-400-888-9999")
    admin.set_password("admin123")
    admin.is_admin = True
    db.session.add(admin)
    buyer = User(username="buyer", email="buyer@test.com", company="Global Trade Co", phone="+1-555-0123")
    buyer.set_password("buyer123")
    db.session.add(buyer)
    cats_data = [
        ("electronics", "电子产品", "Electronics", "\U0001f4bb"),
        ("machinery", "机械设备", "Machinery", "\u2699\ufe0f"),
        ("textiles", "纺织服装", "Textiles & Apparel", "\U0001f455"),
        ("home_garden", "家居园艺", "Home & Garden", "\U0001f3e0"),
        ("sports", "运动户外", "Sports & Outdoors", "\u26bd"),
        ("beauty", "美容个护", "Beauty & Personal Care", "\U0001f484"),
    ]
    cats = {}
    for slug, name_zh, name_en, icon in cats_data:
        cat = Category(slug=slug, name_zh=name_zh, name_en=name_en, image_url=icon)
        db.session.add(cat)
        cats[slug] = cat
    products_data = [
        ("Bluetooth Earphones Pro", "Bluetooth Earphones Pro", "Premium noise-cancelling BT earphones, 30hr battery", "Premium noise-cancelling BT earphones, 30hr battery", 12.99, "electronics", 500, 100, True),
        ("Smart Watch S10", "Smart Watch S10", "1.8-inch AMOLED, heart rate & SpO2 monitoring", "1.8-inch AMOLED, heart rate & SpO2 monitoring", 28.50, "electronics", 300, 50, True),
        ("USB-C Fast Charging Cable", "USB-C Fast Charging Cable", "100W PD fast charging, nylon braided", "100W PD fast charging, nylon braided", 3.99, "electronics", 2000, 200, True),
        ("Wireless Charging Pad", "Wireless Charging Pad", "Qi-certified 15W fast charge, ultra-slim", "Qi-certified 15W fast charge, ultra-slim", 8.99, "electronics", 800, 100, False),
        ("Portable Bluetooth Speaker", "Portable Bluetooth Speaker", "20W output, 360 surround, IPX7 waterproof", "20W output, 360 surround, IPX7 waterproof", 15.99, "electronics", 400, 50, True),
        ("Industrial Heat Gun 2000W", "Industrial Heat Gun 2000W", "2000W, dual temperature, overload protection", "2000W, dual temperature, overload protection", 45.00, "machinery", 200, 10, True),
        ("Electric Screwdriver Set 48-in-1", "Electric Screwdriver Set 48-in-1", "3.6V lithium, magnetic bits, LED light", "3.6V lithium, magnetic bits, LED light", 22.99, "machinery", 350, 20, True),
        ("CNC Engraving Machine 3018 Pro", "CNC Engraving Machine 3018 Pro", "Working area 300x180mm, multi-material", "Working area 300x180mm, multi-material", 189.00, "machinery", 50, 5, False),
        ("Custom Printed Cotton T-Shirt", "Custom Printed Cotton T-Shirt", "100pct cotton, 220g, custom printing", "100pct cotton, 220g, custom printing", 4.50, "textiles", 5000, 100, True),
        ("Yoga Activewear Set", "Yoga Activewear Set", "High-stretch, moisture-wicking fabric", "High-stretch, moisture-wicking fabric", 18.99, "textiles", 600, 50, True),
        ("Custom Canvas Tote Bag", "Custom Canvas Tote Bag", "12oz canvas, multiple colors, print", "12oz canvas, multiple colors, print", 2.99, "textiles", 10000, 500, True),
        ("LED Grow Light 1000W", "LED Grow Light 1000W", "Full spectrum, coverage 4x4ft", "Full spectrum, coverage 4x4ft", 79.99, "home_garden", 150, 10, True),
        ("Stainless Steel Vacuum Flask", "Stainless Steel Vacuum Flask", "316 stainless steel, 12hr insulation", "316 stainless steel, 12hr insulation", 6.50, "home_garden", 3000, 200, True),
        ("Silicone Baking Mat Set", "Silicone Baking Mat Set", "Food-grade silicone, non-stick", "Food-grade silicone, non-stick", 5.99, "home_garden", 1500, 100, False),
        ("Carbon Fiber Badminton Racket", "Carbon Fiber Badminton Racket", "Full carbon, weight 85g", "Full carbon, weight 85g", 24.99, "sports", 250, 20, True),
        ("Folding Camping Chair", "Folding Camping Chair", "Aluminum frame, 600D Oxford fabric", "Aluminum frame, 600D Oxford fabric", 16.99, "sports", 400, 30, False),
        ("Ultrasonic Facial Device", "Ultrasonic Facial Device", "5MHz ultrasonic, iontophoresis", "5MHz ultrasonic, iontophoresis", 32.00, "beauty", 300, 20, True),
        ("Bamboo Charcoal Face Towel 100pcs", "Bamboo Charcoal Face Towel 100pcs", "100pct natural bamboo fiber, biodegradable", "100pct natural bamboo fiber, biodegradable", 3.50, "beauty", 5000, 300, True),
    ]
    for name_zh, name_en, desc_zh, desc_en, price, cat_slug, stock, moq, featured in products_data:
        p = Product(name_zh=name_zh, name_en=name_en, description_zh=desc_zh, description_en=desc_en,
                    price=price, currency="USD", stock=stock, moq=moq, category_id=cats[cat_slug].id,
                    is_featured=featured, is_active=True,
                    image_url=f"https://placehold.co/600x600/667eea/ffffff?text={name_en.replace(' ', '+')}")
        db.session.add(p)
    db.session.commit()
    print("Auto-seed complete!")


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        auto_seed()
    app.run(debug=True, port=5000)
