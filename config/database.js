const { Pool } = require('pg');
require('dotenv').config({ path: require('path').join(__dirname, '../.env') });

const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    // Konfigurasi SSL yang kompatibel dengan Neon dan menghilangkan warning
    ssl: process.env.NODE_ENV === 'production' 
        ? { rejectUnauthorized: true } 
        : { rejectUnauthorized: false } 
});

// Test koneksi
pool.on('error', (err) => {
    console.error('❌ Database error:', err);
});

module.exports = {
    query: (text, params) => pool.query(text, params),
    pool
};