# 🗳 Telegram Ovoz Berish Boti

Telegram orqali konkurslar va ovoz berish uchun professional bot. Real-time natijalar ko'rsatish, ko'p kanalli qo'llab-quvvatlash va avtomatik yangilanish bilan.

## ✨ Xususiyatlar

### 🎯 Asosiy Imkoniyatlar
- ✅ **Ko'p konkursli tizim** - Bir vaqtning o'zida bir nechta konkurs
- ✅ **Real-time yangilanish** - Ovozlar soni avtomatik yangilanadi
- ✅ **Kanal integratsiyasi** - Kanalda post va ovoz berish
- ✅ **Deep link** - Kanaldan to'g'ridan-to'g'ri ovoz berish
- ✅ **Kanal majburiyati** - Ovoz berish uchun kanalga obuna
- ✅ **Rasm qo'llab-quvvatlash** - Konkurs rasmi bilan
- ✅ **Admin panel** - To'liq boshqaruv paneli

### 📊 Hisobot va Eksport
- 📈 **Excel hisobot** - Batafsil statistika
- 📄 **CSV eksport** - Ma'lumotlarni eksport qilish
- 📊 **Grafik** - Vizual natijalar
- 📋 **Real-time statistika** - Jonli natijalar

### 🔒 Xavfsizlik
- 🛡 **Bir kishi - bir ovoz** - Takroriy ovoz berishning oldini olish
- 🔐 **Transaction** - Ma'lumotlar izchilligi
- ⚡ **Rate limiting** - Spam himoyasi
- 📝 **Full logging** - Barcha harakatlar yozib olinadi

### ⚙️ Texnik Imkoniyatlar
- 🚀 **Optimizatsiya** - Database indexlar va connection pooling
- 🔄 **Avtomatik yangilanish** - Kanal postlari real-time yangilanadi
- 📱 **Responsive** - Mobil qurilmalarda mukammal ishlaydi
- 🌐 **Ko'p tilli** - O'zbek tilida

---

## 📋 Talablar

### Zarur Dasturlar
- **Python 3.10+** (tavsiya 3.11)
- **PostgreSQL 12+** (tavsiya 14 yoki 15)
- **Telegram Bot Token** ([@BotFather](https://t.me/BotFather) dan)

### Python Kutubxonalari
```txt
aiogram==3.4.1
asyncpg==0.29.0
python-dotenv==1.0.0
pandas==2.1.4
openpyxl==3.1.2
matplotlib==3.8.2
```

---

## 🚀 O'RNATISH

### 1️⃣ Loyihani Yuklab Olish

```bash
# Git orqali
git clone <repository-url>
cd my_telegram_bot

# Yoki ZIP ni ochish
unzip my_telegram_bot.zip
cd my_telegram_bot
```

### 2️⃣ Virtual Muhit Yaratish

```bash
# Virtual muhit yaratish
python3 -m venv .venv

# Aktivlashtirish
# Mac/Linux:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate
```

### 3️⃣ Kutubxonalarni O'rnatish

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```txt
aiogram==3.4.1
asyncpg==0.29.0
python-dotenv==1.0.0
pandas==2.1.4
openpyxl==3.1.2
matplotlib==3.8.2
```

### 4️⃣ PostgreSQL Database Yaratish

#### Mac (Homebrew)
```bash
# PostgreSQL o'rnatish
brew install postgresql@14
brew services start postgresql@14

# Database yaratish
createdb voting_bot_db
```

#### Ubuntu/Debian
```bash
# PostgreSQL o'rnatish
sudo apt update
sudo apt install postgresql postgresql-contrib

# PostgreSQL ni ishga tushirish
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Database yaratish
sudo -u postgres createdb voting_bot_db
```

#### Windows
1. [PostgreSQL](https://www.postgresql.org/download/windows/) yuklab oling
2. Installer orqali o'rnating
3. pgAdmin 4 ni oching
4. "voting_bot_db" database yarating

### 5️⃣ Environment O'rnatish

Loyiha katalogida `.env` fayli yarating:

```env
# ============================================
# BOT SOZLAMALARI
# ============================================
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# ============================================
# DATABASE SOZLAMALARI
# ============================================
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voting_bot_db
DB_USER=postgres
DB_PASSWORD=your_password_here

# ============================================
# ADMIN SOZLAMALARI
# ============================================
# Bir nechta admin ID larni vergul bilan ajrating
ADMIN_IDS=123456789,987654321

# ============================================
# KANAL SOZLAMALARI
# ============================================
# Asosiy kanal (majburiy)
CHANNEL_ID=-1001234567890

# Kanal linki (ixtiyoriy)
CHANNEL_LINK=https://t.me/mychannel

# ============================================
# LOG SOZLAMALARI
# ============================================
LOG_FILE=bot.log
```

**🔑 Muhim eslatmalar:**

1. **BOT_TOKEN ni olish:**
   - [@BotFather](https://t.me/BotFather) ga boring
   - `/newbot` buyrug'ini yuboring
   - Bot nomini kiriting (masalan: "My Voting Bot")
   - Bot username ni kiriting (masalan: "my_voting_bot")
   - Token ni oling va `.env` ga qo'shing

2. **Admin ID ni olish:**
   - [@userinfobot](https://t.me/userinfobot) ga boring
   - `/start` yuboring
   - ID ni ko'chirib `.env` ga qo'shing

3. **Kanal ID ni olish:**
   - Kanalga kiring
   - Bot'ni kanalga qo'shing va admin qiling
   - Bot loglarida kanal ID si ko'rinadi
   - Yoki [@username_to_id_bot](https://t.me/username_to_id_bot) dan foydalaning

### 6️⃣ Bot ni Kanalga Admin Qilish

1. Telegram'da kanalingizni oching
2. **Settings → Administrators → Add Administrator**
3. Botni qidiring va tanlang
4. Quyidagi huquqlarni bering:
   - ✅ **Post messages**
   - ✅ **Edit messages of others**
   - ✅ **Delete messages of others** (ixtiyoriy)

### 7️⃣ Database Migratsiyasi

```bash
# Terminalni oching
cd my_telegram_bot

# Migratsiyani bajaring
psql -U postgres -d voting_bot_db -f migration.sql

# Yoki PostgreSQL ichida
psql -U postgres -d voting_bot_db
\i migration.sql
\q
```

**Migratsiya natijasi:**
```
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE INDEX
...
✅ Migratsiya muvaffaqiyatli!
```

### 8️⃣ Botni Ishga Tushirish

```bash
# Virtual muhitni aktivlashtiring (agar hali aktivlashtirilmagan bo'lsa)
source .venv/bin/activate  # Mac/Linux
# yoki
.venv\Scripts\activate     # Windows

# Botni ishga tushiring
python bot.py
```

**✅ Muvaffaqiyatli!** Bot ishga tushdi!

Siz quyidagi xabarni ko'rishingiz kerak:
```
INFO - Database ga ulanish...
INFO - Database ulandi ✅
INFO - Polling boshlandi...
```

---

## 📁 Loyiha Strukturasi

```
my_telegram_bot/
├── bot.py                 # Asosiy ishga tushirish fayli
├── config.py              # Konfiguratsiya (environment variables)
├── database.py            # Database boshqaruvi (async PostgreSQL)
├── keyboards.py           # Telegram klaviaturalar
├── utils.py              # Yordamchi funksiyalar
│
├── handlers/
│   ├── __init__.py       # Package init
│   ├── admin.py          # Admin panel handlerlari
│   └── user.py           # Foydalanuvchi handlerlari
│
├── .env                  # Environment variables (GIT ga qo'shilMAYDI!)
├── .gitignore           # Git ignore fayli
├── requirements.txt      # Python dependencies
├── migration.sql         # Database migration
├── README.md            # Ushbu qo'llanma
└── bot.log              # Log fayl (avtomatik yaratiladi)
```

---

## 🎮 ISHLATISH

### Admin Panel

1. Bot'ni ishga tushiring
2. Telegram'da botga `/start` yuboring
3. **👨‍💼 Admin Panel** tugmasini bosing

### Konkurs Yaratish (Qadam-ba-qadam)

#### 1. Yangi Konkurs Boshlash
- **➕ Yangi konkurs** tugmasini bosing

#### 2. Konkurs Ma'lumotlari
```
📝 Konkurs nomi:
→ "Yilning eng yaxshi shifokorlari 2025"

🖼 Rasm:
→ Rasm yuboring yoki /skip

📅 Boshlanish sanasi:
→ 22.01.2026 09:00

⏰ Tugash sanasi:
→ 30.01.2026 23:59
```

#### 3. Kanallar
```
📢 Kanallar soni:
→ 2

Kanal 1:
• ID: @mychannel
• Nom: Mening Kanali
• Link: https://t.me/mychannel

Kanal 2:
• ID: @mychannel2
• Nom: Ikkinchi Kanal
• Link: https://t.me/mychannel2
```

#### 4. Nomzodlar
```
👥 Nomzodlar soni:
→ 3

Nomzod 1: Dr.Aziz
Nomzod 2: Dr.Nodir
Nomzod 3: Dr.Jasur
```

#### 5. Tasdiqlash
- Preview ni ko'ring
- **✅ Ha, kanalga post qiling** ni bosing

### Konkursni Boshqarish

| Tugma | Tavsif |
|-------|--------|
| 📊 **Natijalar** | Joriy natijalarni ko'rish |
| 📋 **Batafsil hisobot** | To'liq statistika va g'oliblar |
| 📥 **Eksport** | Excel/CSV/Grafik yuklab olish |
| ⏸ **Konkursni to'xtatish** | Muddatidan oldin to'xtatish |
| 🗑 **Ovozlarni tozalash** | Barcha ovozlarni o'chirish |
| 📚 **Arxiv** | O'tgan konkurslarni ko'rish |

### Foydalanuvchi Uchun Ovoz Berish

#### Kanal orqali (Deep Link):
1. Kanalda konkurs postini ko'rish
2. Nomzodni tanlash
3. Botga avtomatik o'tish
4. Kanallarga obuna bo'lish (agar kerak bo'lsa)
5. Ovozni tasdiqlash
6. ✅ Tayyor!

#### Bot ichidan:
1. Botda **🗳 Ovoz berish** tugmasini bosish
2. Kanallarga obuna bo'lish
3. Nomzod tanlash
4. Tasdiqlash

---

## 🔧 KONFIGURATSIYA

### Database Optimization

`config.py` da:
```python
DB_CONFIG = {
    'min_size': 10,   # Minimum connections
    'max_size': 50,   # Maximum connections
    'command_timeout': 60,  # Query timeout
}
```

**Tavsiyalar:**
- Kichik botlar (< 100 user): `min_size=5, max_size=20`
- O'rta botlar (100-1000 user): `min_size=10, max_size=50`
- Katta botlar (> 1000 user): `min_size=20, max_size=100`

### Rate Limiting

```python
RATE_LIMIT_SECONDS = 1  # Har 1 sekundda bitta harakat
```

---

## 🐛 MUAMMOLARNI HAL QILISH

### ❌ Bot ishga tushmayapti

#### Sabab 1: Token noto'g'ri
```bash
# .env ni tekshiring
cat .env | grep BOT_TOKEN

# Token'ni @BotFather dan qayta oling
```

#### Sabab 2: Python versiyasi eski
```bash
# Python versiyasini tekshiring
python --version

# Kamida Python 3.10 kerak
```

#### Sabab 3: Kutubxonalar o'rnatilmagan
```bash
# Virtual muhitni aktivlashtiring
source .venv/bin/activate

# Kutubxonalarni qayta o'rnating
pip install -r requirements.txt
```

### ❌ Database ga ulanish xatosi

#### Sabab 1: PostgreSQL ishlamayapti
```bash
# PostgreSQL holati
sudo systemctl status postgresql

# Ishga tushirish
sudo systemctl start postgresql
```

#### Sabab 2: Parol noto'g'ri
```bash
# PostgreSQL'ga kirish va tekshirish
psql -U postgres -d voting_bot_db

# Agar kirolmasangiz, parolni o'zgartiring
sudo -u postgres psql
ALTER USER postgres PASSWORD 'yangi_parol';
\q

# .env da parolni yangilang
```

#### Sabab 3: Database mavjud emas
```bash
# Database'larni ko'rish
psql -U postgres -l

# Agar voting_bot_db yo'q bo'lsa:
createdb voting_bot_db
```

### ❌ Kanalga post qilolmayapti

#### Sabab 1: Bot kanalda admin emas
1. Kanalga kiring
2. Settings → Administrators
3. Botni admin qiling
4. **Post messages** huquqini bering

#### Sabab 2: Kanal ID noto'g'ri
```bash
# Bot loglarini ko'ring
tail -f bot.log

# Kanal ID formatini tekshiring:
# To'g'ri: -1001234567890
# Noto'g'ri: @mychannel (bu username, ID emas!)
```

#### Sabab 3: Bot banned
- Botni kanaldan o'chirib, qayta admin qiling

### ❌ Ovozlar yangilanmayapti

#### Sabab: Migratsiya bajarilmagan
```bash
# Migratsiyani qayta bajaring
psql -U postgres -d voting_bot_db -f migration.sql

# Yoki manual
psql -U postgres -d voting_bot_db
ALTER TABLE contests ADD COLUMN IF NOT EXISTS channel_chat_id VARCHAR(100);
ALTER TABLE contests ADD COLUMN IF NOT EXISTS channel_post_message_id INTEGER;
\q
```

### ❌ Eksport ishlamayapti

#### Sabab: matplotlib konfiguratsiya xatosi
```bash
# matplotlib'ni qayta o'rnating
pip uninstall matplotlib
pip install matplotlib==3.8.2
```

---

## 📊 DATABASE MA'LUMOTLARI

### Jadvallar

| Jadval | Tavsif | Asosiy Ustunlar |
|--------|--------|-----------------|
| **contests** | Konkurslar | id, name, start_date, end_date, is_active |
| **candidates** | Nomzodlar | id, contest_id, name |
| **votes** | Ovozlar | id, contest_id, candidate_id, user_id |
| **contest_channels** | Kanallar | id, contest_id, channel_id, channel_link |
| **users** | Foydalanuvchilar | user_id, username, last_action |

### Indexlar (Tezlik uchun)

```sql
-- Ovozlar jadvali
idx_votes_contest
idx_votes_candidate
idx_votes_user
idx_votes_contest_user

-- Konkurslar jadvali
idx_contests_active
idx_contests_dates

-- Boshqalar
idx_candidates_contest
idx_channels_contest
idx_users_last_action
```

---

## 🔄 YANGILANISH

### Kod Yangilash

```bash
# Git orqali
git pull origin main

# Kutubxonalarni yangilash
pip install -r requirements.txt --upgrade

# Database migratsiyasini tekshirish
psql -U postgres -d voting_bot_db -f migration.sql

# Botni qayta ishga tushirish
python bot.py
```

---

## 🚀 PRODUCTION DEPLOYMENT

### Systemd Service (Linux)

`/etc/systemd/system/voting-bot.service`:

```ini
[Unit]
Description=Telegram Voting Bot
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/my_telegram_bot
Environment="PATH=/home/ubuntu/my_telegram_bot/.venv/bin"
ExecStart=/home/ubuntu/my_telegram_bot/.venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Ishga tushirish:
```bash
sudo systemctl daemon-reload
sudo systemctl enable voting-bot
sudo systemctl start voting-bot
sudo systemctl status voting-bot

# Loglarni ko'rish
sudo journalctl -u voting-bot -f
```

### PM2 (Alternative)

```bash
# PM2 o'rnatish
npm install -g pm2

# Botni ishga tushirish
pm2 start bot.py --name voting-bot --interpreter python3

# Auto-restart qo'shish
pm2 startup
pm2 save

# Loglar
pm2 logs voting-bot
```

---

## 📝 FAQ (Tez-tez Beriladigan Savollar)

### Q: Bot bepul?
A: Ha, bot to'liq bepul va open-source.

### Q: Ko'p konkurs bir vaqtda bo'lishi mumkinmi?
A: Ha, lekin bitta vaqtning o'zida faqat bitta **faol** konkurs bo'lishi mumkin.

### Q: Ovozlarni kim ko'radi?
A: Faqat adminlar to'liq hisobotni ko'radi. Boshqa foydalanuvchilar faqat umumiy natijalarni ko'radi.

### Q: Ovoz berilgandan keyin o'zgartirish mumkinmi?
A: Yo'q, har bir foydalanuvchi faqat 1 marta ovoz beradi va o'zgartira olmaydi.

### Q: Bot qancha foydalanuvchiga bardosh beradi?
A: Database optimizatsiya qilingan, 10,000+ concurrent users uchun.

### Q: Kanallar majburiyatini o'chirib qo'yish mumkinmi?
A: Ha, konkurs yaratishda "Kanallar soni: 0" kiriting.

---

## 🤝 YORDAM VA QO'LLAB-QUVVATLASH

### Muammo yoki Savol

1. **GitHub Issues** - Bug report yoki feature request
2. **Telegram** - [@Sharipov_Oxunjon](https://t.me/Sharipov_Oxunjon)
3. **Email** - support@example.com

### Hissa Qo'shish

1. Repository ni fork qiling
2. Feature branch yarating: `git checkout -b feature/AmazingFeature`
3. Commit qiling: `git commit -m 'Add AmazingFeature'`
4. Push qiling: `git push origin feature/AmazingFeature`
5. Pull Request oching

---

## 📜 LITSENZIYA

MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## 🎉 MINNATDORCHILIK

- **[Aiogram](https://github.com/aiogram/aiogram)** - Ajoyib Telegram Bot framework
- **[asyncpg](https://github.com/MagicStack/asyncpg)** - Tez PostgreSQL driver
- **[PostgreSQL](https://www.postgresql.org/)** - Ishonchli database
- **[Python](https://www.python.org/)** - Universal dasturlash tili

---

**Bot tayyor! Omad tilaymiz! 🍀🎉**

---

© 2026 Telegram Voting Bot. Barcha huquqlar himoyalangan.