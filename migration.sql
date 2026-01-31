-- ============================================
-- DATABASE OPTIMIZATION & FIXES
-- ============================================

-- 1. VARCHAR(255) → TEXT (konkurs va nomzod nomlari uchun)
-- ============================================
ALTER TABLE contests ALTER COLUMN name TYPE TEXT;
ALTER TABLE candidates ALTER COLUMN name TYPE TEXT;
ALTER TABLE candidates ALTER COLUMN description TYPE TEXT;

-- 2. TIMEZONE sozlash (UTC)
-- ============================================
ALTER DATABASE voting_bot_db SET timezone = 'UTC';

-- 3. PERFORMANCE TUNING (400-500k users uchun)
-- ============================================

-- Connection pooling settings
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '128MB';

-- 4. OPTIMIZED INDEXES
-- ============================================

-- Votes jadali uchun (eng muhim!)
DROP INDEX IF EXISTS idx_votes_contest;
DROP INDEX IF EXISTS idx_votes_candidate;
DROP INDEX IF EXISTS idx_votes_user;
DROP INDEX IF EXISTS idx_votes_contest_user;
DROP INDEX IF EXISTS idx_votes_created;

-- COMPOUND indexes (katta hajm uchun)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_votes_contest_candidate
    ON votes(contest_id, candidate_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_votes_contest_user_unique
    ON votes(contest_id, user_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_votes_candidate_count
    ON votes(candidate_id) WHERE contest_id IS NOT NULL;

-- Contests jadali uchun
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contests_active_dates
    ON contests(is_active, is_archived, start_date, end_date)
    WHERE is_active = TRUE;

-- Candidates jadali uchun
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_candidates_contest_position
    ON candidates(contest_id, position);

-- Users jadali uchun
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_id_action
    ON users(user_id, last_action);

-- 5. MATERIALIZED VIEW (Real-time ovozlar uchun)
-- ============================================
DROP MATERIALIZED VIEW IF EXISTS vote_counts_cache;

CREATE MATERIALIZED VIEW vote_counts_cache AS
SELECT
    contest_id,
    candidate_id,
    COUNT(*) as vote_count,
    MAX(voted_at) as last_vote_time
FROM votes
GROUP BY contest_id, candidate_id;

-- Index on materialized view
CREATE INDEX idx_vote_counts_contest
    ON vote_counts_cache(contest_id);
CREATE INDEX idx_vote_counts_candidate
    ON vote_counts_cache(candidate_id);

-- Refresh function
CREATE OR REPLACE FUNCTION refresh_vote_counts()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY vote_counts_cache;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger (auto-refresh on vote)
DROP TRIGGER IF EXISTS trigger_refresh_vote_counts ON votes;
CREATE TRIGGER trigger_refresh_vote_counts
    AFTER INSERT OR DELETE ON votes
    FOR EACH STATEMENT
    EXECUTE FUNCTION refresh_vote_counts();

-- 6. PARTITIONING (future-proof, 1M+ votes uchun)
-- ============================================
-- Hozircha kerak emas, lekin kelajakda qo'shish mumkin
-- CREATE TABLE votes_2026 PARTITION OF votes
--     FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

-- 7. VACUUM & ANALYZE
-- ============================================
VACUUM ANALYZE votes;
VACUUM ANALYZE contests;
VACUUM ANALYZE candidates;
VACUUM ANALYZE users;

-- 8. STATISTICS
-- ============================================
ALTER TABLE votes ALTER COLUMN contest_id SET STATISTICS 1000;
ALTER TABLE votes ALTER COLUMN candidate_id SET STATISTICS 1000;
ALTER TABLE votes ALTER COLUMN user_id SET STATISTICS 1000;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Check table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check indexes
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Check performance stats
SELECT
    schemaname,
    tablename,
    seq_scan,
    idx_scan,
    n_tup_ins,
    n_tup_upd,
    n_tup_del
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY tablename;