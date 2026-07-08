#!/usr/bin/env python3
"""
ER Diagram — matching the reference style.
Left-right split layout, table boxes with PK/FK markers, 1:N arrows.
"""
import os, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Global Style ──────────────────────────────────────────────
plt.rcParams.update({
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "font.size": 10,
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial"],
    "axes.unicode_minus": False,
})

# ── Drawing helpers ───────────────────────────────────────────

class TableBox:
    """Represents one entity table box."""
    def __init__(self, ax, x, y, w, h, title, fields, color="#5B9BD5"):
        self.ax = ax
        self.x, self.y, self.w, self.h = x, y, w, h
        self.title = title
        self.fields = fields  # list of (name, type_, marker)  marker='PK'|'FK'|''
        self.color = color

    def draw(self):
        x, y, w, h = self.x, self.y, self.w, self.h
        ax = self.ax

        # Title bar
        title_h = 0.45
        title_bar = FancyBboxPatch(
            (x, y + h - title_h), w, title_h,
            boxstyle="round,pad=0.02", facecolor=self.color,
            edgecolor=self.color, alpha=0.92
        )
        ax.add_patch(title_bar)
        ax.text(x + w/2, y + h - title_h/2, self.title,
                ha="center", va="center", fontsize=10.5, fontweight="bold",
                color="white")

        # Outer border (below title)
        border = FancyBboxPatch(
            (x, y), w, h - title_h,
            boxstyle="round,pad=0.02", facecolor="white",
            edgecolor="#888888", linewidth=1.2
        )
        ax.add_patch(border)

        # Field rows
        field_start_y = y + h - title_h - 0.08
        row_h = 0.34
        for i, (fname, ftype, marker) in enumerate(self.fields):
            fy = field_start_y - i * row_h
            # Separator line
            if i > 0:
                ax.plot([x + 0.08, x + w - 0.08], [fy + row_h/2 + 0.15, fy + row_h/2 + 0.15],
                        color="#DDD", linewidth=0.5)

            # Marker
            if marker:
                mk_color = "#D2691E" if marker == "PK" else "#4C72B0"
                ax.text(x + 0.12, fy, marker, fontsize=7, fontweight="bold",
                        color=mk_color, va="center", fontfamily="monospace")

            # Field name
            ax.text(x + (0.38 if marker else 0.12), fy, fname,
                    fontsize=8, fontweight="bold", color="#222",
                    va="center", fontfamily="monospace")

            # Field type
            ax.text(x + w - 0.12, fy, ftype,
                    fontsize=7, color="#888", va="center", ha="right",
                    fontfamily="monospace")

    @property
    def right(self): return self.x + self.w
    @property
    def left(self): return self.x
    @property
    def top(self): return self.y + self.h
    @property
    def bottom(self): return self.y
    @property
    def center_y(self): return self.y + self.h / 2
    @property
    def center_x(self): return self.x + self.w / 2


def draw_arrow(ax, x1, y1, x2, y2, label, color="#C0392B", style="straight"):
    """Draw connection arrow with label."""
    if style == "straight":
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color=color, lw=2.2,
                                    connectionstyle="arc3,rad=0"))
    elif style == "curve_down":
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color=color, lw=2.2,
                                    connectionstyle="arc3,rad=-0.25"))
    elif style == "curve_up":
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color=color, lw=2.2,
                                    connectionstyle="arc3,rad=0.25"))

    # Label at midpoint
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    if style == "curve_down":
        my -= 0.8
    elif style == "curve_up":
        my += 0.8

    ax.text(mx, my, label, fontsize=8.5, ha="center", va="center",
            color="#C0392B", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="#FFF5F5",
                      edgecolor="#E8A0A0", alpha=0.92))


# ── Main Drawing ──────────────────────────────────────────────

def draw():
    fig, ax = plt.subplots(1, 1, figsize=(18, 10))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.set_facecolor("#FAFBFC")

    # ── Left Column ──
    LEFT_X = 0.5
    LEFT_W = 3.6

    # host_detail (left top)
    host_box = TableBox(ax, x=LEFT_X, y=5.8, w=LEFT_W, h=2.6,
        title="HOST_DETAIL (20 rows)",
        color="#4C72B0",
        fields=[
            ("hostid",    "TEXT",     "PK"),
            ("hostname",  "TEXT",     ""),
            ("owner",     "TEXT",     ""),
            ("model",     "TEXT",     ""),
            ("location1", "TEXT",     ""),
            ("location2", "TEXT",     ""),
        ])
    host_box.draw()

    # mod_detail (left bottom)
    mod_box = TableBox(ax, x=LEFT_X, y=2.2, w=LEFT_W, h=2.5,
        title="MOD_DETAIL (55 rows)",
        color="#55A868",
        fields=[
            ("mod",         "TEXT",   "PK"),
            ("type",        "TEXT",   ""),
            ("description", "TEXT",   ""),
            ("unit",        "TEXT",   ""),
            ("tag",         "TEXT",   ""),
        ])
    mod_box.draw()

    # ── Right Column ──
    RIGHT_X = 8.2
    RIGHT_W = 4.2

    # disk_tsar (right top)
    disk_box = TableBox(ax, x=RIGHT_X, y=5.5, w=RIGHT_W, h=3.2,
        title="DISK_TSAR (12,000 rows, type=disk)",
        color="#DD8452",
        fields=[
            ("ts",      "INTEGER",  ""),
            ("hostid",  "TEXT",     "FK"),
            ("type",    "TEXT",     ""),
            ("mod",     "TEXT",     "FK"),
            ("value",   "REAL",     ""),
            ("tag",     "TEXT",     ""),
        ])
    disk_box.draw()

    # pref_tsar (right bottom)
    pref_box = TableBox(ax, x=RIGHT_X, y=1.5, w=RIGHT_W, h=3.2,
        title="PREF_TSAR (67,200 rows, type=pref)",
        color="#8172B3",
        fields=[
            ("ts",      "INTEGER",  ""),
            ("hostid",  "TEXT",     "FK"),
            ("type",    "TEXT",     ""),
            ("mod",     "TEXT",     "FK"),
            ("value",   "REAL",     ""),
            ("tag",     "TEXT",     ""),
        ])
    pref_box.draw()

    # ── Arrows ──

    # host_detail.right -> disk_tsar.left (top arrow)
    draw_arrow(ax,
        host_box.right, host_box.center_y + 0.3,
        disk_box.left, disk_box.center_y + 0.6,
        "1 host -- N disk records\n(every 5 min)",
        color="#C0392B", style="straight")

    # host_detail.right -> pref_tsar.left (middle arrow)
    draw_arrow(ax,
        host_box.right, host_box.center_y - 0.3,
        pref_box.left, pref_box.center_y + 0.4,
        "1 host -- N perf records\n(every 1 hour)",
        color="#C0392B", style="curve_down")

    # mod_detail.right -> disk_tsar.left (bottom arrow)
    draw_arrow(ax,
        mod_box.right, mod_box.center_y + 0.3,
        disk_box.left + 0.1, disk_box.center_y - 0.4,
        "1 mod -- N disk records\n(35 disk metrics)",
        color="#C0392B", style="curve_up")

    # mod_detail.right -> pref_tsar.left (bottom arrow)
    draw_arrow(ax,
        mod_box.right, mod_box.center_y - 0.3,
        pref_box.left + 0.1, pref_box.center_y - 0.4,
        "1 mod -- N perf records\n(20 perf metrics)",
        color="#C0392B", style="straight")

    # ── Legend ──
    legend_x, legend_y = 13.5, 9.2
    ax.text(legend_x, legend_y, "Legend:", fontsize=9, fontweight="bold", color="#333")
    ax.text(legend_x, legend_y - 0.35, "PK   Primary Key", fontsize=8,
            color="#D2691E", fontfamily="monospace")
    ax.text(legend_x, legend_y - 0.65, "FK   Foreign Key", fontsize=8,
            color="#4C72B0", fontfamily="monospace")
    ax.plot([legend_x + 0.03, legend_x + 0.55], [legend_y - 0.95, legend_y - 0.95],
            color="#C0392B", lw=2.2)
    ax.text(legend_x + 0.6, legend_y - 1.1, "1:N relationship", fontsize=8, color="#C0392B")

    # ── Title ──
    ax.text(9, 9.8, "TSAR Monitoring System -- ER Diagram",
            ha="center", fontsize=18, fontweight="bold", color="#2C3E50")
    ax.text(9, 9.4, "host_detail  ---<  disk_tsar / pref_tsar  >---  mod_detail",
            ha="center", fontsize=11, color="#7F8C8D", style="italic")

    # ── Timestamp note ──
    ax.text(9, 0.25,
            "Note: ts (millisecond Unix timestamp) converted to YYYY-MM-DD HH:MM:SS (UTC+8) during ETL",
            ha="center", fontsize=8.5, color="#999",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="#F8F8F8", edgecolor="#DDD"))

    # ── Save ──
    path = os.path.join(OUT_DIR, "01_er_diagram.png")
    fig.savefig(path, bbox_inches="tight", facecolor="white", edgecolor="none", dpi=200)
    print(f"  [OK] {path}")
    plt.close(fig)


if __name__ == "__main__":
    draw()
