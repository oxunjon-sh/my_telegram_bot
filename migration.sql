-- Versiya: 2.0 (Real-time updates)
-- Sana: 2026-01-22
-- 
-- Ishlatish:
--   psql -U postgres -d voting_bot_db -f migration.sql
-- 
-- ============================================================

-- Database yaratish (agar kerak bo'lsa)
-- CREATE DATABASE voting_bot_db;
-- \c voting_bot_db;

-- ============================================================
-- 1. JADVALLARNI YARATISH
-- ============================================================

-- -------------------- KONKURSLAR JADVALI --------------------
CREATE TABLE IF NOT EXISTS contests (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    image_file_id VARCHAR(255),
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE contests IS 'Ovoz berish konkurslari';
COMMENT ON COLUMN contests.name IS 'Konkurs nomi';
COMMENT ON COLUMN contests.description IS 'Konkurs tavsifi (ixtiyoriy)';
COMMENT ON COLUMN contests.image_file_id IS 'Telegram fayl ID (rasm)';
COMMENT ON COLUMN contests.start_date IS 'Konkurs boshlanish sanasi';
COMMENT ON COLUMN contests.end_date IS 'Konkurs tugash sanasi';
COMMENT ON COLUMN contests.is_active IS 'Konkurs faol/faol emas';
COMMENT ON COLUMN contests.is_archived IS 'Konkurs arxivlangan';

-- -------------------- KANAL TALABLARI JADVALI --------------------
CREATE TABLE IF NOT EXISTS contest_channels (
    id SERIAL PRIMARY KEY,
    contest_id INTEGER NOT NULL REFERENCES contests(id) ON DELETE CASCADE,
    channel_id VARCHAR(100) NOT NULL,
    channel_name VARCHAR(255),
    channel_link TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE contest_channels IS 'Konkurs uchun talab qilinadigan kanallar';
COMMENT ON COLUMN contest_channels.channel_id IS 'Telegram kanal chat ID';
COMMENT ON COLUMN contest_channels.channel_name IS 'Kanal nomi';
COMMENT ON COLUMN contest_channels.channel_link IS 'Kanal linki (https://t.me/...)';

-- -------------------- NOMZODLAR JADVALI --------------------
CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,
    contest_id INTEGER NOT NULL REFERENCES contests(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    position INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE candidates IS 'Konkurs nomzodlari';
COMMENT ON COLUMN candidates.name IS 'Nomzod ismi';
COMMENT ON COLUMN candidates.description IS 'Nomzod haqida (ixtiyoriy)';
COMMENT ON COLUMN candidates.position IS 'Nomzodning tartibi (sort uchun)';

-- -------------------- OVOZLAR JADVALI --------------------
CREATE TABLE IF NOT EXISTS votes (
    id SERIAL PRIMARY KEY,
    contest_id INTEGER NOT NULL REFERENCES contests(id) ON DELETE CASCADE,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    username VARCHAR(255),
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(contest_id, user_id)
);

COMMENT ON TABLE votes IS 'Foydalanuvchilar ovozlari';
COMMENT ON COLUMN votes.user_id IS 'Telegram user ID';
COMMENT ON COLUMN votes.username IS 'Telegram username';
COMMENT ON COLUMN votes.voted_at IS 'Ovoz berilgan vaqt';

-- -------------------- FOYDALANUVCHILAR JADVALI --------------------
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    last_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE users IS 'Bot foydalanuvchilari (rate limiting uchun)';
COMMENT ON COLUMN users.last_action IS 'Oxirgi faollik vaqti (spam himoyasi)';


-- ============================================================
-- 2. MIGRATSIYA: REAL-TIME UPDATE UCHUN YANGI USTUNLAR
-- ============================================================

-- Contests jadvaliga yangi ustunlar qo'shish
ALTER TABLE contests 
ADD COLUMN IF NOT EXISTS channel_chat_id VARCHAR(100);

ALTER TABLE contests 
ADD COLUMN IF NOT EXISTS channel_post_message_id INTEGER;

COMMENT ON COLUMN contests.channel_chat_id IS 'Kanalning chat ID (bitta kanal uchun)';
COMMENT ON COLUMN contests.channel_post_message_id IS 'Post message ID (bitta kanal uchun)';

-- Contest_channels jadvaliga yangi ustun qo'shish (ko'p kanalli versiya)
ALTER TABLE contest_channels 
ADD COLUMN IF NOT EXISTS posted_message_id INTEGER;

COMMENT ON COLUMN contest_channels.posted_message_id IS 'Har bir kanalga yuborilgan post message ID';


-- ============================================================
-- 3. INDEXLAR YARATISH
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_votes_contest
ON votes(contest_id);

CREATE INDEX IF NOT EXISTS idx_votes_candidate 
ON votes(candidate_id);

CREATE INDEX IF NOT EXISTS idx_votes_user 
ON votes(user_id);

CREATE INDEX IF NOT EXISTS idx_votes_contest_user 
ON votes(contest_id, user_id);

CREATE INDEX IF NOT EXISTS idx_votes_created 
ON votes(voted_at);

CREATE INDEX IF NOT EXISTS idx_contests_active
ON contests(is_active, is_archived);

CREATE INDEX IF NOT EXISTS idx_contests_dates 
ON contests(start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_candidates_contest 
ON candidates(contest_id);

CREATE INDEX IF NOT EXISTS idx_candidates_position 
ON candidates(position);

CREATE INDEX IF NOT EXISTS idx_channels_contest
ON contest_channels(contest_id);

CREATE INDEX IF NOT EXISTS idx_channel_posts 
ON contest_channels(contest_id, posted_message_id) 
WHERE posted_message_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_users_last_action
ON users(last_action);


-- ============================================================
-- 4. YAKUNIY XABAR
-- ============================================================

DO $$ 
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'MIGRATSIYA MUVAFFAQIYATLI TUGADI!';
    RAISE NOTICE '============================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Jadvallar yaratildi:';
    RAISE NOTICE '  ✅ contests';
    RAISE NOTICE '  ✅ contest_channels';
    RAISE NOTICE '  ✅ candidates';
    RAISE NOTICE '  ✅ votes';
    RAISE NOTICE '  ✅ users';
    RAISE NOTICE '';
    RAISE NOTICE 'Indexlar yaratildi: 11 ta';
    RAISE NOTICE '';
    RAISE NOTICE 'Endi botni ishga tushirishingiz mumkin:';
    RAISE NOTICE '  python bot.py';
    RAISE NOTICE '';
    RAISE NOTICE '============================================================';
END $$;