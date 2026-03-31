#!/usr/bin/env python3
"""Plot screening error analysis from screening_errors.tsv."""

import argparse

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd


def grouped_barh(ax, fp_counts, fn_counts, title, top_n=15):
    """Horizontal grouped bar chart with FP/FN side by side for shared categories."""
    # Union of top_n categories from each, ranked by combined count
    combined = (fp_counts.add(fn_counts, fill_value=0)
                .sort_values(ascending=False)
                .head(top_n))
    cats = combined.index.tolist()

    fp_vals = [fp_counts.get(c, 0) for c in cats]
    fn_vals = [fn_counts.get(c, 0) for c in cats]

    y = range(len(cats))
    height = 0.35
    ax.barh([i + height / 2 for i in y], fp_vals, height, label="FP", color="salmon")
    ax.barh([i - height / 2 for i in y], fn_vals, height, label="FN", color="steelblue")
    ax.set_yticks(list(y))
    ax.set_yticklabels(cats, fontsize=20)
    ax.set_title(title, fontsize=20)
    ax.set_xlabel("Count", fontsize=20)
    ax.tick_params(axis="x", labelsize=20)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.legend(fontsize=20)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--errors", required=True, help="Path to screening_errors.tsv")
    parser.add_argument("--output", required=True, help="Output PNG path")
    parser.add_argument("--top_n", type=int, default=15, help="Top N items in bar charts")
    args = parser.parse_args()

    df = pd.read_csv(args.errors, sep="\t")
    fp = df[df["error_type"] == "fp"]
    fn = df[df["error_type"] == "fn"]

    fig, axes = plt.subplots(1, 3, figsize=(18, 7))
    ax1, ax2, ax3 = axes

    # --- Panel 1: FP/FN counts per bootstrap ---
    bootstrap_counts = df.groupby(["bootstrap", "error_type"]).size().unstack(fill_value=0)
    bootstraps = sorted(bootstrap_counts.index)
    x = range(len(bootstraps))
    width = 0.35
    ax1.bar([i - width / 2 for i in x],
            bootstrap_counts.get("fp", pd.Series(0, index=bootstraps)).loc[bootstraps],
            width, label="FP", color="salmon")
    ax1.bar([i + width / 2 for i in x],
            bootstrap_counts.get("fn", pd.Series(0, index=bootstraps)).loc[bootstraps],
            width, label="FN", color="steelblue")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels([f"b{b}" for b in bootstraps], rotation=45, ha="right", fontsize=20)
    ax1.set_ylabel("Count", fontsize=20)
    ax1.set_title("FP / FN counts per bootstrap", fontsize=20)
    ax1.tick_params(axis="y", labelsize=20)
    ax1.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax1.legend(fontsize=20)

    # --- Panel 2: TF names (FP predicted vs FN truth) ---
    fp_tfs = (fp["tf_name_pred"].dropna().astype(str)
              .str.split(r"\s*,\s*").explode().str.strip().str.lower())
    fp_tfs = fp_tfs[fp_tfs.str.len() > 0]
    fp_tf_counts = fp_tfs.value_counts()

    fn_tfs = (fn["tf_name_truth"].dropna().astype(str)
              .str.split(r"\s*,\s*").explode().str.strip().str.lower())
    fn_tfs = fn_tfs[fn_tfs.str.len() > 0]
    fn_tf_counts = fn_tfs.value_counts()

    grouped_barh(ax2, fp_tf_counts, fn_tf_counts, "TF names (FP predicted / FN truth)", args.top_n)

    # --- Panel 3: Organism ---
    fp_org_counts = fp["organism_pred"].fillna("unknown").value_counts()
    fn_org_counts = fn["organism_truth"].fillna("unknown").value_counts()
    grouped_barh(ax3, fp_org_counts, fn_org_counts, "Organism", args.top_n)

    total_fp = len(fp)
    total_fn = len(fn)
    n = df["bootstrap"].nunique() if "bootstrap" in df.columns else "?"
    fig.suptitle(f"Screening errors  (n={n}, total FP={total_fp}, FN={total_fn})", fontsize=20)
    fig.tight_layout()
    fig.savefig(args.output, dpi=150, bbox_inches="tight")
    print(f"Saved plot → {args.output}")


if __name__ == "__main__":
    main()
