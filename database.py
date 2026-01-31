import asyncpg
from datetime import datetime
from typing import List, Dict, Optional
import config
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(**config.DB_CONFIG)
            await self.create_tables()
            logger.info("Database ga muvaffaqiyatli ulandi")
        except Exception as e:
            logger.error(f"Database ulanishda xato: {e}")
            raise

    async def create_tables(self):
        async with self.pool.acquire() as conn:
            await conn.execute('''
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
                )
            ''')

            try:
                await conn.execute('''
                    ALTER TABLE contests 
                    ADD COLUMN IF NOT EXISTS channel_chat_id VARCHAR(100)
                ''')
                logger.info("✅ channel_chat_id ustuni qo'shildi/mavjud")
            except Exception as e:
                logger.debug(f"channel_chat_id: {e}")

            try:
                await conn.execute('''
                    ALTER TABLE contests 
                    ADD COLUMN IF NOT EXISTS channel_post_message_id INTEGER
                ''')
                logger.info("✅ channel_post_message_id ustuni qo'shildi/mavjud")
            except Exception as e:
                logger.debug(f"channel_post_message_id: {e}")

            # Kanal talablari jadvali
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS contest_channels (
                    id SERIAL PRIMARY KEY,
                    contest_id INTEGER REFERENCES contests(id) ON DELETE CASCADE,
                    channel_id VARCHAR(100) NOT NULL,
                    channel_name VARCHAR(255),
                    channel_link TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            await conn.execute('''
                CREATE TABLE IF NOT EXISTS candidates (
                    id SERIAL PRIMARY KEY,
                    contest_id INTEGER REFERENCES contests(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    position INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            await conn.execute('''
                CREATE TABLE IF NOT EXISTS votes (
                    id SERIAL PRIMARY KEY,
                    contest_id INTEGER REFERENCES contests(id) ON DELETE CASCADE,
                    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
                    user_id BIGINT NOT NULL,
                    username VARCHAR(255),
                    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(contest_id, user_id)
                )
            ''')

            # Foydalanuvchilar jadvali
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    last_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            await conn.execute('''
                -- Votes jadali uchun (eng muhim!)
                CREATE INDEX IF NOT EXISTS idx_votes_contest ON votes(contest_id);
                CREATE INDEX IF NOT EXISTS idx_votes_candidate ON votes(candidate_id);
                CREATE INDEX IF NOT EXISTS idx_votes_user ON votes(user_id);
                CREATE INDEX IF NOT EXISTS idx_votes_contest_user ON votes(contest_id, user_id);
                CREATE INDEX IF NOT EXISTS idx_votes_created ON votes(voted_at);

                -- Contests jadali uchun
                CREATE INDEX IF NOT EXISTS idx_contests_active ON contests(is_active, is_archived);
                CREATE INDEX IF NOT EXISTS idx_contests_dates ON contests(start_date, end_date);

                -- Candidates jadali uchun
                CREATE INDEX IF NOT EXISTS idx_candidates_contest ON candidates(contest_id);
                CREATE INDEX IF NOT EXISTS idx_candidates_position ON candidates(position);

                -- Channels jadali uchun
                CREATE INDEX IF NOT EXISTS idx_channels_contest ON contest_channels(contest_id);

                -- Users jadali uchun
                CREATE INDEX IF NOT EXISTS idx_users_last_action ON users(last_action);
            ''')

    async def create_contest(self, name: str, description: str,
                             start_date: datetime, end_date: datetime,
                             image_file_id: str = None) -> int:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                INSERT INTO contests (name, description, image_file_id, start_date, end_date, is_active)
                VALUES ($1, $2, $3, $4, $5, TRUE)
                RETURNING id
            ''', name, description, image_file_id, start_date, end_date)
            logger.info(f"Yangi konkurs yaratildi: {name} (ID: {row['id']})")
            return row['id']

    async def add_channel_to_contest(self, contest_id: int, channel_id: str,
                                     channel_name: str, channel_link: str):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO contest_channels (contest_id, channel_id, channel_name, channel_link)
                VALUES ($1, $2, $3, $4)
            ''', contest_id, channel_id, channel_name, channel_link)

    async def add_candidate(self, contest_id: int, name: str, description: str = None) -> int:
        """Nomzod qo'shish"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                INSERT INTO candidates (contest_id, name, description)
                VALUES ($1, $2, $3)
                RETURNING id
            ''', contest_id, name, description)
            return row['id']

    async def save_contest_channel_post(self, contest_id: int, channel_chat_id: str, message_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE contests 
                SET channel_chat_id = $1, channel_post_message_id = $2
                WHERE id = $3
            ''', str(channel_chat_id), message_id, contest_id)
            logger.info(f"Konkurs {contest_id} kanal post saqlandi: {channel_chat_id}:{message_id}")

    async def get_contest_channel_post(self, contest_id: int) -> Optional[Dict]:

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT channel_chat_id, channel_post_message_id
                FROM contests 
                WHERE id = $1
            ''', contest_id)
            if row and row['channel_chat_id'] and row['channel_post_message_id']:
                return {
                    'chat_id': row['channel_chat_id'],
                    'message_id': row['channel_post_message_id']
                }
            return None

    async def get_active_contest(self) -> Optional[Dict]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT * FROM contests 
                WHERE is_active = TRUE AND is_archived = FALSE
                ORDER BY created_at DESC LIMIT 1
            ''')
            return dict(row) if row else None

    async def get_all_active_contests(self) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT c.*, 
                       COUNT(DISTINCT v.user_id) as total_voters,
                       COUNT(v.id) as total_votes
                FROM contests c
                LEFT JOIN votes v ON c.id = v.contest_id
                WHERE c.is_active = TRUE AND c.is_archived = FALSE
                GROUP BY c.id
                ORDER BY c.created_at DESC
            ''')
            return [dict(row) for row in rows]

    async def get_all_contests(self) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT c.*, 
                       COUNT(DISTINCT v.user_id) as total_voters,
                       COUNT(v.id) as total_votes
                FROM contests c
                LEFT JOIN votes v ON c.id = v.contest_id
                GROUP BY c.id
                ORDER BY c.created_at DESC
            ''')
            return [dict(row) for row in rows]

    async def get_contest_by_id(self, contest_id: int) -> Optional[Dict]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT * FROM contests WHERE id = $1
            ''', contest_id)
            return dict(row) if row else None

    async def get_contest_channels(self, contest_id: int) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM contest_channels 
                WHERE contest_id = $1
                ORDER BY id
            ''', contest_id)
            return [dict(row) for row in rows]

    async def get_candidates(self, contest_id: int) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT c.*, COALESCE(COUNT(v.id), 0) as vote_count
                FROM candidates c
                LEFT JOIN votes v ON c.id = v.candidate_id
                WHERE c.contest_id = $1
                GROUP BY c.id
                ORDER BY c.position, c.name
            ''', contest_id)
            return [dict(row) for row in rows]

    async def has_voted(self, contest_id: int, user_id: int) -> bool:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT 1 FROM votes 
                WHERE contest_id = $1 AND user_id = $2
                LIMIT 1
            ''', contest_id, user_id)
            return row is not None

    async def add_vote(self, contest_id: int, candidate_id: int,
                       user_id: int, username: str = None) -> bool:

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    existing = await conn.fetchval('''
                        SELECT 1 FROM votes 
                        WHERE contest_id = $1 AND user_id = $2
                        FOR UPDATE  -- Database LOCK
                    ''', contest_id, user_id)

                    if existing:
                        logger.warning(f"User {user_id} allaqachon ovoz bergan (transaction check)")
                        return False

                    await conn.execute('''
                        INSERT INTO votes (contest_id, candidate_id, user_id, username, voted_at)
                        VALUES ($1, $2, $3, $4, NOW())
                    ''', contest_id, candidate_id, user_id, username)

                    logger.info(f"Ovoz qo'shildi: User {user_id} -> Candidate {candidate_id}")
                    return True

        except asyncpg.UniqueViolationError:
            logger.warning(f"UniqueViolation: User {user_id} allaqachon ovoz bergan")
            return False
        except Exception as e:
            logger.error(f"Ovoz qo'shishda xato: {e}")
            return False

    async def get_vote_results(self, contest_id: int) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT 
                    c.name as candidate_name,
                    c.description,
                    COUNT(v.id) as votes,
                    ROUND(COUNT(v.id) * 100.0 / NULLIF(
                        (SELECT COUNT(*) FROM votes WHERE contest_id = $1), 0
                    ), 2) as percentage
                FROM candidates c
                LEFT JOIN votes v ON c.id = v.candidate_id
                WHERE c.contest_id = $1
                GROUP BY c.id, c.name, c.description
                ORDER BY votes DESC, c.name
            ''', contest_id)
            return [dict(row) for row in rows]

    async def get_detailed_report(self, contest_id: int) -> Dict:
        """Batafsil hisobot - OPTIMIZED"""
        async with self.pool.acquire() as conn:
            contest = await conn.fetchrow(
                'SELECT * FROM contests WHERE id = $1', contest_id
            )

            if not contest:
                return None

            stats = await conn.fetchrow('''
                SELECT 
                    COUNT(DISTINCT user_id) as total_voters,
                    COUNT(*) as total_votes
                FROM votes WHERE contest_id = $1
            ''', contest_id)

            candidates = await self.get_vote_results(contest_id)

            return {
                'contest': dict(contest),
                'stats': dict(stats) if stats else {'total_voters': 0, 'total_votes': 0},
                'candidates': candidates
            }

    async def archive_contest(self, contest_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE contests 
                SET is_active = FALSE, is_archived = TRUE
                WHERE id = $1
            ''', contest_id)
            logger.info(f"Konkurs {contest_id} arxivga o'tkazildi")

    async def stop_contest(self, contest_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE contests 
                SET is_active = FALSE, 
                    is_archived = TRUE,
                    end_date = NOW()
                WHERE id = $1
            ''', contest_id)
            logger.info(f"Konkurs {contest_id} to'xtatildi va arxivga o'tkazildi")

    async def reset_contest_votes(self, contest_id: int):
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                'DELETE FROM votes WHERE contest_id = $1', contest_id
            )
            logger.info(f"Konkurs {contest_id} ovozlari tozalandi: {result}")

    async def get_archived_contests(self) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT 
                    c.*,
                    COUNT(DISTINCT v.user_id) as total_voters,
                    COUNT(v.id) as total_votes
                FROM contests c
                LEFT JOIN votes v ON c.id = v.contest_id
                WHERE c.is_archived = TRUE
                GROUP BY c.id
                ORDER BY c.end_date DESC
            ''')
            return [dict(row) for row in rows]

    async def update_user_activity(self, user_id: int, username: str = None,
                                   first_name: str = None, last_name: str = None):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO users (user_id, username, first_name, last_name, last_action)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    last_action = NOW()
            ''', user_id, username, first_name, last_name)

    async def check_rate_limit(self, user_id: int, seconds: int = 5) -> bool:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT 1 FROM users 
                WHERE user_id = $1 
                AND last_action > NOW() - INTERVAL '1 second' * $2
                LIMIT 1
            ''', user_id, seconds)
            return row is None

    async def get_total_stats(self) -> Dict:
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow('''
                SELECT 
                    (SELECT COUNT(*) FROM contests) as total_contests,
                    (SELECT COUNT(*) FROM contests WHERE is_active = TRUE) as active_contests,
                    (SELECT COUNT(*) FROM votes) as total_votes,
                    (SELECT COUNT(DISTINCT user_id) FROM votes) as total_users
            ''')
            return dict(stats) if stats else {}

    async def close(self):
        if self.pool:
            await self.pool.close()
            logger.info("Database ulanishi yopildi")