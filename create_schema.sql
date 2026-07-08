-- ============================================================================
-- TSAR Monitoring Database Schema
-- Server: SQLite 3
-- Timezone: UTC+8 (Beijing Time) — timestamps stored as milliseconds from epoch
-- ============================================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. Dimension Tables
-- ----------------------------------------------------------------------------

-- Host detail: server inventory (20 servers across 5 locations)
DROP TABLE IF EXISTS host_detail;
CREATE TABLE host_detail (
    hostid      TEXT PRIMARY KEY,
    hostname    TEXT NOT NULL,
    owner       TEXT NOT NULL,
    model       TEXT NOT NULL,
    location1   TEXT NOT NULL,          -- data center room (A/B/C/D/E)
    location2   TEXT NOT NULL           -- rack number
);

-- Metric dictionary: 35 disk + 20 performance = 55 metrics
DROP TABLE IF EXISTS mod_detail;
CREATE TABLE mod_detail (
    mod         TEXT PRIMARY KEY,       -- metric code (e.g., sda_util, cpu_user)
    type        TEXT NOT NULL,          -- 'disk' or 'pref'
    description TEXT NOT NULL,          -- Chinese description
    unit        TEXT,                   -- %, MB, MB/s, ms, req/s, sectors/s, pkt/s, etc.
    tag         TEXT NOT NULL,          -- metric category tag
    CHECK (type IN ('disk', 'pref'))
);

-- ----------------------------------------------------------------------------
-- 2. Fact Table: unified monitoring data
-- ----------------------------------------------------------------------------

DROP TABLE IF EXISTS tsar_detail;
CREATE TABLE tsar_detail (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms       INTEGER NOT NULL,       -- original Unix timestamp (milliseconds)
    dt          TEXT NOT NULL,          -- converted datetime (YYYY-MM-DD HH:MM:SS, UTC+8)
    hostid      TEXT NOT NULL,
    type        TEXT NOT NULL,          -- 'disk' or 'pref'
    mod         TEXT NOT NULL,
    value       REAL NOT NULL,          -- numeric metric value
    tag         TEXT NOT NULL,
    FOREIGN KEY (hostid) REFERENCES host_detail(hostid),
    FOREIGN KEY (mod)   REFERENCES mod_detail(mod)
);

-- Indexes for common query patterns
CREATE INDEX idx_tsar_dt      ON tsar_detail(dt);
CREATE INDEX idx_tsar_hostid  ON tsar_detail(hostid);
CREATE INDEX idx_tsar_mod     ON tsar_detail(mod);
CREATE INDEX idx_tsar_type_dt ON tsar_detail(type, dt);
CREATE INDEX idx_tsar_host_mod ON tsar_detail(hostid, mod);

-- ----------------------------------------------------------------------------
-- 3. Hourly Summary View (long format)
--    Aggregates disk 5-min samples and pref hourly samples into uniform
--    hourly buckets with AVG / MAX / MIN / COUNT
-- ----------------------------------------------------------------------------

DROP VIEW IF EXISTS v_tsar_hourly;
CREATE VIEW v_tsar_hourly AS
SELECT
    strftime('%Y-%m-%d %H:00:00', dt) AS hour_bucket,
    hostid,
    type,
    mod,
    tag,
    ROUND(AVG(value), 4)  AS avg_value,
    ROUND(MAX(value), 4)  AS max_value,
    ROUND(MIN(value), 4)  AS min_value,
    COUNT(*)              AS sample_count
FROM tsar_detail
GROUP BY hour_bucket, hostid, type, mod;

-- ----------------------------------------------------------------------------
-- 4. Materialized Hourly Summary Table (optional, for faster repeated queries)
-- ----------------------------------------------------------------------------

DROP TABLE IF EXISTS tsar_hourly;
CREATE TABLE tsar_hourly (
    hour_bucket  TEXT NOT NULL,         -- YYYY-MM-DD HH:00:00
    hostid       TEXT NOT NULL,
    type         TEXT NOT NULL,
    mod          TEXT NOT NULL,
    tag          TEXT NOT NULL,
    avg_value    REAL,
    max_value    REAL,
    min_value    REAL,
    sample_count INTEGER,
    PRIMARY KEY (hour_bucket, hostid, mod)
);
CREATE INDEX idx_hourly_dt   ON tsar_hourly(hour_bucket);
CREATE INDEX idx_hourly_host ON tsar_hourly(hostid);
CREATE INDEX idx_hourly_mod  ON tsar_hourly(mod);

-- ----------------------------------------------------------------------------
-- 5. Wide-Format Hourly View (pivoted: one column per key metric)
--    Useful for dashboard/report queries — one row per host per hour
-- ----------------------------------------------------------------------------

DROP VIEW IF EXISTS v_hourly_wide;
CREATE VIEW v_hourly_wide AS
SELECT
    h.hour_bucket,
    h.hostid,
    hd.hostname,
    hd.owner,
    hd.location1,
    hd.location2,
    -- CPU metrics (%)
    MAX(CASE WHEN h.mod = 'cpu_user'   THEN h.avg_value END) AS cpu_user,
    MAX(CASE WHEN h.mod = 'cpu_sys'    THEN h.avg_value END) AS cpu_sys,
    MAX(CASE WHEN h.mod = 'cpu_wait'   THEN h.avg_value END) AS cpu_wait,
    MAX(CASE WHEN h.mod = 'cpu_idle'   THEN h.avg_value END) AS cpu_idle,
    MAX(CASE WHEN h.mod = 'cpu_usage'  THEN h.avg_value END) AS cpu_usage,
    -- Memory metrics (MB)
    MAX(CASE WHEN h.mod = 'mem_used'   THEN h.avg_value END) AS mem_used,
    MAX(CASE WHEN h.mod = 'mem_free'   THEN h.avg_value END) AS mem_free,
    MAX(CASE WHEN h.mod = 'mem_buff'   THEN h.avg_value END) AS mem_buff,
    MAX(CASE WHEN h.mod = 'mem_cache'  THEN h.avg_value END) AS mem_cache,
    MAX(CASE WHEN h.mod = 'mem_swap'   THEN h.avg_value END) AS mem_swap,
    -- Network metrics (MB/s, pkt/s)
    MAX(CASE WHEN h.mod = 'net_in'     THEN h.avg_value END) AS net_in,
    MAX(CASE WHEN h.mod = 'net_out'    THEN h.avg_value END) AS net_out,
    MAX(CASE WHEN h.mod = 'net_pktin'  THEN h.avg_value END) AS net_pktin,
    MAX(CASE WHEN h.mod = 'net_pktout' THEN h.avg_value END) AS net_pktout,
    -- Load average
    MAX(CASE WHEN h.mod = 'load1'      THEN h.avg_value END) AS load1,
    MAX(CASE WHEN h.mod = 'load5'      THEN h.avg_value END) AS load5,
    MAX(CASE WHEN h.mod = 'load15'     THEN h.avg_value END) AS load15,
    -- Process counts
    MAX(CASE WHEN h.mod = 'proc_run'   THEN h.avg_value END) AS proc_run,
    MAX(CASE WHEN h.mod = 'proc_block' THEN h.avg_value END) AS proc_block,
    MAX(CASE WHEN h.mod = 'proc_total' THEN h.avg_value END) AS proc_total,
    -- Disk sda_util (disk A utilization, %) — representative disk metric
    MAX(CASE WHEN h.mod = 'sda_util'   THEN h.avg_value END) AS sda_util,
    MAX(CASE WHEN h.mod = 'sda_await'  THEN h.avg_value END) AS sda_await_ms,
    MAX(CASE WHEN h.mod = 'sda_read'   THEN h.avg_value END) AS sda_read_sectors,
    MAX(CASE WHEN h.mod = 'sda_write'  THEN h.avg_value END) AS sda_write_sectors
FROM v_tsar_hourly h
JOIN host_detail hd ON h.hostid = hd.hostid
GROUP BY h.hour_bucket, h.hostid;

-- ============================================================================
-- End of schema
-- ============================================================================
