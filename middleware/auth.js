const jwt = require('jsonwebtoken');

const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

    if (!token) {
        return res.status(401).json({ error: 'Token tidak ditemukan. Silakan login.' });
    }

    try {
        const user = jwt.verify(token, process.env.JWT_SECRET);
        req.user = user; // { id, telegram_id, role }
        next();
    } catch (err) {
        return res.status(403).json({ error: 'Token tidak valid atau sudah expired. Silakan login ulang.' });
    }
};

const requireAdmin = (req, res, next) => {
    if (req.user.role !== 'admin') {
        return res.status(403).json({ error: 'Akses ditolak. Admin only.' });
    }
    next();
};

module.exports = { authenticateToken, requireAdmin };