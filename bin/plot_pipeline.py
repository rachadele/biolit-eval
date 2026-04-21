#!/usr/bin/env python3
"""Metro-map style pipeline diagram — text inside nodes, visible arrows."""

import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


NODE_COLORS = {
    "data":   "#fbbf24",
    "proc":   "#60a5fa",
    "model":  "#a78bfa",
    "metric": "#34d399",
}
BG        = "#f8fafc"
TEXT_DARK = "#1e293b"
TRACK_COL  = "#1e293b"
BRANCH_COL = "#047857"


def node(ax, cx, cy, w, h, lines, kind):
    """Rounded-rect node with all text inside."""
    color = NODE_COLORS[kind]
    rect = FancyBboxPatch(
        (cx - w/2, cy - h/2), w, h,
        boxstyle="round,pad=0.02",
        facecolor=color, edgecolor="#1e293b", linewidth=1.5, zorder=4,
    )
    ax.add_patch(rect)
    if isinstance(lines, str):
        lines = lines.split("\n")
    n = len(lines)
    for i, line in enumerate(lines):
        frac = (i + 1) / (n + 1)
        y = cy + h/2 - frac * h
        bold = (i == 0)
        ax.text(cx, y, line,
                ha="center", va="center",
                fontsize=10 if bold else 9,
                fontweight="bold" if bold else "normal",
                color=TEXT_DARK, zorder=5)


def connect(ax, x0, cx, cy0, cy1, w0, w1, color=TRACK_COL, lw=2.5):
    """Arrow from right edge of source node to left edge of dest node."""
    GAP = 0.006
    start_x = x0 + w0/2 + GAP
    end_x   = cx - w1/2 - GAP
    ax.annotate("",
        xy=(end_x, cy1), xytext=(start_x, cy0),
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=lw,
            mutation_scale=18,
            connectionstyle="arc3,rad=0.0",
        ),
        zorder=6,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="pipeline_diagram.png")
    args = parser.parse_args()

    fig, ax = plt.subplots(figsize=(18, 4))
    ax.set_facecolor(BG)
    fig.patch.set_facecolor(BG)
    ax.set_xlim(-0.01, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    MY = 0.52   # main track y
    NW = 0.085  # node width
    NH = 0.22   # node height

    # 6 main nodes evenly spaced from 0.06 to 0.70
    N_NODES = 6
    X_START, X_END = 0.06, 0.70
    step = (X_END - X_START) / (N_NODES - 1)
    xs = [X_START + i * step for i in range(N_NODES)]
    nodes = [
        ("GEO Accessions\nn = 509\nTF perturbation\nexperiments",       "data"),
        ("Ground Truth\nmanual curation\nhas perturbation\nTF name\norganism · platform", "data"),
        ("Bootstrap\nSampling\n5 folds · n=30\nwith replacement",          "proc"),
        ("biolit\nclaude-sonnet-4-6\n25k tokens/record\nscreening +\nextraction", "model"),
        ("Parse\nPredictions\nscreened positive\nTF name\norganism · platform",    "proc"),
        ("Score\n+ ground truth\nper bootstrap\n→ 95% CI",        "proc"),
    ]

    # draw main-track nodes
    for x, (text, kind) in zip(xs, nodes):
        node(ax, x, MY, NW, NH, text, kind)

    # draw main-track arrows
    for i in range(len(xs) - 1):
        connect(ax, xs[i], xs[i+1], MY, MY, NW, NW)

    # branch outputs
    OW = 0.09
    OH = 0.18
    OX = 0.90
    Y_SCREEN  = 0.76
    Y_EXTRACT = 0.28

    node(ax, OX, Y_SCREEN, OW, OH,
         "Screening Metrics\nAccuracy · Precision\nRecall · F1\n→ 95% CI (all records)",
         "metric")

    node(ax, OX, Y_EXTRACT, OW, OH,
         "Extraction Metrics\norganism · platform\nTF name Jaccard\n→ 95% CI (TPs only)",
         "metric")

    connect(ax, xs[-1], OX, MY, Y_SCREEN,  NW, OW, color=BRANCH_COL)
    connect(ax, xs[-1], OX, MY, Y_EXTRACT, NW, OW, color=BRANCH_COL)


    # legend
    items = [
        mpatches.Patch(color=NODE_COLORS["data"],   label="Data"),
        mpatches.Patch(color=NODE_COLORS["proc"],   label="Processing"),
        mpatches.Patch(color=NODE_COLORS["model"],  label="LLM inference"),
        mpatches.Patch(color=NODE_COLORS["metric"], label="Output metrics"),
    ]
    ax.legend(handles=items, loc="lower left", fontsize=8.5,
              framealpha=0.9, edgecolor="#cbd5e1", facecolor=BG,
              bbox_to_anchor=(0.0, 0.02))
    plt.tight_layout()
    plt.savefig(args.output, dpi=150, bbox_inches="tight")
    print(f"Saved → {args.output}")


if __name__ == "__main__":
    main()
