import os
BASE = r"C:\Users\19668\Documents\Codex\2026-05-28\new-chat\tradehub\templates"
def w(rel, content):
    path = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  OK: {rel}")

# === chat/chat.html ===
w("chat/chat.html", """{% extends "base.html" %}
{% block title %}🦞 {{ '龙虾助手' if lang == 'zh' else 'LobsterBot AI' }}{% endblock %}
{% block content %}
<div class="container py-4">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card shadow">
                <div class="card-header bg-primary text-white d-flex align-items-center gap-2">
                    <span class="fs-3">🦞</span>
                    <div><h5 class="mb-0">{{ '龙虾助手 - AI 智能客服' if lang == 'zh' else 'LobsterBot - AI Assistant' }}</h5><small>{{ '随时为您解答外贸问题' if lang == 'zh' else 'Here to help with your trade questions' }}</small></div>
                </div>
                <div class="card-body" style="height: 450px; overflow-y: auto;" id="chat-messages">
                    <div class="d-flex mb-3">
                        <div class="bg-light rounded-3 p-3" style="max-width:80%">
                            <p class="mb-0">{{ '您好！我是龙虾助手 🦞，您的智能外贸客服。我可以帮您：' if lang == 'zh' else 'Hello! I am LobsterBot 🦞, your AI trade assistant. I can help with:' }}</p>
                            <ul class="mb-0 mt-2 small">
                                <li>{{ '产品信息和推荐' if lang == 'zh' else 'Product info & recommendations' }}</li>
                                <li>{{ '价格和起订量咨询' if lang == 'zh' else 'Pricing & MOQ inquiries' }}</li>
                                <li>{{ '物流和运输方案' if lang == 'zh' else 'Shipping & logistics' }}</li>
                                <li>{{ '支付方式说明' if lang == 'zh' else 'Payment methods' }}</li>
                                <li>{{ '公司介绍和联系方式' if lang == 'zh' else 'Company info & contact' }}</li>
                            </ul>
                            <p class="mb-0 mt-2">{{ '请问有什么可以帮您的？' if lang == 'zh' else 'What can I help you with?' }}</p>
                        </div>
                    </div>
                </div>
                <div class="card-footer">
                    <div class="input-group">
                        <input type="text" id="chat-input" class="form-control" placeholder="{{ '输入您的问题...' if lang == 'zh' else 'Type your question...' }}" onkeypress="if(event.key==='Enter')sendMessage()">
                        <button class="btn btn-primary" onclick="sendMessage()"><i class="bi bi-send"></i> {{ '发送' if lang == 'zh' else 'Send' }}</button>
                    </div>
                    <div class="mt-2 d-flex gap-1 flex-wrap">
                        <button class="btn btn-sm btn-outline-secondary" onclick="quickAsk('products')">{{ '产品' if lang == 'zh' else 'Products' }}</button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="quickAsk('price')">{{ '价格' if lang == 'zh' else 'Pricing' }}</button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="quickAsk('shipping')">{{ '物流' if lang == 'zh' else 'Shipping' }}</button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="quickAsk('payment')">{{ '支付' if lang == 'zh' else 'Payment' }}</button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="quickAsk('contact')">{{ '联系' if lang == 'zh' else 'Contact' }}</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
{% block extra_scripts %}
<script>
const chatBox = document.getElementById("chat-messages");
const input = document.getElementById("chat-input");

function addMessage(text, isUser) {
    const div = document.createElement("div");
    div.className = "d-flex mb-3 " + (isUser ? "justify-content-end" : "");
    div.innerHTML = '<div class="rounded-3 p-3" style="max-width:80%;background:' + (isUser ? "#667eea;color:white" : "#f1f5f9") + '"><p class="mb-0" style="white-space:pre-wrap">' + text + "</p></div>";
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
    const msg = input.value.trim();
    if (!msg) return;
    addMessage(msg, true);
    input.value = "";
    const loading = document.createElement("div");
    loading.className = "d-flex mb-3";
    loading.innerHTML = '<div class="bg-light rounded-3 p-3"><div class="spinner-grow spinner-grow-sm text-primary"></div></div>';
    chatBox.appendChild(loading);
    chatBox.scrollTop = chatBox.scrollHeight;
    try {
        const res = await fetch("/api/chat", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:msg})});
        const data = await res.json();
        loading.remove();
        addMessage(data.reply, false);
    } catch(e) {
        loading.remove();
        addMessage("Sorry, something went wrong. Please try again.", false);
    }
}

function quickAsk(topic) {
    const qs = {products:"{{ '你们有什么产品？' if lang == 'zh' else 'What products do you sell?' }}",price:"{{ '价格和起订量是多少？' if lang == 'zh' else 'What are your prices and MOQ?' }}",shipping:"{{ '如何发货和运输？' if lang == 'zh' else 'How do you ship and deliver?' }}",payment:"{{ '支持哪些支付方式？' if lang == 'zh' else 'What payment methods do you accept?' }}",contact:"{{ '联系方式是什么？' if lang == 'zh' else 'How can I contact you?' }}"};
    input.value = qs[topic];
    sendMessage();
}
</script>
{% endblock %}
""")

print("Chat done")
