#!/usr/bin/env python3
"""Plot screening and extraction metrics from scores.tsv."""

import argparse

import matplotlib.pyplot as plt
import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    scores = pd.read_csv(args.scores, sep="\t")
    screening = scores[scores["group"] == "screening"]
    exact = scores[scores["group"] == "extraction_exact"]
    jaccard = scores[scores["group"] == "extraction_jaccard"]
    extraction = pd.concat([exact, jaccard])

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    ax1, ax2, ax3 = axes

    ax1.bar(screening["metric"], screening["value"])
    ax1.set_ylim(0, 1)
    ax1.set_ylabel("Score")
    ax1.set_title("Screening metrics")

    ax2.bar(exact["metric"], exact["value"])
    ax2.set_ylim(0, 1)
    ax2.set_ylabel("Accuracy")
    ax2.set_title("Field extraction accuracy")
    ax2.tick_params(axis="x", rotation=20)

    ax3.bar(jaccard["metric"], jaccard["value"])
    ax3.set_ylim(0, 1)
    ax3.set_ylabel("Mean Jaccard similarity")
    ax3.set_title("Field extraction (Jaccard)")
    ax3.tick_params(axis="x", rotation=20)

    fig.tight_layout()
    fig.savefig(args.output, dpi=150)
    print(f"Saved plot → {args.output}")


if __name__ == "__main__":
    main()
