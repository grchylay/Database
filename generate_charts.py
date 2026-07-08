#!/usr/bin/env python3
"""
Analysis Charts Generator — TSAR Monitoring Data
=================================================
Generates all charts and ER diagram for the assignment submission.

Output (all saved to /output/ folder):
  01_er_diagram.png         — ER relationship diagram
  02_timestamp_demo.png     — Timestamp conversion demonstration
  03_cpu_hourly_trend.png   — CPU usage hourly trend (5 hosts, 7 days)
  04_cpu_host_comparison.png— CPU comparison across all 20 hosts
  05_memory_overview.png    — Memory usage components (used/free/buff/cache)
  06_disk_util_trend.png    — Disk A utilization trend
  07_network_traffic.png    — Network inbound/outbound traffic
  08_load_average.png       — Load average (1min/5min/15min)
  09_hourly_aggregation.png — Before/after: 5-min raw → hourly summary
  10_dashboard.png          — Combined dashboard overview
"""

import sqlite3
import os
import sys
from datetime import datetime, timezone, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "tsar_monitor.db")
OUT_DIR  = os.path.join(BASE_DIR, "output")
os.makedirs(OUT_DIR, exist_ok=True)

# Style
plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "figure.titlesize": 15,
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
    "axes.unicode_minus": False,
})

COLORS = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3",
          "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD"]

BEIJING_TZ = timezone(timedelta(hours=8))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_conn():
    return sqlite3.connect(DB_PATH)


def save(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, bbox_inches="tight", facecolor="white", edgecolor="none")
    print(f"  [OK] {name}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Chart 1: ER Diagram
# ---------------------------------------------------------------------------

def draw_er_diagram():
    """Draw ER relationship diagram using matplotlib shapes."""
    fig, ax = plt.subplots(1, 1, figsize=(18, 10))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.set_facecolor("#FAFBFC")

    # --- Helper to draw a table box ---
    def table_box(x, y, w, h, title, fields, color, pk_rows=1):
        """Draw a beveled table box with title and field rows."""
        # Outer box
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                              facecolor=color, edgecolor="#333", linewidth=1.8, alpha=0.15)
        ax.add_patch(rect)
        rect2 = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                               facecolor="none", edgecolor="#333", linewidth=1.8)
        ax.add_patch(rect2)

        # Title bar
        title_bar = FancyBboxPatch((x + 0.04, y + h - 0.55), w - 0.08, 0.48,
                                    boxstyle="round,pad=0.04",
                                    facecolor=color, edgecolor="none", alpha=0.85)
        ax.add_patch(title_bar)
        ax.text(x + w/2, y + h - 0.31, title, ha="center", va="center",
                fontsize=11, fontweight="bold", color="white")

        # Fields
        for i, (field_name, field_type, is_pk, is_fk) in enumerate(fields):
            fy = y + h - 0.75 - i * 0.35
            prefix = ""
            if is_pk:
                prefix = "PK "
            elif is_fk:
                prefix = "FK "
            else:
                prefix = "   "
            text = f"{prefix}{field_name}  ({field_type})"
            fw = "bold" if (is_pk or is_fk) else "normal"
            fc = "#222" if (is_pk or is_fk) else "#444"
            ax.text(x + 0.2, fy, text, fontsize=8.5, fontweight=fw, color=fc,
                    fontfamily="monospace")

            if i < len(fields) - 1:
                ax.plot([x + 0.1, x + w - 0.1], [fy - 0.18, fy - 0.18],
                        color="#DDD", linewidth=0.5)

    def draw_arrow(x1, y1, x2, y2, label, curvature=0):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color="#E74C3C",
                                    lw=2.5, connectionstyle=f"arc3,rad={curvature}"))
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + curvature * 1.5
        ax.text(mx, my + 0.15, label, fontsize=9, color="#C0392B",
                ha="center", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.1", facecolor="#FFF3F3",
                          edgecolor="#E74C3C", alpha=0.85))

    # --- Draw the 4 tables ---
    # host_detail (left)
    table_box(0.3, 4.5, 3.2, 2.8, "host_detail (主机信息 — 20行)",
              [("hostid", "TEXT", True, False),
               ("hostname", "TEXT", False, False),
               ("owner", "TEXT", False, False),
               ("model", "TEXT", False, False),
               ("location1", "TEXT", False, False),
               ("location2", "TEXT", False, False)],
              "#4C72B0")

    # mod_detail (right top)
    table_box(13.5, 5.5, 3.5, 2.3, "mod_detail (指标字典 — 55行)",
              [("mod", "TEXT", True, False),
               ("type", "TEXT", False, False),
               ("description", "TEXT", False, False),
               ("unit", "TEXT", False, False),
               ("tag", "TEXT", False, False)],
              "#55A868")

    # tsar_detail (center, large)
    table_box(5.0, 1.0, 4.5, 4.3, "tsar_detail (采集明细 — 79,200行)",
              [("id", "INTEGER", True, False),
               ("ts_ms", "INTEGER", False, False),
               ("dt", "TEXT", False, False),
               ("hostid", "TEXT", False, True),
               ("type", "TEXT", False, False),
               ("mod", "TEXT", False, True),
               ("value", "REAL", False, False),
               ("tag", "TEXT", False, False)],
              "#DD8452")

    # tsar_hourly (bottom)
    table_box(6.0, 6.5, 4.8, 3.0, "tsar_hourly (小时汇总 — 79,096行)",
              [("hour_bucket", "TEXT", True, False),
               ("hostid", "TEXT", True, True),
               ("mod", "TEXT", True, True),
               ("avg_value", "REAL", False, False),
               ("max_value", "REAL", False, False),
               ("min_value", "REAL", False, False),
               ("sample_count", "INTEGER", False, False)],
              "#8172B3")

    # --- Draw relationship arrows ---
    # host_detail → tsar_detail (1:N on hostid)
    draw_arrow(3.5, 6.0, 5.0, 4.0, "1 : N\n(hostid)", curvature=-0.2)

    # mod_detail → tsar_detail (1:N on mod)
    draw_arrow(13.5, 6.8, 9.5, 4.2, "1 : N\n(mod)", curvature=0.2)

    # tsar_detail → tsar_hourly (aggregation)
    ax.annotate("", xy=(9.0, 6.5), xytext=(7.5, 5.3),
                arrowprops=dict(arrowstyle="->", color="#8E44AD", lw=2.5,
                                linestyle="dashed", connectionstyle="arc3,rad=0.1"))
    ax.text(8.9, 6.0, "汇总\nGROUP BY\n小时 + 主机 + 指标",
            fontsize=8, color="#6C3483", ha="center", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.1", facecolor="#F4ECF7",
                      edgecolor="#8E44AD", alpha=0.85))

    # --- Legend ---
    legend_items = [
        (mpatches.Patch(color="#E74C3C", alpha=0.7), "外键关联 (1:N)"),
        (mpatches.Patch(color="#8E44AD", alpha=0.7), "汇总聚合 (小时平均/最大/最小)"),
    ]
    legend_patches, legend_labels = zip(*legend_items)
    ax.legend(legend_patches, legend_labels, loc="lower right",
              fontsize=9, framealpha=0.9)

    # --- Title ---
    ax.text(9, 9.6, "TSAR 监控系统 — ER 实体关系图",
            ha="center", fontsize=19, fontweight="bold", color="#2C3E50")
    ax.text(9, 9.15, "disk_tsar.dat ∪ pref_tsar.dat → tsar_detail → tsar_hourly",
            ha="center", fontsize=10, color="#7F8C8D", style="italic")

    save(fig, "01_er_diagram.png")


# ---------------------------------------------------------------------------
# Chart 2: Timestamp Conversion Demo
# ---------------------------------------------------------------------------

def draw_timestamp_demo():
    """Visual demonstration of millisecond timestamp conversion."""
    fig, ax = plt.subplots(1, 1, figsize=(14, 5))
    ax.axis("off")
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 5)

    ts_examples = [
        (1782835200000, "2026-07-01 00:00:00", "数据起点"),
        (1782838800000, "2026-07-01 01:00:00", "1小时后"),
        (1782921600000, "2026-07-02 00:00:00", "1天后"),
        (1783436400000, "2026-07-07 23:00:00", "7天后 (pref终点)"),
        (1786434900000, "2026-08-11 15:55:00", "41天后 (disk终点)"),
    ]

    ax.text(7, 4.7, "[Timestamp] 时间戳转换：毫秒 -> 可读日期时间",
            ha="center", fontsize=16, fontweight="bold", color="#2C3E50")

    # Draw conversion steps
    for i, (ts_ms, dt_str, desc) in enumerate(ts_examples):
        y = 3.8 - i * 0.7

        # Step boxes
        bbox1 = dict(boxstyle="round,pad=0.3", facecolor="#FFF3E0", edgecolor="#E67E22", lw=1.5)
        bbox2 = dict(boxstyle="round,pad=0.3", facecolor="#E8F5E9", edgecolor="#27AE60", lw=1.5)

        ax.text(3.0, y, f"{ts_ms}", fontsize=12, fontweight="bold",
                ha="center", fontfamily="monospace", bbox=bbox1)
        ax.text(5.5, y, "→  ÷1000  →\n→  +8h   →", fontsize=9,
                ha="center", va="center", color="#E67E22", fontweight="bold")
        ax.text(9.0, y, dt_str, fontsize=12, fontweight="bold",
                ha="center", fontfamily="monospace", bbox=bbox2)
        ax.text(11.5, y, f"({desc})", fontsize=9, va="center", color="#7F8C8D")

        # Formula at bottom
        if i == 0:
            ax.annotate("毫秒数\n(13位整数)", xy=(3.0, y-0.6), fontsize=7.5,
                        ha="center", color="#E67E22")
            ax.annotate("北京时间\n(UTC+8)", xy=(9.0, y-0.6), fontsize=7.5,
                        ha="center", color="#27AE60")

    # Conversion formula
    ax.text(7, 0.25,
            "公式:  dt = datetime.fromtimestamp(ts_ms / 1000, tz=UTC).astimezone(UTC+8).strftime('%Y-%m-%d %H:%M:%S')",
            ha="center", fontsize=9, fontfamily="monospace",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#EBF5FB", edgecolor="#2980B9", alpha=0.7))

    save(fig, "02_timestamp_demo.png")


# ---------------------------------------------------------------------------
# Chart 3: CPU Hourly Trend (5 representative hosts, 7 days)
# ---------------------------------------------------------------------------

def draw_cpu_trend():
    """CPU usage over 7 days for 5 hosts."""
    conn = get_conn()
    hosts = ["host001", "host005", "host010", "host015", "host020"]
    fig, ax = plt.subplots(1, 1, figsize=(14, 6))

    for idx, host in enumerate(hosts):
        rows = conn.execute(
            "SELECT hour_bucket, avg_value FROM tsar_hourly "
            "WHERE mod='cpu_usage' AND hostid=? AND type='pref' "
            "ORDER BY hour_bucket",
            (host,)
        ).fetchall()
        if rows:
            x = [r[0] for r in rows]
            y = [r[1] for r in rows]
            # Show only first 168 hours (7 days)
            ax.plot(x[:168], y[:168], color=COLORS[idx], linewidth=1.2,
                    alpha=0.85, label=host)

    ax.set_title("CPU 综合使用率 — 小时趋势 (5台主机 × 7天)", fontweight="bold")
    ax.set_xlabel("时间")
    ax.set_ylabel("CPU 使用率 (%)")
    ax.legend(loc="upper right", ncol=5, fontsize=8)
    # Show fewer x-ticks
    n_ticks = min(14, len(ax.get_xticklabels()))
    step = max(1, 168 // n_ticks)
    ax.set_xticks(ax.get_xticks()[::step])
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=7)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_ylim(0, 100)

    # Add avg line
    avg = conn.execute("SELECT AVG(avg_value) FROM tsar_hourly WHERE mod='cpu_usage'").fetchone()[0]
    ax.axhline(avg, color="red", linestyle="--", linewidth=1, alpha=0.5,
               label=f"全局平均: {avg:.1f}%")
    ax.legend(loc="upper right", ncol=2, fontsize=8)

    conn.close()
    save(fig, "03_cpu_hourly_trend.png")


# ---------------------------------------------------------------------------
# Chart 4: CPU Host Comparison (bar chart)
# ---------------------------------------------------------------------------

def draw_cpu_host_comparison():
    """Average CPU usage per host as bar chart."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT hostid, ROUND(AVG(avg_value), 2) AS avg_cpu, "
        "ROUND(MAX(max_value), 2) AS peak_cpu "
        "FROM tsar_hourly WHERE mod='cpu_usage' "
        "GROUP BY hostid ORDER BY avg_cpu DESC"
    ).fetchall()
    conn.close()

    fig, ax = plt.subplots(1, 1, figsize=(14, 5))
    hostids = [r[0] for r in rows]
    avg_cpus = [r[1] for r in rows]
    peak_cpus = [r[2] for r in rows]

    x = np.arange(len(hostids))
    width = 0.35
    bars1 = ax.bar(x - width/2, avg_cpus, width, label="平均 CPU (%)", color="#4C72B0", alpha=0.85)
    bars2 = ax.bar(x + width/2, peak_cpus, width, label="峰值 CPU (%)", color="#C44E52", alpha=0.85)

    # Add value labels on bars
    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f"{bar.get_height():.1f}", ha="center", fontsize=5.5, fontweight="bold")
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f"{bar.get_height():.1f}", ha="center", fontsize=5.5, fontweight="bold")

    ax.set_title("CPU 使用率 — 20台主机对比 (平均 vs 峰值)", fontweight="bold")
    ax.set_xlabel("主机")
    ax.set_ylabel("CPU 使用率 (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(hostids, rotation=45, ha="right", fontsize=7)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, linestyle="--", axis="y")
    ax.set_ylim(0, max(peak_cpus) * 1.08)

    save(fig, "04_cpu_host_comparison.png")


# ---------------------------------------------------------------------------
# Chart 5: Memory Overview (host001)
# ---------------------------------------------------------------------------

def draw_memory_overview():
    """Memory components for host001 over time."""
    conn = get_conn()
    mem_mods = ["mem_used", "mem_free", "mem_buff", "mem_cache", "mem_swap"]
    colors_mem = ["#C44E52", "#55A868", "#4C72B0", "#DD8452", "#8172B3"]

    fig, ax = plt.subplots(1, 1, figsize=(14, 6))

    for mod, color in zip(mem_mods, colors_mem):
        rows = conn.execute(
            "SELECT hour_bucket, avg_value FROM tsar_hourly "
            "WHERE mod=? AND hostid='host001' ORDER BY hour_bucket LIMIT 168",
            (mod,)
        ).fetchall()
        if rows:
            x = [r[0] for r in rows]
            y = [r[1] for r in rows]
            ax.plot(x, y, color=color, linewidth=1.2, alpha=0.85, label=mod)

    ax.set_title("内存使用 — host001 各组件趋势 (7天)", fontweight="bold")
    ax.set_xlabel("时间")
    ax.set_ylabel("内存 (MB)")
    ax.legend(loc="upper right", ncol=5, fontsize=8)
    step = max(1, 168 // 14)
    ax.set_xticks(ax.get_xticks()[::step])
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=7)
    ax.grid(True, alpha=0.3, linestyle="--")

    conn.close()
    save(fig, "05_memory_overview.png")


# ---------------------------------------------------------------------------
# Chart 6: Disk Utilization Trend (sda_util)
# ---------------------------------------------------------------------------

def draw_disk_util():
    """Disk A utilization for top 5 hosts (hourly aggregated)."""
    conn = get_conn()
    # Find top 5 hosts by peak disk util
    top_hosts = [r[0] for r in conn.execute(
        "SELECT hostid FROM tsar_hourly WHERE mod='sda_util' "
        "GROUP BY hostid ORDER BY MAX(max_value) DESC LIMIT 5"
    ).fetchall()]

    fig, ax = plt.subplots(1, 1, figsize=(14, 5.5))

    for idx, host in enumerate(top_hosts):
        rows = conn.execute(
            "SELECT hour_bucket, avg_value FROM tsar_hourly "
            "WHERE mod='sda_util' AND hostid=? ORDER BY hour_bucket",
            (host,)
        ).fetchall()
        if rows:
            x = [r[0] for r in rows]
            y = [r[1] for r in rows]
            ax.plot(x, y, color=COLORS[idx], linewidth=1.0, alpha=0.8,
                    label=host, marker=".", markersize=1.5)

    ax.set_title("磁盘A使用率 (sda_util) — 峰值最高的5台主机", fontweight="bold")
    ax.set_xlabel("时间")
    ax.set_ylabel("磁盘使用率 (%)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, linestyle="--")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=7)
    ax.set_ylim(0, 105)

    conn.close()
    save(fig, "06_disk_util_trend.png")


# ---------------------------------------------------------------------------
# Chart 7: Network Traffic (host001)
# ---------------------------------------------------------------------------

def draw_network_traffic():
    """Network inbound/outbound for host001."""
    conn = get_conn()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7))

    # Bandwidth
    for mod, color, label in [("net_in", "#4C72B0", "入站 net_in"),
                               ("net_out", "#C44E52", "出站 net_out")]:
        rows = conn.execute(
            "SELECT hour_bucket, avg_value FROM tsar_hourly "
            "WHERE mod=? AND hostid='host001' ORDER BY hour_bucket LIMIT 168",
            (mod,)
        ).fetchall()
        if rows:
            x = [r[0] for r in rows]
            y = [r[1] for r in rows]
            ax1.plot(x, y, color=color, linewidth=1.2, alpha=0.85, label=label)

    ax1.set_title("网络带宽 — host001 (入站/出站 MB/s)", fontweight="bold")
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3, linestyle="--")
    step = max(1, 168 // 14)
    ax1.set_xticks(ax1.get_xticks()[::step])
    plt.setp(ax1.get_xticklabels(), rotation=30, ha="right", fontsize=7)

    # Packets
    for mod, color, label in [("net_pktin", "#55A868", "入站 net_pktin"),
                               ("net_pktout", "#DD8452", "出站 net_pktout")]:
        rows = conn.execute(
            "SELECT hour_bucket, avg_value FROM tsar_hourly "
            "WHERE mod=? AND hostid='host001' ORDER BY hour_bucket LIMIT 168",
            (mod,)
        ).fetchall()
        if rows:
            x = [r[0] for r in rows]
            y = [r[1] for r in rows]
            ax2.plot(x, y, color=color, linewidth=1.2, alpha=0.85, label=label)

    ax2.set_title("网络数据包 — host001 (入站/出站 pkt/s)", fontweight="bold")
    ax2.set_xlabel("时间")
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3, linestyle="--")
    ax2.set_xticks(ax2.get_xticks()[::step])
    plt.setp(ax2.get_xticklabels(), rotation=30, ha="right", fontsize=7)

    plt.tight_layout()
    conn.close()
    save(fig, "07_network_traffic.png")


# ---------------------------------------------------------------------------
# Chart 8: Load Average (host001)
# ---------------------------------------------------------------------------

def draw_load_average():
    """Load 1/5/15 for host001."""
    conn = get_conn()

    fig, ax = plt.subplots(1, 1, figsize=(14, 5))
    colors_load = {"load1": "#4C72B0", "load5": "#DD8452", "load15": "#C44E52"}

    for mod, color in colors_load.items():
        rows = conn.execute(
            "SELECT hour_bucket, avg_value FROM tsar_hourly "
            "WHERE mod=? AND hostid='host001' ORDER BY hour_bucket LIMIT 168",
            (mod,)
        ).fetchall()
        if rows:
            x = [r[0] for r in rows]
            y = [r[1] for r in rows]
            ax.plot(x, y, color=color, linewidth=1.2, alpha=0.85, label=mod)

    ax.set_title("系统负载 — host001 (load1 / load5 / load15)", fontweight="bold")
    ax.set_xlabel("时间")
    ax.set_ylabel("平均负载")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, linestyle="--")
    step = max(1, 168 // 14)
    ax.set_xticks(ax.get_xticks()[::step])
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=7)

    conn.close()
    save(fig, "08_load_average.png")


# ---------------------------------------------------------------------------
# Chart 9: Hourly Aggregation Demo
# ---------------------------------------------------------------------------

def draw_hourly_aggregation_demo():
    """Show 5-min raw data → hourly summary transformation."""
    conn = get_conn()

    # Get raw disk data for a specific host/mod/hour
    rows_raw = conn.execute(
        "SELECT dt, value FROM tsar_detail "
        "WHERE hostid='host001' AND mod='sda_util' AND type='disk' "
        "AND dt >= '2026-07-01 00:00:00' AND dt < '2026-07-01 06:00:00' "
        "ORDER BY dt"
    ).fetchall()

    rows_hourly = conn.execute(
        "SELECT hour_bucket, avg_value, max_value, min_value, sample_count "
        "FROM tsar_hourly WHERE hostid='host001' AND mod='sda_util' "
        "AND hour_bucket >= '2026-07-01 00:00:00' "
        "AND hour_bucket < '2026-07-01 06:00:00' "
        "ORDER BY hour_bucket"
    ).fetchall()
    conn.close()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), gridspec_kw={"height_ratios": [1, 1]})

    # Top: raw data points
    if rows_raw:
        times = [datetime.strptime(r[0], "%Y-%m-%d %H:%M:%S") for r in rows_raw]
        values = [r[1] for r in rows_raw]
        ax1.scatter(times, values, c="#DD8452", s=30, alpha=0.7, edgecolors="#333", linewidth=0.3)
        ax1.plot(times, values, color="#DD8452", alpha=0.3, linewidth=0.8)
        ax1.set_title("原始数据 — disk_tsar (每5分钟采样, sda_util)", fontweight="bold")
        ax1.set_ylabel("磁盘使用率 (%)")

    # Mark hour boundaries
    for h in range(0, 7):
        boundary = datetime(2026, 7, 1, h, 0, 0)
        ax1.axvline(boundary, color="#E74C3C", linestyle="--", linewidth=0.6, alpha=0.4)

    ax1.grid(True, alpha=0.3, linestyle="--")

    # Bottom: hourly summary bars + range
    if rows_hourly:
        hours = [datetime.strptime(r[0], "%Y-%m-%d %H:%M:%S") for r in rows_hourly]
        avgs = [r[1] for r in rows_hourly]
        maxs = [r[2] for r in rows_hourly]
        mins = [r[3] for r in rows_hourly]
        counts = [r[4] for r in rows_hourly]

        bar_width = timedelta(minutes=40)
        ax2.bar(hours, avgs, width=bar_width, color="#4C72B0", alpha=0.7,
                label="平均值", edgecolor="#333", linewidth=0.5)
        # Error bars showing range
        yerr_low = [avgs[i] - mins[i] for i in range(len(avgs))]
        yerr_high = [maxs[i] - avgs[i] for i in range(len(avgs))]
        ax2.errorbar(hours, avgs, yerr=[yerr_low, yerr_high],
                     fmt="none", ecolor="#C44E52", capsize=4, linewidth=1.5,
                     label="最大值/最小值范围")

        # Sample count annotations
        for h, c in zip(hours, counts):
            ax2.annotate(f"n={c}", xy=(h, maxs[maxs.index(
                [x for x, h2 in zip(avgs, hours) if h2 == h][0]
            )] + 0.3 if maxs else 0),
                         fontsize=8, ha="center", color="#555")

        ax2.set_title("小时汇总 — tsar_hourly (AVG / MAX / MIN / COUNT)", fontweight="bold")
        ax2.set_xlabel("时间")
        ax2.set_ylabel("磁盘使用率 (%)")
        ax2.legend(fontsize=9)
        ax2.grid(True, alpha=0.3, linestyle="--", axis="y")

    plt.tight_layout()
    save(fig, "09_hourly_aggregation_demo.png")


# ---------------------------------------------------------------------------
# Chart 10: Dashboard Overview
# ---------------------------------------------------------------------------

def draw_dashboard():
    """Combined dashboard: 4-panel overview of key metrics."""
    conn = get_conn()
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    # Panel 1: CPU usage (all hosts, avg)
    rows = conn.execute(
        "SELECT hour_bucket, ROUND(AVG(avg_value), 2) FROM tsar_hourly "
        "WHERE mod='cpu_usage' GROUP BY hour_bucket ORDER BY hour_bucket LIMIT 168"
    ).fetchall()
    if rows:
        x = [r[0] for r in rows]
        y = [r[1] for r in rows]
        axes[0, 0].fill_between(range(len(y)), y, alpha=0.3, color="#4C72B0")
        axes[0, 0].plot(range(len(y)), y, color="#4C72B0", linewidth=1.5)
        axes[0, 0].axhline(np.mean(y), color="red", linestyle="--", linewidth=1, alpha=0.6)
        axes[0, 0].set_title("CPU 综合使用率 (20台均值)", fontweight="bold")
        axes[0, 0].set_ylabel("%")
        axes[0, 0].grid(True, alpha=0.3, linestyle="--")
        step = max(1, len(y) // 10)
        axes[0, 0].set_xticks(range(0, len(y), step))
        axes[0, 0].set_xticklabels([x[i][5:10] for i in range(0, len(x), step)],
                                    rotation=30, fontsize=7)

    # Panel 2: Top 5 disk util hosts (max)
    rows = conn.execute(
        "SELECT hostid, MAX(max_value) FROM tsar_hourly "
        "WHERE mod='sda_util' GROUP BY hostid ORDER BY MAX(max_value) DESC LIMIT 10"
    ).fetchall()
    if rows:
        hosts = [r[0] for r in rows]
        vals = [r[1] for r in rows]
        colors_bar = ["#C44E52" if v > 90 else "#DD8452" if v > 80 else "#4C72B0" for v in vals]
        axes[0, 1].barh(hosts, vals, color=colors_bar, alpha=0.85, edgecolor="#333", linewidth=0.3)
        axes[0, 1].set_title("磁盘A峰值使用率 Top 10", fontweight="bold")
        axes[0, 1].set_xlabel("%")
        axes[0, 1].grid(True, alpha=0.3, linestyle="--", axis="x")
        axes[0, 1].invert_yaxis()

    # Panel 3: Process counts (host001)
    for mod, color, label in [("proc_total", "#4C72B0", "总进程"),
                               ("proc_run", "#55A868", "运行中"),
                               ("proc_block", "#C44E52", "阻塞")]:
        rows = conn.execute(
            "SELECT hour_bucket, avg_value FROM tsar_hourly "
            "WHERE mod=? AND hostid='host001' ORDER BY hour_bucket LIMIT 168",
            (mod,)
        ).fetchall()
        if rows:
            y = [r[1] for r in rows]
            axes[1, 0].plot(range(len(y)), y, color=color, linewidth=1.2, alpha=0.85, label=label)
    axes[1, 0].set_title("进程数 — host001", fontweight="bold")
    axes[1, 0].set_ylabel("个")
    axes[1, 0].legend(fontsize=8)
    axes[1, 0].grid(True, alpha=0.3, linestyle="--")
    step = max(1, 168 // 10)
    axes[1, 0].set_xticks(range(0, 168, step))
    axes[1, 0].set_xticklabels([f"7/{1+i//24:02d}" for i in range(0, 168, step)],
                                rotation=30, fontsize=7)

    # Panel 4: Metric type distribution
    rows = conn.execute(
        "SELECT type, COUNT(*) FROM tsar_detail GROUP BY type"
    ).fetchall()
    labels = ["disk (磁盘)", "pref (性能)"]
    sizes = [r[1] for r in rows]
    colors_pie = ["#DD8452", "#4C72B0"]
    wedges, texts, autotexts = axes[1, 1].pie(
        sizes, labels=labels, autopct="%1.1f%%", colors=colors_pie,
        explode=(0.03, 0.03), startangle=90, textprops={"fontsize": 10})
    for at in autotexts:
        at.set_fontweight("bold")
    axes[1, 1].set_title("数据分布 (disk vs pref)", fontweight="bold")

    fig.suptitle("TSAR 监控系统 — 数据概览仪表盘", fontsize=18, fontweight="bold", y=1.01)
    plt.tight_layout()
    conn.close()
    save(fig, "10_dashboard.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  Generating Analysis Charts & ER Diagram")
    print("=" * 60)
    print()

    draw_er_diagram()
    draw_timestamp_demo()
    draw_cpu_trend()
    draw_cpu_host_comparison()
    draw_memory_overview()
    draw_disk_util()
    draw_network_traffic()
    draw_load_average()
    draw_hourly_aggregation_demo()
    draw_dashboard()

    print()
    print(f"All charts saved to: {OUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
