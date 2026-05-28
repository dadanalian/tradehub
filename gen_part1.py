import os

BASE = r"C:\Users\19668\Documents\Codex\2026-05-28\new-chat\tradehub\templates"

def write_file(relpath, content):
    path = os.path.join(BASE, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  Created: {relpath}")

# Index template
write_file("index.html", '''{% extends "base.html" %}
{% block title %}{{ '首页' if lang == 'zh' else 'Home' }}{% endblock %}
{% block content %}

<section class="hero-banner text-white text-center d-flex align-items-center justify-content-center">
    <div class="container">
        <h1 class="display-3 fw-bold mb-3">
            {% if lang == 'zh' %}全球贸易，从这里开始{% else %}Global Trade Starts Here{% endif %}
        </h1>
        <p class="lead mb-4">
            {% if lang == 'zh' %}连接全球买家与优质中国供应商 · 安全 · 高效 · 可靠{% else %}Connecting global buyers with quality Chinese suppliers · Safe · Efficient · Reliable{% endif %}
        </p>
        <div class="d-flex justify-content-center gap-3">
            <a href="{{ url_for("products") }}" class="btn btn-primary btn-lg px-4">
                {% if lang == 'zh' %}浏览产品{% else %}Browse Products{% endif %}
            </a>
            <a href="{{ url_for("chat") }}" class="btn btn-outline-light btn-lg px-4">
                🦞 {% if lang == 'zh' %}龙虾助手{% else %}LobsterBot AI{% endif %}
            </a>
        </div>
    </div>
</section>

<section class="py-5 bg-light">
    <div class="container">
        <div class="row g-4 text-center">
            <div class="col-md-3"><div class="p-4 bg-white rounded-3 shadow-sm h-100">
                <i class="bi bi-shield-check display-4 text-primary"></i>
                <h5 class="mt-3">{{ '品质保证' if lang == 'zh' else 'Quality Verified' }}</h5>
                <p class="text-secondary small">{{ '所有供应商经过严格审核' if lang == 'zh' else 'All suppliers strictly vetted' }}</p>
            </div></div>
            <div class="col-md-3"><div class="p-4 bg-white rounded-3 shadow-sm h-100">
                <i class="bi bi-truck display-4 text-success"></i>
                <h5 class="mt-3">{{ '全球物流' if lang == 'zh' else 'Global Shipping' }}</h5>
                <p class="text-secondary small">{{ '海运·空运·快递全覆盖' if lang == 'zh' else 'Sea·Air·Express worldwide' }}</p>
            </div></div>
            <div class="col-md-3"><div class="p-4 bg-white rounded-3 shadow-sm h-100">
                <i class="bi bi-currency-exchange display-4 text-warning"></i>
                <h5 class="mt-3">{{ '安全支付' if lang == 'zh' else 'Secure Payment' }}</h5>
                <p class="text-secondary small">{{ '多种支付方式保障交易' if lang == 'zh' else 'Multiple secure payment options' }}</p>
            </div></div>
            <div class="col-md-3"><div class="p-4 bg-white rounded-3 shadow-sm h-100">
                <i class="bi bi-headset display-4 text-info"></i>
                <h5 class="mt-3">{{ '专属客服' if lang == 'zh' else 'Dedicated Support' }}</h5>
                <p class="text-secondary small">{{ '7x24小时多语言服务' if lang == 'zh' else '24/7 multilingual support' }}</p>
            </div></div>
        </div>
    </div>
</section>
''')
print("part 1 done")
