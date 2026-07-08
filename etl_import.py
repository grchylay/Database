#!/usr/bin/env python3
"""
ETL Import Script — TSAR Monitoring Data
=========================================
Reads 4 TSV data files, converts millisecond timestamps to readable datetimes,
and imports everything into a SQLite database with the schema from create_schema.sql.

Usage:
    python etl_import.py

Output:
    tsar_monitor.db — SQLite database with all tables, indexes, and views
"""

import csv
import sqlite3
import os
import time
from datetime import datetime, timezone, timedelta

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = BASE_DIR  # all .dat files are here

# Beijing timezone (UTC+8) — all timestamps rendered in local time
BEIJING_TZ = timezone(timedelta(hours=8))

# Files to import (order matters for FK constraints)
FILES = {
    "host_detail": os.path.join(DATA_DIR, "host_detail.dat"),
    "mod_detail":  os.path.join(DATA_DIR, "mod_detail.dat"),
    "disk_tsar":   os.path.join(DATA_DIR, "disk_tsar.dat"),
    "pref_tsar":   os.path.join(DATA_DIR, "pref_tsar.dat"),
}

SCHEMA_FILE = os.path.join(DATA_DIR, "create_schema.sql")
DB_PATH     = os.path.join(DATA_DIR, "tsar_monitor.db")

BATCH_SIZE  = 10_000  # rows per batch insert


# ---------------------------------------------------------------------------
# Timestamp conversion
# ---------------------------------------------------------------------------

def ms_to_datetime(ts_ms: int) -> str:
    """
    Convert a Unix timestamp in milliseconds to a Beijing-time datetime string.

    Args:
        ts_ms: epoch milliseconds (e.g., 1782835200000)

    Returns:
        ISO-format datetime string: 'YYYY-MM-DD HH:MM:SS'
    """
    ts_sec = ts_ms / 1000.0
    dt_utc = datetime.fromtimestamp(ts_sec, tz=timezone.utc)
    dt_beijing = dt_utc.astimezone(BEIJING_TZ)
    return dt_beijing.strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# Schema execution
# ---------------------------------------------------------------------------

def execute_schema(conn: sqlite3.Connection) -> None:
    """Read create_schema.sql and execute it against the database."""
    print(f"[SCHEMA] Loading schema from {SCHEMA_FILE} ...")
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        sql = f.read()
    conn.executescript(sql)
    conn.commit()
    print("[SCHEMA] Schema created successfully.")


# ---------------------------------------------------------------------------
# Dimension tables (small, direct insert)
# ---------------------------------------------------------------------------

def load_host_detail(conn: sqlite3.Connection) -> int:
    """Load host_detail.dat into host_detail table. Returns row count."""
    path = FILES["host_detail"]
    print(f"[HOST] Loading {path} ...")
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = list(reader)  # only 20 rows, safe to load all
    conn.executemany(
        "INSERT INTO host_detail (hostid, hostname, owner, model, location1, location2) "
        "VALUES (:hostid, :hostname, :owner, :model, :location1, :location2)",
        rows,
    )
    conn.commit()
    print(f"[HOST] {len(rows)} rows inserted.")
    return len(rows)


def load_mod_detail(conn: sqlite3.Connection) -> int:
    """Load mod_detail.dat into mod_detail table. Returns row count."""
    path = FILES["mod_detail"]
    print(f"[MOD]  Loading {path} ...")
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = list(reader)  # only 55 rows
    conn.executemany(
        "INSERT INTO mod_detail (mod, type, description, unit, tag) "
        "VALUES (:mod, :type, :desc, :unit, :tag)",
        rows,
    )
    conn.commit()
    print(f"[MOD]  {len(rows)} rows inserted.")
    return len(rows)


# ---------------------------------------------------------------------------
# Fact table (large, batched)
# ---------------------------------------------------------------------------

def load_tsar_file(conn: sqlite3.Connection, file_key: str) -> tuple[int, str, str]:
    """
    Load a tsar detail file (disk_tsar or pref_tsar) in batches.
    Converts timestamp from milliseconds to datetime string on the fly.

    Returns:
        (row_count, min_dt, max_dt)
    """
    path = FILES[file_key]
    print(f"[TSAR] Loading {os.path.basename(path)} (batch size={BATCH_SIZE}) ...")

    sql = (
        "INSERT INTO tsar_detail (ts_ms, dt, hostid, type, mod, value, tag) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)"
    )

    batch = []
    total = 0
    min_dt = None
    max_dt = None

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            ts_ms = int(row["ts"])
            dt_str = ms_to_datetime(ts_ms)

            batch.append((
                ts_ms,
                dt_str,
                row["hostid"],
                row["type"],
                row["mod"],
                float(row["value"]),
                row["tag"],
            ))

            # Track dt range
            if min_dt is None or dt_str < min_dt:
                min_dt = dt_str
            if max_dt is None or dt_str > max_dt:
                max_dt = dt_str

            # Flush batch when full
            if len(batch) >= BATCH_SIZE:
                conn.executemany(sql, batch)
                total += len(batch)
                batch.clear()
                print(f"  ... {total:,} rows imported")

    # Flush remaining
    if batch:
        conn.executemany(sql, batch)
        total += len(batch)

    conn.commit()
    print(f"[TSAR] {os.path.basename(path)}: {total:,} rows | dt range: {min_dt} → {max_dt}")
    return total, min_dt, max_dt


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    start_time = time.time()

    # Remove existing database so we start fresh
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"[INIT] Removed existing {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = OFF")        # faster bulk loading
    conn.execute("PRAGMA cache_size = -64000")       # 64 MB cache
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        # 1. Create schema
        execute_schema(conn)

        # 2. Load dimension tables
        n_hosts = load_host_detail(conn)
        n_mods  = load_mod_detail(conn)

        # 3. Load fact tables
        n_disk, disk_min, disk_max = load_tsar_file(conn, "disk_tsar")
        n_pref, pref_min, pref_max = load_tsar_file(conn, "pref_tsar")

        # 4. Optimize
        print("[STAT] Running ANALYZE ...")
        conn.execute("ANALYZE")
        conn.commit()

        # 5. Summary
        elapsed = time.time() - start_time
        total_tsar = n_disk + n_pref
        print()
        print("=" * 62)
        print("  IMPORT SUMMARY")
        print("=" * 62)
        print(f"  host_detail   : {n_hosts:>6} rows")
        print(f"  mod_detail    : {n_mods:>6} rows")
        print(f"  disk_tsar     : {n_disk:>6} rows  ({disk_min} → {disk_max})")
        print(f"  pref_tsar     : {n_pref:>6} rows  ({pref_min} → {pref_max})")
        print(f"  tsar_detail   : {total_tsar:>6} rows total")
        print(f"  Database      : {os.path.getsize(DB_PATH) / 1024 / 1024:.1f} MB")
        print(f"  Elapsed       : {elapsed:.2f}s")
        print("=" * 62)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
