// Authentication functions
const API_URL = '';

// Check if user is logged in
function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/index.html';
        return null;
    }
    return token;
}

// Show message
function showMessage(elementId, message, type) {
    const messageEl = document.getElementById(elementId);
    messageEl.textContent = message;
    messageEl.className = `message ${type}`;
    setTimeout(() => {
        messageEl.className = 'message';
    }, 5000);
}

// Login form
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const telegram_id = document.getElementById('telegram_id').value;
        const password = document.getElementById('password').value;

        try {
            const response = await fetch(`${API_URL}/api/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ telegram_id, password })
            });

            const data = await response.json();

            if (response.ok) {
                localStorage.setItem('token', data.token);
                localStorage.setItem('user', JSON.stringify(data.user));
                window.location.href = '/dashboard.html';
            } else {
                showMessage('message', data.error || 'Login gagal', 'error');
            }
        } catch (error) {
            showMessage('message', 'Terjadi kesalahan. Periksa koneksi Anda.', 'error');
        }
    });
}

// Register form - Step 1
const registerForm = document.getElementById('registerForm');
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const telegram_id = document.getElementById('telegram_id').value;
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        try {
            const response = await fetch(`${API_URL}/api/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ telegram_id, username, password })
            });

            const data = await response.json();

            if (response.ok) {
                // Simpan telegram_id untuk step 2
                localStorage.setItem('pending_telegram_id', telegram_id);
                
                // Tampilkan step 2
                document.getElementById('step1').style.display = 'none';
                document.getElementById('step2').style.display = 'block';
                document.getElementById('displayTelegramId').textContent = telegram_id;
                
                showMessage('message', data.message || 'Kode verifikasi telah dikirim!', 'success');
            } else {
                showMessage('message', data.error || 'Pendaftaran gagal', 'error');
            }
        } catch (error) {
            showMessage('message', 'Terjadi kesalahan. Periksa koneksi Anda.', 'error');
        }
    });
}

// Verify form - Step 2
const verifyForm = document.getElementById('verifyForm');
if (verifyForm) {
    verifyForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const telegram_id = localStorage.getItem('pending_telegram_id');
        const code = document.getElementById('verify_code').value;

        if (!telegram_id) {
            showMessage('message', 'Session expired. Silakan daftar ulang.', 'error');
            return;
        }

        try {
            const response = await fetch(`${API_URL}/api/auth/verify`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ telegram_id, code })
            });

            const data = await response.json();

            if (response.ok) {
                localStorage.removeItem('pending_telegram_id');
                showMessage('message', data.message || 'Verifikasi berhasil! Silakan login.', 'success');
                setTimeout(() => {
                    window.location.href = '/index.html';
                }, 2000);
            } else {
                showMessage('message', data.error || 'Kode verifikasi tidak valid', 'error');
            }
        } catch (error) {
            showMessage('message', 'Terjadi kesalahan. Periksa koneksi Anda.', 'error');
        }
    });
}

// Resend code button
const resendBtn = document.getElementById('resendBtn');
if (resendBtn) {
    resendBtn.addEventListener('click', async () => {
        const telegram_id = localStorage.getItem('pending_telegram_id');
        
        if (!telegram_id) {
            showMessage('message', 'Session expired. Silakan daftar ulang.', 'error');
            return;
        }

        try {
            const response = await fetch(`${API_URL}/api/auth/resend-code`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ telegram_id })
            });

            const data = await response.json();

            if (response.ok) {
                showMessage('message', data.message || 'Kode baru telah dikirim!', 'success');
            } else {
                showMessage('message', data.error || 'Gagal mengirim ulang kode', 'error');
            }
        } catch (error) {
            showMessage('message', 'Terjadi kesalahan. Periksa koneksi Anda.', 'error');
        }
    });
}

// Forgot password form
const forgotForm = document.getElementById('forgotForm');
if (forgotForm) {
    forgotForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const telegram_id = document.getElementById('telegram_id').value;

        try {
            const response = await fetch(`${API_URL}/api/auth/forgot-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ telegram_id })
            });

            const data = await response.json();

            if (response.ok) {
                showMessage('message', 'Kode reset telah dikirim ke Telegram Anda.', 'success');
            } else {
                showMessage('message', data.error || 'Gagal mengirim kode reset', 'error');
            }
        } catch (error) {
            showMessage('message', 'Terjadi kesalahan. Periksa koneksi Anda.', 'error');
        }
    });
}

// Logout function
const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/index.html';
    });
}
