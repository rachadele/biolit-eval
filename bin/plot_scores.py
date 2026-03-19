#!/usr/bin/env python3
"""Plot screening and extraction metrics from all_scores.tsv (k-fold CV)."""

import argparse

import matplotlib.pyplot as plt
import pandas as pd


def boxplot_panel(ax, scores, group_label, title, ylabel):
    sub = scores[scores["group"] == group_label]
    if sub.empty:
        ax.set_visible(False)
        return
    metrics = sub["metric"].unique()
    plot_data = [sub[sub["metric"] == m]["value"].dropna().tolist() for m in metrics]
    ax.boxplot(plot_data, labels=metrics, patch_artist=True)
    ax.set_ylim(0, 1)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=20)
    for i, vals in enumerate(plot_data, start=1):
        ax.scatter([i] * len(vals), vals, alpha=0.5, s=20, color="black", zorder=3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", required=True)
    parser.add_argument("--screening_truth_col", default="has_perturbation")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    scores = pd.read_csv(args.scores, sep="\t")

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    ax1, ax2, ax3 = axes

    boxplot_panel(ax1, scores, "screening",
                  f"Screening ({args.screening_truth_col})", "Score")
    boxplot_panel(ax2, scores, "extraction_exact",
                  "Field extraction accuracy", "Accuracy")
    boxplot_panel(ax3, scores, "extraction_jaccard",
                  "Field extraction (Jaccard)", "Mean Jaccard similarity")

    k = scores["fold"].nunique() if "fold" in scores.columns else "?"
    fig.suptitle(f"K-Fold CV  (k={k})")
    fig.tight_layout()
    fig.savefig(args.output, dpi=150, bbox_inches="tight")
    print(f"Saved plot → {args.output}")


if __name__ == "__main__":
    main()
