// Main JavaScript file

// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navLinks = document.querySelector('.nav-links');
    
    if (mobileMenuBtn && navLinks) {
        mobileMenuBtn.addEventListener('click', function() {
            navLinks.style.display = navLinks.style.display === 'flex' ? 'none' : 'flex';
            
            if (window.innerWidth <= 768) {
                if (navLinks.style.display === 'flex') {
                    navLinks.style.flexDirection = 'column';
                    navLinks.style.position = 'absolute';
                    navLinks.style.top = '100%';
                    navLinks.style.left = '0';
                    navLinks.style.right = '0';
                    navLinks.style.backgroundColor = 'var(--dark-bg)';
                    navLinks.style.padding = '1rem';
                    navLinks.style.gap = '1rem';
                }
            }
        });
    }
    
    // Auto-hide messages after 5 seconds
    const messages = document.querySelectorAll('.alert');
    messages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            message.style.transition = 'opacity 0.5s';
            setTimeout(() => message.remove(), 500);
        }, 5000);
    });
});

// Crypto ticker simulation
function updateCryptoTicker() {
    const ticker = document.getElementById('crypto-ticker');
    if (!ticker) return;
    
    // Simulated crypto data
    const cryptoData = [
        { symbol: 'BTC', name: 'Bitcoin', price: '$' + (43000 + Math.random() * 1000).toFixed(2), change: (Math.random() * 5 - 2.5).toFixed(2) },
        { symbol: 'ETH', name: 'Ethereum', price: '$' + (2300 + Math.random() * 200).toFixed(2), change: (Math.random() * 5 - 2.5).toFixed(2) },
        { symbol: 'TRX', name: 'TRON', price: '$' + (0.1 + Math.random() * 0.02).toFixed(4), change: (Math.random() * 5 - 2.5).toFixed(2) },
        { symbol: 'USDT', name: 'Tether', price: '$1.00', change: '0.00' }
    ];
    
    ticker.innerHTML = '';
    
    cryptoData.forEach(crypto => {
        const change = parseFloat(crypto.change);
        const changeClass = change >= 0 ? 'positive' : 'negative';
        const changeSymbol = change >= 0 ? '+' : '';
        
        const tickerItem = document.createElement('div');
        tickerItem.className = 'ticker-item';
        tickerItem.innerHTML = `
            <span class="crypto-name">${crypto.symbol}</span>
            <span class="crypto-price">${crypto.price}</span>
            <span class="price-change ${changeClass}">
                ${changeSymbol}${crypto.change}%
            </span>
        `;
        ticker.appendChild(tickerItem);
    });
}

// Update ticker on page load and every 30 seconds
if (document.getElementById('crypto-ticker')) {
    updateCryptoTicker();
    setInterval(updateCryptoTicker, 30000);
}

// Form validation helpers
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    return password.length >= 8;
}

// Copy to clipboard function
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert('Copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
}