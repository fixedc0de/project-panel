// Dashboard functions
const API_URL = '';

// Check authentication on load
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    const user = JSON.parse(localStorage.getItem('user') || 'null');

    if (!token) {
        window.location.href = '/index.html';
        return;
    }

    // Display user email
    if (user && user.email) {
        document.getElementById('userEmail').textContent = user.email;
    }

    // Load dashboard data
    loadDashboard();
});

// Load dashboard data
async function loadDashboard() {
    const token = localStorage.getItem('token');

    try {
        const response = await fetch(`/api/bots`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const bots = await response.json();
            renderBots(bots);
            updateStats(bots);
        } else if (response.status === 401) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/index.html';
        } else {
            const errorData = await response.json();
            console.error('Failed to load bots:', errorData);
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Render bots list
function renderBots(bots) {
    const botsList = document.getElementById('botsList');
    
    if (!bots || bots.length === 0) {
        botsList.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #666;">Belum ada bot. Klik "Tambah Bot" untuk membuat bot pertama Anda.</p>';
        return;
    }

    botsList.innerHTML = bots.map(bot => `
        <div class="bot-card">
            <div class="bot-card-header">
                <h3>${escapeHtml(bot.name)}</h3>
                <span class="bot-status ${bot.is_active ? 'status-active' : 'status-inactive'}">
                    ${bot.is_active ? 'Aktif' : 'Nonaktif'}
                </span>
            </div>
            <p><strong>Template:</strong> ${escapeHtml(bot.template || 'Custom')}</p>
            <p><strong>Deskripsi:</strong> ${escapeHtml(bot.description || 'Tidak ada deskripsi')}</p>
            <p><small>Dibuat: ${new Date(bot.created_at).toLocaleDateString('id-ID')}</small></p>
            <div class="bot-card-actions">
                <button class="btn btn-primary btn-sm" onclick="toggleBot(${bot.id}, ${!bot.is_active})">
                    ${bot.is_active ? 'Stop' : 'Start'}
                </button>
                <button class="btn btn-secondary btn-sm" onclick="editBot(${bot.id})">Edit</button>
                <button class="btn btn-secondary btn-sm" style="background: #dc3545;" onclick="deleteBot(${bot.id})">Hapus</button>
            </div>
        </div>
    `).join('');
}

// Update stats
function updateStats(bots) {
    document.getElementById('totalBots').textContent = bots.length;
    document.getElementById('activeBots').textContent = bots.filter(b => b.is_active).length;
    document.getElementById('totalUsers').textContent = '1'; // Could be enhanced later
}

// Toggle bot status
async function toggleBot(botId, isActive) {
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`/api/bots/${botId}/toggle`, {
            method: 'POST',
            headers: { 
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ is_active: isActive })
        });

        if (response.ok) {
            loadDashboard();
        } else {
            const data = await response.json();
            alert(data.error || 'Gagal mengubah status bot');
        }
    } catch (error) {
        console.error('Toggle bot error:', error);
        alert('Terjadi kesalahan saat mengubah status bot');
    }
}

// Edit bot (placeholder)
function editBot(botId) {
    alert('Fitur edit akan segera hadir!');
}

// Delete bot
async function deleteBot(botId) {
    if (!confirm('Yakin ingin menghapus bot ini?')) return;

    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`/api/bots/${botId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            loadDashboard();
        } else {
            const data = await response.json();
            alert(data.error || 'Gagal menghapus bot');
        }
    } catch (error) {
        console.error('Delete bot error:', error);
        alert('Terjadi kesalahan saat menghapus bot');
    }
}

// Modal handling
const modal = document.getElementById('addBotModal');
const addBotBtn = document.getElementById('addBotBtn');
const closeBtn = document.querySelector('.close');

if (addBotBtn) {
    addBotBtn.addEventListener('click', () => {
        modal.classList.add('show');
    });
}

if (closeBtn) {
    closeBtn.addEventListener('click', () => {
        modal.classList.remove('show');
    });
}

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    if (e.target === modal) {
        modal.classList.remove('show');
    }
});

// Add bot form
const addBotForm = document.getElementById('addBotForm');
if (addBotForm) {
    addBotForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const token = localStorage.getItem('token');
        
        const formData = {
            name: document.getElementById('botName').value,
            token: document.getElementById('botToken').value,
            template: document.getElementById('botTemplate').value,
            description: document.getElementById('description').value
        };

        try {
            const response = await fetch(`/api/bots`, {
                method: 'POST',
                headers: { 
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                modal.classList.remove('show');
                addBotForm.reset();
                loadDashboard();
            } else {
                const data = await response.json();
                alert(data.error || 'Gagal membuat bot');
            }
        } catch (error) {
            console.error('Create bot error:', error);
            alert('Terjadi kesalahan saat membuat bot');
        }
    });
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
