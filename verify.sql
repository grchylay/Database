-- ============================================================================
-- Verification Queries — TSAR Monitoring Database
-- Usage:  sqlite3 tsar_monitor.db < verify.sql
-- ============================================================================

.headers on
.mode column
.width 30 12 12

.print
.print ============================================================
.print   1. Row Count Checks
.print ============================================================

SELECT 'host_detail'  AS table_name, COUNT(*) AS row_count FROM host_detail
UNION ALL
SELECT 'mod_detail',   COUNT(*) FROM mod_detail
UNION ALL
SELECT 'tsar_detail',  COUNT(*) FROM tsar_detail
UNION ALL
SELECT 'tsar_hourly',  COUNT(*) FROM tsar_hourly;

-- Expected: host_detail=20, mod_detail=55, tsar_detail=79,200, tsar_hourly=0 (before materialize)

.print
.print ============================================================
.print   2. Time Range Validation
.print ============================================================

SELECT 'disk_min_dt' AS label, MIN(dt) AS value FROM tsar_detail WHERE type='disk'
UNION ALL
SELECT 'disk_max_dt',       MAX(dt) FROM tsar_detail WHERE type='disk'
UNION ALL
SELECT 'pref_min_dt',       MIN(dt) FROM tsar_detail WHERE type='pref'
UNION ALL
SELECT 'pref_max_dt',       MAX(dt) FROM tsar_detail WHERE type='pref';

-- Verify timestamp conversion (spot check: first 3 rows)
.print
.print ============================================================
.print   3. Timestamp Conversion Spot Check (first 5 rows)
.print ============================================================

SELECT ts_ms, dt, hostid, type, mod, value
FROM tsar_detail
ORDER BY ts_ms, hostid, mod
LIMIT 5;

-- Verify ts_ms → dt conversion with a known value:
-- 1782835200000 ms should convert to 2026-07-01 00:00:00 (UTC+8)
.print
SELECT '1782835200000 ms →'
       || ' ' || datetime(1782835200, 'unixepoch', '+8 hours')
       AS timestamp_conversion_check;

.print
.print ============================================================
.print   4. Distribution: Records per Host (top 10 + total)
.print ============================================================

SELECT hostid, COUNT(*) AS records
FROM tsar_detail
GROUP BY hostid
ORDER BY records DESC
LIMIT 10;

SELECT 'TOTAL' AS hostid, COUNT(*) AS records FROM tsar_detail;

.print
.print ============================================================
.print   5. Distribution: Records per Metric Type
.print ============================================================

SELECT type, COUNT(*) AS records, COUNT(DISTINCT mod) AS unique_mods
FROM tsar_detail
GROUP BY type;

.print
.print ============================================================
.print   6. Unique Timestamps per Type
.print    (disk = ~12,000 unique 5-min slots; pref = ~168 hourly slots)
.print ============================================================

SELECT type, COUNT(DISTINCT ts_ms) AS unique_ts,
       MIN(dt) AS min_dt, MAX(dt) AS max_dt
FROM tsar_detail
GROUP BY type;

.print
.print ============================================================
.print   7. Data Completeness: Missing host-mod combos per type
.print ============================================================

SELECT 'disk' AS type,
       (20 * 35) - COUNT(DISTINCT hostid || '|' || mod) AS missing_combos
FROM tsar_detail WHERE type='disk'
UNION ALL
SELECT 'pref',
       (20 * 20) - COUNT(DISTINCT hostid || '|' || mod)
FROM tsar_detail WHERE type='pref';

.print
.print ============================================================
.print   8. Hourly View Sample (cpu_usage for host001, first 10 hours)
.print ============================================================

SELECT hour_bucket, hostid, mod,
       avg_value, max_value, min_value, sample_count
FROM v_tsar_hourly
WHERE hostid = 'host001' AND mod = 'cpu_usage'
ORDER BY hour_bucket
LIMIT 10;

.print
.print ============================================================
.print   9. Wide-Format View Sample (first 5 rows)
.print ============================================================

SELECT hour_bucket, hostid, hostname, location1,
       cpu_usage, mem_used, net_in, net_out, load1, proc_total
FROM v_hourly_wide
ORDER BY hour_bucket, hostid
LIMIT 5;

.print
.print ============================================================
.print   Verification Complete
.print ============================================================
