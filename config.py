import os
from dotenv import load_dotenv

# .env faylini yuklash
load_dotenv()

# ============================================
# BOT SOZLAMALARI
# ============================================
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylida topilmadi!")

# ============================================
# DATABASE SOZLAMALARI
# ============================================
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'voting_bot_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),

    # PERFORMANCE OPTIMIZATION FOR 500K+ USERS
    'min_size': 20,  # Minimum connections (increased for high load)
    'max_size': 100,  # Maximum connections (support 500K concurrent users)
    'max_queries': 50000,  # Max queries per connection before recycling
    'max_inactive_connection_lifetime': 300,  # Close idle connections after 5 min
    'command_timeout': 60,  # Query timeout (seconds)
    'timeout': 30,  # Connection timeout
    'server_settings': {
        'timezone': 'UTC',  # IMPORTANT: Always use UTC in database
        'application_name': 'voting_bot',
    }
}

# ============================================
# ADMIN SOZLAMALARI
# ============================================
ADMIN_IDS = [
    int(id.strip())
    for id in os.getenv('ADMIN_IDS', '').split(',')
    if id.strip()
]

if not ADMIN_IDS:
    raise ValueError("ADMIN_IDS .env faylida topilmadi!")

# ============================================
# LOG SOZLAMALARI
# ============================================
LOG_FILE = os.getenv('LOG_FILE', 'bot.log')

# ============================================
# KANAL SOZLAMALARI
# ============================================
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not CHANNEL_ID:
    raise ValueError("CHANNEL_ID .env faylida topilmadi!")

# Kanal linki (ixtiyoriy)
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "")

# ============================================
# OVOZ BERISH SOZLAMALARI
# ============================================
MAX_VOTES_PER_USER = 1  # Har bir foydalanuvchi bitta ovoz beradi
RATE_LIMIT_SECONDS = 1  # Spam himoyasi uchun