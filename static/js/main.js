// TradeHub Main Script

// Update cart badge count on page load
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        document.querySelectorAll('.alert').forEach(function(el) {
            var bsAlert = new bootstrap.Alert(el);
            bsAlert.close();
        });
    }, 5000);
    
    // Update cart count from server
    updateCartCount();
});

function updateCartCount() {
    fetch('/cart/count')
        .then(res => res.json())
        .then(data => {
            const badge = document.getElementById('cart-count');
            if (badge) badge.textContent = data.count || 0;
        })
        .catch(() => {});
}
