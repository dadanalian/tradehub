import os, random
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, User, Category, Product, CartItem, Order, OrderItem, Inquiry, Message, Notification, MerchantSettings
from translations import t, LANGUAGES

def create_app():
    app = Flask(__name__, instance_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance"))
    app.config.from_object(Config)
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_globals():
        lang = session.get("lang", "en")
        return {
            "lang": lang,
            "t": lambda key: t(key, lang),
            "languages": LANGUAGES,
            "get_categories": lambda: Category.query.all(),
        }

    @app.route("/")
    def index():
        featured = Product.query.filter_by(is_featured=True, is_active=True).limit(8).all()
        categories = Category.query.all()
        return render_template("index.html", featured=featured, categories=categories)

    @app.route("/set-lang/<lang>")
    def set_lang(lang):
        if lang in LANGUAGES:
            session["lang"] = lang
        return redirect(request.referrer or url_for("index"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            if User.query.filter_by(username=username).first():
                flash("Username already exists", "danger")
                return redirect(url_for("register"))
            if User.query.filter_by(email=email).first():
                flash("Email already registered", "danger")
                return redirect(url_for("register"))
            user = User(username=username, email=email,
                       company=request.form.get("company", "").strip(),
                       phone=request.form.get("phone", "").strip())
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Registration successful! Welcome to TradeHub", "success")
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
                flash("Login successful", "success")
                next_page = request.args.get("next")
                return redirect(next_page or url_for("index"))
            flash("Invalid email or password", "danger")
        return render_template("auth/login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Logged out", "info")
        return redirect(url_for("index"))

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
        return render_template("products/list.html", products=products_list,
                             categories=categories, current_category=category_slug,
                             search=search, sort=sort)

    @app.route("/product/<int:product_id>")
    def product_detail(product_id):
        product = Product.query.get_or_404(product_id)
        related = Product.query.filter_by(category_id=product.category_id, is_active=True)\
                              .filter(Product.id != product.id).limit(4).all()
        return render_template("products/detail.html", product=product, related=related)

    def get_guest_cart():
        cart = session.get("guest_cart", {})
        items = []
        total = 0.0
        for pid, qty in cart.items():
            p = Product.query.get(int(pid))
            if p:
                items.append({"product": p, "quantity": qty, "id": pid})
                total += p.price * qty
        return items, total

    @app.route("/cart")
    def cart():
        if current_user.is_authenticated:
            items = CartItem.query.filter_by(user_id=current_user.id).all()
            total = sum(item.product.price * item.quantity for item in items)
        else:
            raw_items, total = get_guest_cart()
            items = []
            for ri in raw_items:
                class GI: pass
                gi = GI()
                gi.product = ri["product"]
                gi.quantity = ri["quantity"]
                gi.id = ri["id"]
                items.append(gi)
        return render_template("cart/cart.html", items=items, total=total)

    @app.route("/cart/add/<int:product_id>", methods=["POST"])
    def cart_add(product_id):
        quantity = request.form.get("quantity", 1, type=int)
        if current_user.is_authenticated:
            existing = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
            if existing:
                existing.quantity += quantity
            else:
                db.session.add(CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity))
            db.session.commit()
        else:
            cart = session.get("guest_cart", {})
            pid_str = str(product_id)
            cart[pid_str] = cart.get(pid_str, 0) + quantity
            session["guest_cart"] = cart
        flash("Added to cart", "success")
        return redirect(url_for("cart"))

    @app.route("/cart/update/<int:item_id>", methods=["POST"])
    def cart_update(item_id):
        item = CartItem.query.get_or_404(item_id)
        if item.user_id != current_user.id:
            return jsonify({"error": "Unauthorized"}), 403
        item.quantity = max(1, request.json.get("quantity", 1))
        db.session.commit()
        total = sum(i.product.price * i.quantity for i in CartItem.query.filter_by(user_id=current_user.id).all())
        return jsonify({"success": True, "subtotal": f"{item.product.price * item.quantity:.2f}", "total": f"{total:.2f}"})

    @app.route("/cart/remove/<int:item_id>", methods=["POST"])
    def cart_remove(item_id):
        item = CartItem.query.get_or_404(item_id)
        if item.user_id != current_user.id:
            return jsonify({"error": "Unauthorized"}), 403
        db.session.delete(item)
        db.session.commit()
        return redirect(url_for("cart"))

    # GUEST CHECKOUT - no login required
    @app.route("/checkout", methods=["GET", "POST"])
    def checkout():
        order_items = []
        if current_user.is_authenticated:
            items = CartItem.query.filter_by(user_id=current_user.id).all()
            total = sum(item.product.price * item.quantity for item in items)
            for item in items:
                order_items.append((item.product, item.quantity, item.product.price))
        else:
            raw_items, total = get_guest_cart()
            items = []
            for ri in raw_items:
                class GI: pass
                gi = GI()
                gi.product = ri["product"]
                gi.quantity = ri["quantity"]
                gi.id = ri["id"]
                items.append(gi)
                order_items.append((ri["product"], ri["quantity"], ri["product"].price))

        if request.method == "POST":
            order = Order(
                user_id=current_user.id if current_user.is_authenticated else 1,
                total_amount=total,
                shipping_address=request.form.get("shipping_address", ""),
                contact_name=request.form.get("contact_name", ""),
                contact_email=request.form.get("contact_email", ""),
                contact_phone=request.form.get("contact_phone", ""),
                notes=request.form.get("notes", ""),
                status="pending"
            )
            db.session.add(order)
            for prod, qty, price in order_items:
                db.session.add(OrderItem(order=order, product_id=prod.id, quantity=qty, price=price))
            if current_user.is_authenticated:
                CartItem.query.filter_by(user_id=current_user.id).delete()
            else:
                session.pop("guest_cart", None)
            db.session.commit()
            flash("Order submitted successfully! We will contact you soon.", "success")
            push_wx(f"New Order #{order.id}", f"Customer: {order.contact_name}\nEmail: {order.contact_email}\nAmount: ${order.total_amount:.2f}\n\nView: https://shijingyuan.pythonanywhere.com/merchant/orders")
            notify_merchant("new_order", f"New Order #{order.id}", f"Customer: {order.contact_name}\nEmail: {order.contact_email}\nAmount: ${order.total_amount:.2f}\nAddress: {order.shipping_address}")
            return redirect(url_for("payment_info", order_id=order.id))
        return render_template("orders/checkout.html", items=items, total=total)

    @app.route("/payment/<int:order_id>")
    def payment_info(order_id):
        order = Order.query.get_or_404(order_id)
        return render_template("orders/payment.html", order=order)

    @app.route("/orders")
    def orders():
        if not current_user.is_authenticated:
            return redirect(url_for("login"))
        orders_list = Order.query.filter_by(user_id=current_user.id)\
                                .order_by(Order.created_at.desc()).all()
        return render_template("orders/list.html", orders=orders_list)

    @app.route("/order/<int:order_id>")
    def order_detail(order_id):
        order = Order.query.get_or_404(order_id)
        return render_template("orders/detail.html", order=order)

    @app.route("/inquiry/<int:product_id>", methods=["POST"])
    def inquiry(product_id):
        db.session.add(Inquiry(
            name=request.form.get("name", ""),
            email=request.form.get("email", ""),
            company=request.form.get("company", ""),
            phone=request.form.get("phone", ""),
            product_id=product_id,
            message=request.form.get("message", "")
        ))
        db.session.commit()
        flash("Inquiry sent! We will reply soon.", "success")
        push_wx(f"New Inquiry", f"From: {inquiry.name}\nEmail: {inquiry.email}\n\n{inquiry.message[:200]}\n\nView: https://shijingyuan.pythonanywhere.com/merchant/messages")
        notify_merchant("new_inquiry", f"New Inquiry about #{product_id}", f"From: {inquiry.name}\nEmail: {inquiry.email}\n\n{inquiry.message[:200]}")
        return redirect(url_for("product_detail", product_id=product_id))

    @app.route("/chat")
    def chat():
        return render_template("chat/chat.html")

    @app.route("/api/chat", methods=["POST"])
    def api_chat():
        msg = request.json.get("message", "").strip()
        if not msg:
            return jsonify({"reply": "Please enter a question."})
        return jsonify({"reply": get_chatbot_response(msg)})

    # Admin
    @app.route("/admin")
    @login_required
    def admin():
        if not current_user.is_admin:
            flash("Unauthorized", "danger")
            return redirect(url_for("index"))
        stats = {
            "products": Product.query.count(),
            "orders": Order.query.count(),
            "users": User.query.count(),
            "inquiries": Inquiry.query.filter_by(is_read=False).count(),
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
                name_zh=request.form.get("name_zh", ""),
                name_en=request.form.get("name_en", ""),
                description_zh=request.form.get("description_zh", ""),
                description_en=request.form.get("description_en", ""),
                price=float(request.form.get("price", 0)),
                stock=int(request.form.get("stock", 0)),
                image_url=request.form.get("image_url", ""),
                category_id=int(request.form.get("category_id", 1)),
                moq=int(request.form.get("moq", 1)),
                is_featured="is_featured" in request.form
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


    def notify_merchant(ntype, title, content):
        """Send notification and try email"""
        notif = Notification(type=ntype, title=title, content=content)
        db.session.add(notif)
        db.session.commit()
        # Try email notification
        settings = MerchantSettings.query.first()
        if settings and settings.notify_email:
            try:
                send_email(settings.notify_email, title, content)
            except:
                pass


    def push_wx(title, content):
        """Send push notification to WeChat via Server酱"""
        import urllib.request, urllib.parse
        try:
            data = urllib.parse.urlencode({"title": title, "desp": content}).encode()
            req = urllib.request.Request("https://sctapi.ftqq.com/SCT356107TdAGEbh1QAfmdcjQxlsJGvQQc.send", data=data, method="POST")
            urllib.request.urlopen(req, timeout=10)
            return True
        except:
            return False

    def send_email(to_email, subject, body):
        """Send email via QQ SMTP"""
        import smtplib
        from email.mime.text import MIMEText
        try:
            msg = MIMEText(body, "plain", "utf-8")
            msg["Subject"] = subject
            msg["From"] = "TradeHub <1966899806@qq.com>"
            msg["To"] = to_email
            s = smtplib.SMTP_SSL("smtp.qq.com", 465, timeout=10)
            s.login("1966899806@qq.com", "")  # SMTP password needs to be configured
            s.sendmail("1966899806@qq.com", [to_email], msg.as_string())
            s.quit()
            return True
        except Exception as e:
            print(f"Email failed: {e}")
            return False


    # ===== Merchant Dashboard =====
    @app.route("/merchant")
    @login_required
    def merchant():
        if not current_user.is_admin:
            flash("Unauthorized", "danger")
            return redirect(url_for("index"))
        stats = {
            "total_orders": Order.query.count(),
            "pending_orders": Order.query.filter_by(status="pending").count(),
            "total_revenue": db.session.query(db.func.sum(Order.total_amount)).scalar() or 0,
            "unread_messages": Message.query.filter_by(is_read=False, is_from_merchant=False).count(),
            "recent_orders": Order.query.order_by(Order.created_at.desc()).limit(8).all(),
            "recent_messages": Message.query.filter_by(is_from_merchant=False).order_by(Message.created_at.desc()).limit(5).all(),
            "notifications": Notification.query.order_by(Notification.created_at.desc()).limit(10).all(),
        }
        return render_template("merchant/dashboard.html", stats=stats)

    @app.route("/merchant/orders")
    @login_required
    def merchant_orders():
        if not current_user.is_admin: return redirect(url_for("index"))
        status_filter = request.args.get("status", "")
        query = Order.query
        if status_filter:
            query = query.filter_by(status=status_filter)
        orders = query.order_by(Order.created_at.desc()).all()
        return render_template("merchant/orders.html", orders=orders, status_filter=status_filter)

    @app.route("/merchant/order/<int:order_id>")
    @login_required
    def merchant_order_detail(order_id):
        if not current_user.is_admin: return redirect(url_for("index"))
        order = Order.query.get_or_404(order_id)
        return render_template("merchant/order_detail.html", order=order)

    @app.route("/merchant/order/<int:order_id>/status", methods=["POST"])
    @login_required
    def merchant_update_status(order_id):
        if not current_user.is_admin: return jsonify({"error": "Unauthorized"}), 403
        order = Order.query.get_or_404(order_id)
        new_status = request.form.get("status")
        tracking = request.form.get("tracking_number", "")
        if new_status in ["pending", "confirmed", "shipped", "delivered", "cancelled"]:
            order.status = new_status
            if tracking:
                order.notes = (order.notes or "") + f"\nTracking: {tracking}"
            db.session.commit()
        return redirect(url_for("merchant_order_detail", order_id=order_id))

    # ===== Messages / Chat =====
    @app.route("/merchant/messages")
    @login_required
    def merchant_messages():
        if not current_user.is_admin: return redirect(url_for("index"))
        messages = Message.query.order_by(Message.created_at.desc()).all()
        # Mark all as read
        Message.query.filter_by(is_read=False, is_from_merchant=False).update({"is_read": True})
        db.session.commit()
        # Group by sender
        conversations = {}
        for msg in messages:
            key = msg.sender_email
            if key not in conversations:
                conversations[key] = []
            conversations[key].append(msg)
        return render_template("merchant/messages.html", conversations=conversations, messages=messages)

    @app.route("/merchant/messages/reply", methods=["POST"])
    @login_required
    def merchant_reply():
        if not current_user.is_admin: return jsonify({"error": "Unauthorized"}), 403
        reply_to_email = request.form.get("email")
        content = request.form.get("content")
        if not content or not reply_to_email:
            return redirect(url_for("merchant_messages"))
        msg = Message(sender_email="merchant@tradehub.com", sender_name="Merchant",
                      content="[Re: " + reply_to_email + "] " + content, is_from_merchant=True, is_read=True)
        db.session.add(msg)
        db.session.commit()
        flash("Reply sent", "success")
        return redirect(url_for("merchant_messages"))

    @app.route("/api/messages", methods=["POST"])
    def api_send_message():
        data = request.json
        email = data.get("email", "anonymous")
        content = data.get("content", "")
        if not content:
            return jsonify({"error": "empty"}), 400
        msg = Message(
            sender_email=email,
            sender_name=data.get("name", "Customer"),
            content=content,
            is_from_merchant=False,
            is_read=False
        )
        db.session.add(msg)
        db.session.commit()
        # Try email notification
        try:
            settings = MerchantSettings.query.first()
            if settings and settings.notify_email:
                send_email(settings.notify_email, f"New message from {msg.sender_name}", f"From: {msg.sender_name} ({msg.sender_email})\n\n{msg.content}\n\nReply at: https://shijingyuan.pythonanywhere.com/merchant/messages")
        except:
            pass
        push_wx(f"New message from {msg.sender_name}", f"{msg.sender_name} ({msg.sender_email})\n\n{msg.content[:300]}\n\nReply: https://shijingyuan.pythonanywhere.com/merchant/messages")
        notify_merchant("new_message", f"New message from {msg.sender_name}",
                        f"From: {msg.sender_name} ({msg.sender_email})\n\n{msg.content[:200]}")
        try:
            import urllib.request, urllib.parse
            push_data = urllib.parse.urlencode({"title": f"New message from {msg.sender_name}", "desp": f"{msg.sender_name} ({msg.sender_email})\n\n{msg.content[:300]}"}).encode()
            urllib.request.urlopen(urllib.request.Request("https://sctapi.ftqq.com/SCT356107TdAGEbh1QAfmdcjQxlsJGvQQc.send", data=push_data, method="POST"), timeout=8)
        except:
            pass
        return jsonify({"success": True})

    @app.route("/api/messages/<email>")
    def api_get_messages(email):
        msgs = Message.query.filter(
            db.or_(Message.sender_email == email, Message.sender_email.like("%merchant%"))
        ).filter(
            db.or_(Message.sender_email == email, Message.content.like("%"))
        ).order_by(Message.created_at.asc()).all()
        # Simpler: get all recent messages
        msgs = Message.query.order_by(Message.created_at.desc()).limit(50).all()
        msgs.reverse()
        return jsonify([{
            "content": m.content,
            "is_from_merchant": m.is_from_merchant,
            "created_at": m.created_at.strftime("%H:%M"),
            "sender_name": m.sender_name
        } for m in msgs])

    @app.route("/api/messages/all")
    def api_messages_all():
        msgs = Message.query.order_by(Message.created_at.asc()).limit(100).all()
        return jsonify([{"content": m.content, "is_from_merchant": m.is_from_merchant, "created_at": m.created_at.strftime("%H:%M"), "sender_name": m.sender_name} for m in msgs])

    @app.route("/api/messages/unread")
    @login_required
    def api_unread_count():
        if not current_user.is_admin:
            return jsonify({"count": 0})
        count = Message.query.filter_by(is_read=False, is_from_merchant=False).count()
        return jsonify({"count": count})

    # ===== Merchant Settings =====
    @app.route("/merchant/settings", methods=["GET", "POST"])
    @login_required
    def merchant_settings():
        if not current_user.is_admin: return redirect(url_for("index"))
        settings = MerchantSettings.query.first()
        if not settings:
            settings = MerchantSettings()
            db.session.add(settings)
            db.session.commit()
        if request.method == "POST":
            settings.notify_email = request.form.get("notify_email", "")
            settings.paypal_email = request.form.get("paypal_email", "")
            settings.bank_name = request.form.get("bank_name", "")
            settings.bank_account = request.form.get("bank_account", "")
            settings.bank_swift = request.form.get("bank_swift", "")
            settings.account_holder = request.form.get("account_holder", "")
            db.session.commit()
            flash("Settings saved", "success")
            return redirect(url_for("merchant_settings"))
        return render_template("merchant/settings.html", settings=settings)



    @app.route("/update/<token>")
    def update_by_token(token):
        if token != "tradehub2026":
            return "Invalid token", 403
        import subprocess
        result = subprocess.run(["git", "pull", "origin", "master"], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        try:
            db.create_all()
            auto_seed()
        except:
            pass
            admin = User.query.filter_by(username="admin").first()
            if admin:
                admin.email = "1966899806@qq.com"
                admin.set_password("smy..521")
                db.session.commit()
        except:
            pass
        return f"OK {result.stdout[:100]}"

    @app.route("/admin/auto-update")
    @login_required
    def auto_update():
        if not current_user.is_admin:
            return "Unauthorized", 403
        import subprocess
        result = subprocess.run(["git", "pull", "origin", "master"], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        # Re-seed
        try:
            db.create_all()
            auto_seed()
        except:
            pass
        except:
            pass
        # Update admin credentials
        admin = User.query.filter_by(username="admin").first()
        if admin:
            admin.email = "1966899806@qq.com"
            admin.set_password("smy..521")
            db.session.commit()
        return f"<pre>Git Pull:\n{result.stdout}\n{result.stderr}\n\nSeed: Done. Admin updated.\n\n<a href='/'>Go to site</a></pre>"

    return app

def get_chatbot_response(message):
    msg = message.lower()
    if any(w in msg for w in ["hello", "hi", "hey"]):
        return random.choice([
            "Hello! I'm LobsterBot, your AI trade assistant. I can help with products, pricing, shipping, payment methods, and more. How can I help you today?",
            "Hi there! I'm here to help with your sourcing needs. What products are you looking for?",
        ])
    if any(w in msg for w in ["product", "products", "sell"]):
        products = Product.query.filter_by(is_active=True).limit(5).all()
        if products:
            return "Here are some popular products:\n" + "\n".join(f"• {p.name_en} - ${p.price:.2f}" for p in products)
        return "We offer electronics, machinery, textiles, and more. Browse our Products page for the full catalog!"
    if any(w in msg for w in ["price", "pricing", "moq", "minimum"]):
        return "Prices vary by product and quantity. Most products have MOQ requirements. Bulk orders get competitive discounts. Check product pages or send an inquiry for detailed pricing!"
    if any(w in msg for w in ["ship", "shipping", "delivery"]):
        return "We ship worldwide via sea freight (15-30 days), air freight (5-10 days), and express couriers DHL/FedEx/UPS (3-7 days). Shipping cost calculated at checkout. Free shipping on orders over $5000!"
    if any(w in msg for w in ["pay", "payment", "tt", "paypal", "credit card"]):
        return "We accept: Credit/Debit Cards, PayPal, T/T Bank Transfer, Western Union, and Alibaba Trade Assurance. For new customers: 30% deposit, 70% before shipment. All payments are secure."
    if any(w in msg for w in ["about", "company", "who"]):
        return "TradeHub is a leading B2B platform connecting global buyers with quality Chinese manufacturers. We verify all suppliers to ensure product quality and reliable delivery."
    if any(w in msg for w in ["contact", "email", "phone"]):
        return "Email: support@tradehub.com | Phone: +86-400-888-9999 | Address: Shenzhen, Guangdong, China | We're available 24/7!"
    return "I'm LobsterBot, your AI trade assistant! I can help with:\n• Product inquiries\n• Pricing & MOQ\n• Shipping & logistics\n• Payment methods\n• Company information\n\nWhat would you like to know?"

def auto_seed():
    if User.query.first() is not None:
        return
    admin = User(username="admin", email="1966899806@qq.com", company="TradeHub Inc", phone="+86-400-888-9999")
    admin.set_password("smy..521")
    admin.is_admin = True
    db.session.add(admin)
    buyer = User(username="buyer", email="buyer@test.com", company="Global Trade Co", phone="+1-555-0123")
    buyer.set_password("buyer123")
    db.session.add(buyer)
    cats_data = [
        ("electronics", "电子产品", "Electronics"),
        ("machinery", "机械设备", "Machinery"),
        ("textiles", "纺织服装", "Textiles & Apparel"),
        ("home_garden", "家居园艺", "Home & Garden"),
        ("sports", "运动户外", "Sports & Outdoors"),
        ("beauty", "美容个护", "Beauty & Personal Care"),
    ]
    cats = {}
    for slug, name_zh, name_en in cats_data:
        cat = Category(slug=slug, name_zh=name_zh, name_en=name_en, image_url="📦")
        db.session.add(cat)
        cats[slug] = cat
    products_data = [
        ("蓝牙耳机 Pro", "Bluetooth Earphones Pro", "ANC降噪, 30h续航, IPX5防水", "ANC noise cancelling, 30hr battery, IPX5 waterproof", 12.99, "electronics", 500, 100, True),
        ("智能手表 S10", "Smart Watch S10", "AMOLED 1.8寸, 心率血氧监测, IP68", "AMOLED 1.8in, HR & SpO2, IP68 waterproof", 28.50, "electronics", 300, 50, True),
        ("USB-C快充线 2m", "USB-C Fast Charge Cable 2m", "100W PD快充, 尼龙编织", "100W PD fast charge, nylon braided", 3.99, "electronics", 2000, 200, True),
        ("无线充电板 15W", "Wireless Charging Pad 15W", "Qi认证, 超薄设计", "Qi-certified, ultra-slim design", 8.99, "electronics", 800, 100, False),
        ("便携蓝牙音箱", "Portable Bluetooth Speaker", "20W输出, IPX7防水, 12h续航", "20W output, IPX7 waterproof, 12hr battery", 15.99, "electronics", 400, 50, True),
        ("工业热风枪 2000W", "Industrial Heat Gun 2000W", "双温档, 过载保护", "Dual temp, overload protection", 45.00, "machinery", 200, 10, True),
        ("电动螺丝刀 48合1", "Electric Screwdriver 48-in-1", "3.6V锂电, LED照明, 扭矩可调", "3.6V lithium, LED, adjustable torque", 22.99, "machinery", 350, 20, True),
        ("CNC雕刻机 3018", "CNC Engraver 3018 Pro", "工作面积300x180mm", "Working area 300x180mm", 189.00, "machinery", 50, 5, False),
        ("纯棉T恤定制", "Custom Cotton T-Shirt", "100%棉 220g, 支持LOGO定制", "100% cotton 220g, custom LOGO", 4.50, "textiles", 5000, 100, True),
        ("瑜伽运动套装", "Yoga Activewear Set", "高弹面料, 吸湿排汗", "High-stretch, moisture-wicking", 18.99, "textiles", 600, 50, True),
        ("帆布手提袋定制", "Custom Canvas Tote Bag", "12oz帆布, 多色可选", "12oz canvas, multiple colors", 2.99, "textiles", 10000, 500, True),
        ("LED植物生长灯", "LED Grow Light 1000W", "全光谱, 覆盖4x4ft", "Full spectrum, 4x4ft coverage", 79.99, "home_garden", 150, 10, True),
        ("不锈钢保温杯", "Stainless Steel Vacuum Flask", "316不锈钢, 12h保温", "316 stainless, 12hr insulation", 6.50, "home_garden", 3000, 200, True),
        ("硅胶烘焙垫套装", "Silicone Baking Mat Set", "食品级硅胶, 耐温230°C", "Food-grade silicone, 230°C", 5.99, "home_garden", 1500, 100, False),
        ("碳纤维羽毛球拍", "Carbon Fiber Badminton Racket", "全碳素, 重量85g", "Full carbon, weight 85g", 24.99, "sports", 250, 20, True),
        ("折叠露营椅", "Folding Camping Chair", "铝合金, 600D牛津布, 150kg", "Aluminum, 600D Oxford, 150kg", 16.99, "sports", 400, 30, False),
        ("超声波美容仪", "Ultrasonic Facial Device", "5MHz超声波, LED红蓝光", "5MHz ultrasonic, LED therapy", 32.00, "beauty", 300, 20, True),
        ("竹炭洗脸巾100片", "Bamboo Charcoal Face Towel 100pcs", "天然竹纤维, 可降解", "Natural bamboo fiber, biodegradable", 3.50, "beauty", 5000, 300, True),
    ]
    for name_zh, name_en, desc_zh, desc_en, price, cat_slug, stock, moq, featured in products_data:
        db.session.add(Product(
            name_zh=name_zh, name_en=name_en, description_zh=desc_zh, description_en=desc_en,
            price=price, currency="USD", stock=stock, moq=moq, category_id=cats[cat_slug].id,
            is_featured=featured, is_active=True,
            image_url=f"https://placehold.co/600x600/2563eb/ffffff?text={name_en.replace(' ', '+')}"
        ))
    db.session.commit()
    if not MerchantSettings.query.first():
        db.session.add(MerchantSettings(notify_email="1966899806@qq.com"))
        db.session.commit()
    print("Auto-seed complete!")

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        auto_seed()
    app.run(debug=True, port=5000)
