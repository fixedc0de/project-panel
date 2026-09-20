// Forgot Password functions
const API_URL = '';

let forgotTelegramId = null;

// Step 1: Request reset code
const forgotForm = document.getElementById('forgotForm');
if (forgotForm) {
    forgotForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const telegram_id = document.getElementById('telegram_id').value;

        try {
            const response = await fetch(`${API_URL}/api/auth/forgot-password-request`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ telegram_id })
            });

            const data = await response.json();

            if (response.ok) {
                forgotTelegramId = telegram_id;
                localStorage.setItem('forgot_telegram_id', telegram_id);
                
                // Show step 2
                document.getElementById('step1').style.display = 'none';
                document.getElementById('step2').style.display = 'block';
                
                showMessage('message', data.message || 'Kode verifikasi telah dikirim ke Telegram Anda!', 'success');
            } else {
                showMessage('message', data.error || 'Gagal mengirim kode reset', 'error');
            }
        } catch (error) {
            showMessage('message', 'Terjadi kesalahan. Periksa koneksi Anda.', 'error');
        }
    });
}

// Step 2: Verify code
const verifyCodeForm = document.getElementById('verifyCodeForm');
if (verifyCodeForm) {
    verifyCodeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const telegram_id = localStorage.getItem('forgot_telegram_id');
        const code = document.getElementById('reset_code').value;

        if (!telegram_id) {
            showMessage('message', 'Session expired. Silakan ulangi dari awal.', 'error');
            return;
        }

        try {
            const response = await fetch(`${API_URL}/api/auth/forgot-password-verify`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ telegram_id, code })
            });

            const data = await response.json();

            if (response.ok) {
                // Show step 3
                document.getElementById('step2').style.display = 'none';
                document.getElementById('step3').style.display = 'block';
                
                showMessage('message', 'Kode valid! Silakan masukkan password baru.', 'success');
            } else {
                showMessage('message', data.error || 'Kode verifikasi tidak valid', 'error');
            }
        } catch (error) {
            showMessage('message', 'Terjadi kesalahan. Periksa koneksi Anda.', 'error');
        }
    });
}

// Step 3: Reset password
const resetPasswordForm = document.getElementById('resetPasswordForm');
if (resetPasswordForm) {
    resetPasswordForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const telegram_id = localStorage.getItem('forgot_telegram_id');
        const new_password = document.getElementById('new_password').value;
        const confirm_password = document.getElementById('confirm_password').value;

        if (!telegram_id) {
            showMessage('message', 'Session expired. Silakan ulangi dari awal.', 'error');
            return;
        }

        if (new_password.length < 6) {
            showMessage('message', 'Password minimal 6 karakter', 'error');
            return;
        }

        if (new_password !== confirm_password) {
            showMessage('message', 'Konfirmasi password tidak cocok', 'error');
            return;
        }

        try {
            const response = await fetch(`${API_URL}/api/auth/forgot-password-reset`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ telegram_id, new_password })
            });

            const data = await response.json();

            if (response.ok) {
                localStorage.removeItem('forgot_telegram_id');
                showMessage('message', data.message || 'Password berhasil diubah! Silakan login.', 'success');
                setTimeout(() => {
                    window.location.href = '/index.html';
                }, 2000);
            } else {
                showMessage('message', data.error || 'Gagal mengubah password', 'error');
            }
        } catch (error) {
            showMessage('message', 'Terjadi kesalahan. Periksa koneksi Anda.', 'error');
        }
    });
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
