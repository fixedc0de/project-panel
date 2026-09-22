-- Reset Database Script untuk Bot Panel
-- Jalankan di Neon Dashboard atau psql client

-- Drop semua tabel (urutan penting karena foreign keys)
DROP TABLE IF EXISTS password_resets CASCADE;
DROP TABLE IF EXISTS bots CASCADE;
DROP TABLE IF EXISTS verification_codes CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Buat ulang tabel users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Tabel verification codes (untuk registrasi)
CREATE TABLE verification_codes (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    code VARCHAR(6) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    attempts INTEGER DEFAULT 0,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabel bots
CREATE TABLE bots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    bot_name VARCHAR(100) NOT NULL,
    template_id VARCHAR(50) NOT NULL,
    token TEXT UNIQUE,
    bot_username VARCHAR(100),
    description TEXT,
    status VARCHAR(20) DEFAULT 'stopped',
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW()
);

-- Tabel password resets (untuk forgot password)
CREATE TABLE password_resets (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    code VARCHAR(6) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    attempts INTEGER DEFAULT 0,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index untuk performa
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_verification_codes_telegram_id ON verification_codes(telegram_id);
CREATE INDEX idx_bots_user_id ON bots(user_id);
CREATE INDEX idx_password_resets_telegram_id ON password_resets(telegram_id);

COMMENT ON TABLE users IS 'Data pengguna panel bot';
COMMENT ON TABLE verification_codes IS 'Kode verifikasi untuk registrasi';
COMMENT ON TABLE bots IS 'Daftar bot yang dibuat user';
COMMENT ON TABLE password_resets IS 'Kode reset untuk forgot password';
