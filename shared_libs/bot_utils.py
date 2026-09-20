"""
Shared Library untuk Bot Telegram
Berisi fungsi-fungsi umum yang bisa digunakan oleh semua template bot
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

class DatabaseManager:
    """Manajer database SQLite untuk bot individual"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.ensure_directory()
        self.init_db()
    
    def ensure_directory(self):
        """Pastikan direktori database ada"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    def get_connection(self):
        """Mendapatkan koneksi database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Inisialisasi tabel dasar (bisa di-override oleh bot spesifik)"""
        pass
    
    def execute(self, query: str, params: tuple = ()):
        """Execute query dengan commit"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor
        finally:
            conn.close()
    
    def fetch_all(self, query: str, params: tuple = ()):
        """Fetch semua hasil query"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()
    
    def fetch_one(self, query: str, params: tuple = ()):
        """Fetch satu hasil query"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        finally:
            conn.close()


class ModuleRegistry:
    """Registry untuk modul bot yang modular"""
    
    _modules: Dict[str, Any] = {}
    
    @classmethod
    def register(cls, name: str):
        """Decorator untuk mendaftarkan modul"""
        def decorator(module_class):
            cls._modules[name] = module_class
            return module_class
        return decorator
    
    @classmethod
    def get_module(cls, name: str):
        """Mengambil modul berdasarkan nama"""
        return cls._modules.get(name)
    
    @classmethod
    def get_all_modules(cls):
        """Mengambil semua modul yang terdaftar"""
        return cls._modules.copy()
    
    @classmethod
    def list_modules(cls):
        """List semua nama modul"""
        return list(cls._modules.keys())


def format_duration(seconds: int) -> str:
    """Format durasi dalam detik menjadi string yang mudah dibaca"""
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    
    if days > 0:
        return f"{days} hari {hours} jam {minutes} menit"
    elif hours > 0:
        return f"{hours} jam {minutes} menit {secs} detik"
    elif minutes > 0:
        return f"{minutes} menit {secs} detik"
    else:
        return f"{secs} detik"


def sanitize_text(text: str, max_length: int = 4096) -> str:
    """Sanitize teks untuk menghindari masalah dengan Telegram"""
    if not text:
        return ""
    # Batasi panjang teks
    text = text[:max_length]
    # Hapus karakter kontrol yang tidak diinginkan
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    return text


def is_admin(user_id: int, admin_list: List[int]) -> bool:
    """Cek apakah user adalah admin"""
    return user_id in admin_list or user_id == 0  # 0 adalah creator


def log_action(bot_name: str, action: str, user_id: int, details: str = ""):
    """Log aktivitas bot"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{bot_name}] {action} by user {user_id}"
    if details:
        log_entry += f" - {details}"
    print(log_entry)
    # Bisa ditambahkan untuk menyimpan ke file log


__all__ = [
    'DatabaseManager',
    'ModuleRegistry',
    'format_duration',
    'sanitize_text',
    'is_admin',
    'log_action'
]
