import os
from dotenv import load_dotenv

# .env faylini yuklash
load_dotenv()

# Bot sozlamalari
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Database sozlamalari
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'voting_bot'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'min_size': 10,
    'max_size': 50,
    'command_timeout': 60,
}

#Admins
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]

#Log
LOG_FILE = os.getenv('LOG_FILE', 'bot.log')
#Channel
CHANNEL_ID = os.getenv("CHANNEL_ID")

#Kanal linki (ixtiyoriy)
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "")  # Masalan: https://t.me/mychannel

# Ovoz berish sozlamalari
MAX_VOTES_PER_USER = 1  # Har bir foydalanuvchi bitta ovoz beradi
RATE_LIMIT_SECONDS = 0.1  # Spam himoyasi uchun