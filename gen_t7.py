import os
BASE = r"C:\Users\19668\Documents\Codex\2026-05-28\new-chat\tradehub\templates"
def w(rel, content):
    path = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  OK: {rel}")

# === admin/dashboard.html ===
w("admin/dashboard.html", """{% extends "base.html" %}
{% block title %}Admin Dashboard{% endblock %}
{% block content %}
<div class="container py-4">
    <h2 class="fw-bold mb-4">🛠️ Admin Dashboard</h2>
    <div class="row g-3 mb-4">
        <div class="col-md-3"><div class="card bg-primary text-white"><div class="card-body text-center"><h3>{{ stats.products }}</h3><small>Products</small></div></div></div>
        <div class="col-md-3"><div class="card bg-success text-white"><div class="card-body text-center"><h3>{{ stats.orders }}</h3><small>Orders</small></div></div></div>
        <div class="col-md-3"><div class="card bg-info text-white"><div class="card-body text-center"><h3>{{ stats.users }}</h3><small>Users</small></div></div></div>
        <div class="col-md-3"><div class="card bg-warning text-dark"><div class="card-body text-center"><h3>{{ stats.inquiries }}</h3><small>New Inquiries</small></div></div></div>
    </div>
    <div class="row g-4">
        <div class="col-md-6"><div class="card shadow-sm"><div class="card-header fw-bold">Recent Orders</div><div class="card-body">
            {% for o in stats.recent_orders %}<div class="d-flex justify-content-between py-2 border-bottom"><span>#{{ o.id }} - {{ o.contact_name }}</span><span>${{ "%.2f"|format(o.total_amount) }}</span><span class="badge bg-{{ "success" if o.status=="delivered" else "warning" }}">{{ o.status }}</span></div>{% endfor %}
            <a href="{{ url_for("admin_orders") }}" class="btn btn-sm btn-outline-primary mt-3">View All Orders</a>
        </div></div></div>
        <div class="col-md-6"><div class="card shadow-sm"><div class="card-header fw-bold">New Inquiries</div><div class="card-body">
            {% for i in stats.recent_inquiries %}<div class="py-2 border-bottom"><strong>{{ i.name }}</strong> ({{ i.email }}){% if i.product %}<br><small>Re: {{ i.product.name_en }}</small>{% endif %}<br><small class="text-muted">{{ i.message[:100] }}...</small></div>{% endfor %}
            <a href="{{ url_for("admin_inquiries") }}" class="btn btn-sm btn-outline-primary mt-3">View All Inquiries</a>
        </div></div></div>
    </div>
    <div class="mt-4 d-flex gap-2">
        <a href="{{ url_for("admin_products") }}" class="btn btn-outline-primary">Manage Products</a>
        <a href="{{ url_for("admin_orders") }}" class="btn btn-outline-success">Manage Orders</a>
        <a href="{{ url_for("admin_inquiries") }}" class="btn btn-outline-warning">View Inquiries</a>
    </div>
</div>
{% endblock %}
""")

# === admin/products.html ===
w("admin/products.html", """{% extends "base.html" %}
{% block title %}Admin - Products{% endblock %}
{% block content %}
<div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-3"><h2 class="fw-bold">Manage Products</h2><a href="{{ url_for("admin_product_add") }}" class="btn btn-primary"><i class="bi bi-plus-lg"></i> Add Product</a></div>
    <div class="table-responsive"><table class="table table-hover align-middle">
        <thead class="table-light"><tr><th>ID</th><th>Image</th><th>Name</th><th>Price</th><th>Stock</th><th>Featured</th><th>Active</th><th></th></tr></thead>
        <tbody>
            {% for p in products %}
            <tr>
                <td>{{ p.id }}</td>
                <td><img src="{{ p.image_url or 'https://placehold.co/40x40/e2e8f0/64748b?text=P' }}" width="40" class="rounded"></td>
                <td>{{ p.name_en }}</td>
                <td>${{ "%.2f"|format(p.price) }}</td>
                <td>{{ p.stock }}</td>
                <td>{{ 'Yes' if p.is_featured else 'No' }}</td>
                <td>{{ 'Yes' if p.is_active else 'No' }}</td>
                <td><a href="{{ url_for("admin_product_edit", product_id=p.id) }}" class="btn btn-sm btn-outline-primary">Edit</a></td>
            </tr>
            {% endfor %}
        </tbody>
    </table></div>
</div>
{% endblock %}
""")

# === admin/product_form.html ===
w("admin/product_form.html", """{% extends "base.html" %}
{% block title %}{{ 'Edit' if product else 'Add' }} Product{% endblock %}
{% block content %}
<div class="container py-4">
    <h2 class="fw-bold mb-4">{{ 'Edit Product' if product else 'Add Product' }}</h2>
    <div class="card shadow-sm"><div class="card-body p-4">
        <form method="POST">
            <div class="row g-3">
                <div class="col-md-6"><label class="form-label">Name (Chinese)</label><input type="text" name="name_zh" class="form-control" value="{{ product.name_zh if product else '' }}" required></div>
                <div class="col-md-6"><label class="form-label">Name (English)</label><input type="text" name="name_en" class="form-control" value="{{ product.name_en if product else '' }}" required></div>
                <div class="col-md-4"><label class="form-label">Price (USD)</label><input type="number" step="0.01" name="price" class="form-control" value="{{ product.price if product else '' }}" required></div>
                <div class="col-md-4"><label class="form-label">Stock</label><input type="number" name="stock" class="form-control" value="{{ product.stock if product else 0 }}" required></div>
                <div class="col-md-4"><label class="form-label">MOQ</label><input type="number" name="moq" class="form-control" value="{{ product.moq if product else 1 }}" required></div>
                <div class="col-md-6"><label class="form-label">Category</label><select name="category_id" class="form-select">{% for c in categories %}<option value="{{ c.id }}" {{ "selected" if product and product.category_id == c.id }}>{{ c.name_en }}</option>{% endfor %}</select></div>
                <div class="col-md-6"><label class="form-label">Image URL</label><input type="text" name="image_url" class="form-control" value="{{ product.image_url if product else '' }}"></div>
                <div class="col-12"><label class="form-label">Description (Chinese)</label><textarea name="description_zh" class="form-control" rows="3">{{ product.description_zh if product else '' }}</textarea></div>
                <div class="col-12"><label class="form-label">Description (English)</label><textarea name="description_en" class="form-control" rows="3">{{ product.description_en if product else '' }}</textarea></div>
                <div class="col-12">
                    <div class="form-check form-check-inline"><input class="form-check-input" type="checkbox" name="is_featured" {{ "checked" if product and product.is_featured }}><label class="form-check-label">Featured</label></div>
                    <div class="form-check form-check-inline"><input class="form-check-input" type="checkbox" name="is_active" {{ "checked" if not product or product.is_active }}><label class="form-check-label">Active</label></div>
                </div>
                <div class="col-12"><button type="submit" class="btn btn-primary btn-lg">Save</button></div>
            </div>
        </form>
    </div></div>
</div>
{% endblock %}
""")

# === admin/orders.html ===
w("admin/orders.html", """{% extends "base.html" %}
{% block title %}Admin - Orders{% endblock %}
{% block content %}
<div class="container py-4"><h2 class="fw-bold mb-4">Manage Orders</h2>
<div class="table-responsive"><table class="table table-hover align-middle">
    <thead class="table-light"><tr><th>#</th><th>Customer</th><th>Email</th><th>Amount</th><th>Status</th><th>Date</th><th>Action</th></tr></thead>
    <tbody>
        {% for o in orders %}
        <tr>
            <td><strong>#{{ o.id }}</strong></td><td>{{ o.contact_name }}</td><td>{{ o.contact_email }}</td>
            <td>${{ "%.2f"|format(o.total_amount) }}</td>
            <td><span class="badge bg-{{ "success" if o.status=="delivered" else "warning" if o.status=="pending" else "info" }}">{{ o.status }}</span></td>
            <td>{{ o.created_at.strftime("%Y-%m-%d") }}</td>
            <td>
                <form action="{{ url_for("admin_order_status", order_id=o.id) }}" method="POST" class="d-flex gap-1">
                    <select name="status" class="form-select form-select-sm w-auto">
                        <option value="pending" {{ "selected" if o.status=="pending" }}>Pending</option>
                        <option value="confirmed" {{ "selected" if o.status=="confirmed" }}>Confirmed</option>
                        <option value="shipped" {{ "selected" if o.status=="shipped" }}>Shipped</option>
                        <option value="delivered" {{ "selected" if o.status=="delivered" }}>Delivered</option>
                        <option value="cancelled" {{ "selected" if o.status=="cancelled" }}>Cancelled</option>
                    </select>
                    <button class="btn btn-sm btn-primary">Update</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table></div></div>
{% endblock %}
""")

# === admin/inquiries.html ===
w("admin/inquiries.html", """{% extends "base.html" %}
{% block title %}Admin - Inquiries{% endblock %}
{% block content %}
<div class="container py-4"><h2 class="fw-bold mb-4">Customer Inquiries</h2>
<div class="table-responsive"><table class="table table-hover align-middle">
    <thead class="table-light"><tr><th>#</th><th>Name</th><th>Email</th><th>Company</th><th>Product</th><th>Message</th><th>Status</th><th>Date</th><th></th></tr></thead>
    <tbody>
        {% for i in inquiries %}
        <tr class="{{ 'table-warning' if not i.is_read }}">
            <td>{{ i.id }}</td><td>{{ i.name }}</td><td>{{ i.email }}</td><td>{{ i.company or '-' }}</td>
            <td>{{ i.product.name_en if i.product else '-' }}</td>
            <td><small>{{ i.message[:80] }}...</small></td>
            <td><span class="badge bg-{{ 'success' if i.is_read else 'warning' }}">{{ 'Read' if i.is_read else 'New' }}</span></td>
            <td>{{ i.created_at.strftime("%m-%d %H:%M") }}</td>
            <td>
                {% if not i.is_read %}
                <form action="{{ url_for("admin_inquiry_read", inquiry_id=i.id) }}" method="POST"><button class="btn btn-sm btn-outline-success">Mark Read</button></form>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table></div></div>
{% endblock %}
""")

print("Admin templates done")
