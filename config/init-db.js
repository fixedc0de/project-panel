const db = require('./database');

const initDatabase = async () => {
    try {
        // Tabel Users
        await db.query(`
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(255),
                password_hash VARCHAR(255) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                role VARCHAR(20) DEFAULT 'user',
                created_at TIMESTAMP DEFAULT NOW(),
                last_login TIMESTAMP
            )
        `);

        // Tabel Verification Codes
        await db.query(`
            CREATE TABLE IF NOT EXISTS verification_codes (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT NOT NULL,
                code VARCHAR(6) NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                attempts INTEGER DEFAULT 0,
                used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            )
        `);

        // Tabel Bots (terkait dengan user)
        await db.query(`
            CREATE TABLE IF NOT EXISTS bots (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                bot_name VARCHAR(100) NOT NULL,
                template_id VARCHAR(50) NOT NULL,
                token TEXT UNIQUE NOT NULL,
                bot_username VARCHAR(100),
                description TEXT,
                status VARCHAR(20) DEFAULT 'stopped',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW(),
                last_active TIMESTAMP DEFAULT NOW()
            )
        `);

        // Migration: Add missing columns if table already exists
        try {
            await db.query(`ALTER TABLE bots ADD COLUMN IF NOT EXISTS bot_username VARCHAR(100)`);
            await db.query(`ALTER TABLE bots ADD COLUMN IF NOT EXISTS description TEXT`);
            await db.query(`ALTER TABLE bots ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE`);
            await db.query(`ALTER TABLE bots ADD COLUMN IF NOT EXISTS last_active TIMESTAMP DEFAULT NOW()`);
        } catch (migrationErr) {
            console.log('⚠️ Migration check completed.');
        }

        // Tabel Password Resets (untuk forgot password)
        await db.query(`
            CREATE TABLE IF NOT EXISTS password_resets (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT NOT NULL,
                code VARCHAR(6) NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                attempts INTEGER DEFAULT 0,
                used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            )
        `);

        console.log('✅ Database tables initialized successfully');
    } catch (err) {
        console.error('❌ Database init error:', err);
        process.exit(1);
    }
};

module.exports = initDatabase;