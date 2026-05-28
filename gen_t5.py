import os
BASE = r"C:\Users\19668\Documents\Codex\2026-05-28\new-chat\tradehub\templates"
def w(rel, content):
    path = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  OK: {rel}")

# === cart/cart.html ===
w("cart/cart.html", """{% extends "base.html" %}
{% block title %}{{ '购物车' if lang == 'zh' else 'Shopping Cart' }}{% endblock %}
{% block content %}
<div class="container py-4">
    <h2 class="fw-bold mb-4">{{ '购物车' if lang == 'zh' else 'Shopping Cart' }}</h2>
    {% if items %}
    <div class="table-responsive"><table class="table align-middle">
        <thead class="table-light"><tr>
            <th>{{ '产品' if lang == 'zh' else 'Product' }}</th>
            <th>{{ '单价' if lang == 'zh' else 'Unit Price' }}</th>
            <th>{{ '数量' if lang == 'zh' else 'Quantity' }}</th>
            <th>{{ '小计' if lang == 'zh' else 'Subtotal' }}</th>
            <th></th>
        </tr></thead>
        <tbody>
            {% for item in items %}
            <tr id="cart-row-{{ item.id }}">
                <td><div class="d-flex align-items-center gap-3">
                    <img src="{{ item.product.image_url or 'https://placehold.co/80x80/e2e8f0/64748b?text=P' }}" width="60" class="rounded" alt="">
                    <div><h6 class="mb-0">{{ item.product.name_zh if lang == 'zh' else item.product.name_en }}</h6><small class="text-muted">MOQ: {{ item.product.moq }}</small></div>
                </div></td>
                <td>${{ "%.2f"|format(item.product.price) }}</td>
                <td><input type="number" class="form-control cart-qty w-auto" style="width:80px" value="{{ item.quantity }}" min="1" data-id="{{ item.id }}" data-price="{{ item.product.price }}"></td>
                <td class="fw-bold text-primary" id="subtotal-{{ item.id }}">${{ "%.2f"|format(item.product.price * item.quantity) }}</td>
                <td>
                    <form action="{{ url_for("cart_remove", item_id=item.id) }}" method="POST" class="d-inline">
                        <button class="btn btn-sm btn-outline-danger"><i class="bi bi-trash"></i></button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table></div>
    <div class="d-flex justify-content-between align-items-center border-top pt-3">
        <h4 class="fw-bold">{{ '合计' if lang == 'zh' else 'Total' }}: <span class="text-primary" id="cart-total">${{ "%.2f"|format(total) }}</span></h4>
        <a href="{{ url_for("checkout") }}" class="btn btn-success btn-lg"><i class="bi bi-credit-card"></i> {{ '去结算' if lang == 'zh' else 'Checkout' }}</a>
    </div>
    {% else %}
    <div class="text-center py-5"><i class="bi bi-cart-x display-1 text-muted"></i><h4 class="text-muted mt-3">{{ '购物车是空的' if lang == 'zh' else 'Your cart is empty' }}</h4><a href="{{ url_for("products") }}" class="btn btn-primary mt-3">{{ '去购物' if lang == 'zh' else 'Shop Now' }}</a></div>
    {% endif %}
</div>
{% endblock %}
{% block extra_scripts %}
<script>
document.querySelectorAll(".cart-qty").forEach(input => {
    input.addEventListener("change", async function() {
        const id = this.dataset.id;
        const qty = parseInt(this.value) || 1;
        const res = await fetch("/cart/update/" + id, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({quantity: qty})
        });
        const data = await res.json();
        if (data.success) {
            document.getElementById("subtotal-" + id).textContent = "$" + data.subtotal;
            document.getElementById("cart-total").textContent = "$" + data.total;
        }
    });
});
</script>
{% endblock %}
""")

# === orders/checkout.html ===
w("orders/checkout.html", """{% extends "base.html" %}
{% block title %}{{ '结算' if lang == 'zh' else 'Checkout' }}{% endblock %}
{% block content %}
<div class="container py-4">
    <h2 class="fw-bold mb-4">{{ '结算' if lang == 'zh' else 'Checkout' }}</h2>
    <div class="row g-4">
        <div class="col-md-8">
            <div class="card shadow-sm"><div class="card-body p-4">
                <h5 class="fw-bold mb-3">{{ '收货信息' if lang == 'zh' else 'Shipping Information' }}</h5>
                <form method="POST">
                    <div class="row g-3">
                        <div class="col-md-6"><label class="form-label">{{ '联系人' if lang == 'zh' else 'Contact Name' }}</label><input type="text" name="contact_name" class="form-control" value="{{ current_user.username }}" required></div>
                        <div class="col-md-6"><label class="form-label">{{ '邮箱' if lang == 'zh' else 'Email' }}</label><input type="email" name="contact_email" class="form-control" value="{{ current_user.email }}" required></div>
                        <div class="col-md-6"><label class="form-label">{{ '电话' if lang == 'zh' else 'Phone' }}</label><input type="text" name="contact_phone" class="form-control" value="{{ current_user.phone or '' }}"></div>
                        <div class="col-12"><label class="form-label">{{ '收货地址' if lang == 'zh' else 'Shipping Address' }}</label><textarea name="shipping_address" class="form-control" rows="3" required placeholder="{{ '请填写详细地址...' if lang == 'zh' else 'Enter full shipping address...' }}"></textarea></div>
                        <div class="col-12"><label class="form-label">{{ '备注' if lang == 'zh' else 'Notes' }}</label><textarea name="notes" class="form-control" rows="2" placeholder="{{ '选填' if lang == 'zh' else 'Optional' }}"></textarea></div>
                    </div>
                    <hr>
                    <button type="submit" class="btn btn-success btn-lg w-100"><i class="bi bi-check-circle"></i> {{ '提交订单' if lang == 'zh' else 'Place Order' }}</button>
                </form>
            </div></div>
        </div>
        <div class="col-md-4">
            <div class="card shadow-sm"><div class="card-body">
                <h5 class="fw-bold mb-3">{{ '订单摘要' if lang == 'zh' else 'Order Summary' }}</h5>
                {% for item in items %}
                <div class="d-flex justify-content-between mb-2"><span>{{ item.product.name_zh if lang == 'zh' else item.product.name_en }} x {{ item.quantity }}</span><span>${{ "%.2f"|format(item.product.price * item.quantity) }}</span></div>
                {% endfor %}
                <hr>
                <div class="d-flex justify-content-between fw-bold fs-5"><span>{{ '合计' if lang == 'zh' else 'Total' }}</span><span class="text-primary">${{ "%.2f"|format(total) }}</span></div>
                <small class="text-muted">{{ '支付方式: T/T, L/C, PayPal 等' if lang == 'zh' else 'Payment: T/T, L/C, PayPal, etc.' }}</small>
            </div></div>
        </div>
    </div>
</div>
{% endblock %}
""")

# === orders/list.html ===
w("orders/list.html", """{% extends "base.html" %}
{% block title %}{{ '我的订单' if lang == 'zh' else 'My Orders' }}{% endblock %}
{% block content %}
<div class="container py-4">
    <h2 class="fw-bold mb-4">{{ '我的订单' if lang == 'zh' else 'My Orders' }}</h2>
    {% if orders %}
    <div class="table-responsive"><table class="table table-hover align-middle">
        <thead class="table-light"><tr><th>#</th><th>{{ '日期' if lang == 'zh' else 'Date' }}</th><th>{{ '金额' if lang == 'zh' else 'Amount' }}</th><th>{{ '状态' if lang == 'zh' else 'Status' }}</th><th></th></tr></thead>
        <tbody>
            {% for order in orders %}
            <tr>
                <td><strong>#{{ order.id }}</strong></td>
                <td>{{ order.created_at.strftime("%Y-%m-%d %H:%M") }}</td>
                <td class="fw-bold">${{ "%.2f"|format(order.total_amount) }}</td>
                <td>
                    {% set status_map = {"pending": ("待确认", "Pending"), "confirmed": ("已确认", "Confirmed"), "shipped": ("已发货", "Shipped"), "delivered": ("已送达", "Delivered"), "cancelled": ("已取消", "Cancelled")} %}
                    {% set s = status_map.get(order.status, (order.status, order.status)) %}
                    {% set badge_class = {"pending": "warning", "confirmed": "info", "shipped": "primary", "delivered": "success", "cancelled": "secondary"} %}
                    <span class="badge bg-{{ badge_class.get(order.status, 'secondary') }}">{{ s[0] if lang == 'zh' else s[1] }}</span>
                </td>
                <td><a href="{{ url_for("order_detail", order_id=order.id) }}" class="btn btn-sm btn-outline-primary">{{ '详情' if lang == 'zh' else 'Details' }}</a></td>
            </tr>
            {% endfor %}
        </tbody>
    </table></div>
    {% else %}
    <div class="text-center py-5"><i class="bi bi-inbox display-1 text-muted"></i><h4 class="text-muted mt-3">{{ '暂无订单' if lang == 'zh' else 'No orders yet' }}</h4><a href="{{ url_for("products") }}" class="btn btn-primary mt-3">{{ '去购物' if lang == 'zh' else 'Shop Now' }}</a></div>
    {% endif %}
</div>
{% endblock %}
""")

# === orders/detail.html ===
w("orders/detail.html", """{% extends "base.html" %}
{% block title %}{{ '订单详情' if lang == 'zh' else 'Order Detail' }} #{{ order.id }}{% endblock %}
{% block content %}
<div class="container py-4">
    <nav aria-label="breadcrumb"><ol class="breadcrumb"><li class="breadcrumb-item"><a href="{{ url_for("orders") }}">{{ '我的订单' if lang == 'zh' else 'My Orders' }}</a></li><li class="breadcrumb-item active">#{{ order.id }}</li></ol></nav>
    <div class="row g-4">
        <div class="col-md-8">
            <div class="card shadow-sm mb-3"><div class="card-body">
                <h5 class="fw-bold">{{ '订单商品' if lang == 'zh' else 'Order Items' }}</h5>
                {% for item in order.items %}
                <div class="d-flex align-items-center gap-3 py-2 border-bottom">
                    <img src="{{ item.product.image_url or 'https://placehold.co/60x60/e2e8f0/64748b?text=P' }}" width="50" class="rounded" alt="">
                    <div class="flex-grow-1"><strong>{{ item.product.name_zh if lang == 'zh' else item.product.name_en }}</strong><br><small class="text-muted">Qty: {{ item.quantity }} x ${{ "%.2f"|format(item.price) }}</small></div>
                    <strong>${{ "%.2f"|format(item.price * item.quantity) }}</strong>
                </div>
                {% endfor %}
                <div class="d-flex justify-content-between mt-3 fw-bold fs-5"><span>{{ '合计' if lang == 'zh' else 'Total' }}</span><span class="text-primary">${{ "%.2f"|format(order.total_amount) }}</span></div>
            </div></div>
        </div>
        <div class="col-md-4">
            <div class="card shadow-sm mb-3"><div class="card-body">
                <h5 class="fw-bold">{{ '订单信息' if lang == 'zh' else 'Order Info' }}</h5>
                <p><strong>{{ '状态' if lang == 'zh' else 'Status' }}:</strong> <span class="badge bg-{{ "success" if order.status == "delivered" else "warning" if order.status == "pending" else "info" }}">{{ order.status }}</span></p>
                <p><strong>{{ '日期' if lang == 'zh' else 'Date' }}:</strong> {{ order.created_at.strftime("%Y-%m-%d %H:%M") }}</p>
            </div></div>
            <div class="card shadow-sm"><div class="card-body">
                <h5 class="fw-bold">{{ '收货信息' if lang == 'zh' else 'Shipping Info' }}</h5>
                <p><strong>{{ '联系人' if lang == 'zh' else 'Contact' }}:</strong> {{ order.contact_name }}</p>
                <p><strong>Email:</strong> {{ order.contact_email }}</p>
                {% if order.contact_phone %}<p><strong>{{ '电话' if lang == 'zh' else 'Phone' }}:</strong> {{ order.contact_phone }}</p>{% endif %}
                <p><strong>{{ '地址' if lang == 'zh' else 'Address' }}:</strong> {{ order.shipping_address }}</p>
                {% if order.notes %}<p><strong>{{ '备注' if lang == 'zh' else 'Notes' }}:</strong> {{ order.notes }}</p>{% endif %}
            </div></div>
        </div>
    </div>
</div>
{% endblock %}
""")

print("Cart + Orders done")
