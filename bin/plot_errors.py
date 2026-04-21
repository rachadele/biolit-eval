#!/usr/bin/env python3
"""Plot screening error analysis from all_merged.tsv."""

import argparse

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd


def grouped_barh(ax, fp_counts, fn_counts, title, top_n=15):
    """Horizontal grouped bar chart with FP/FN side by side for shared categories."""
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


def stochasticity_panel(ax, merged):
    """Stacked horizontal bar: error bootstraps vs correct bootstraps per accession.

    Only shows accessions sampled in more than one bootstrap — stochasticity
    is only meaningful when an accession can be compared across draws.
    """
    is_fp = (merged["screened_positive"] == True) & (merged["has_perturbation"] == False)
    is_fn = (merged["screened_positive"] == False) & (merged["has_perturbation"] == True)
    merged = merged.copy()
    merged["error_type"] = "correct"
    merged.loc[is_fp, "error_type"] = "fp"
    merged.loc[is_fn, "error_type"] = "fn"

    # Only accessions that were ever an error
    error_accs = merged.loc[merged["error_type"] != "correct", "geo_accession"].unique()
    sub = merged[merged["geo_accession"].isin(error_accs)]

    counts = (sub.groupby(["geo_accession", "error_type"]).size()
                .unstack(fill_value=0))
    for col in ["fp", "fn", "correct"]:
        if col not in counts:
            counts[col] = 0
    counts["n_total"] = counts[["fp", "fn", "correct"]].sum(axis=1)

    # Only show accessions sampled more than once
    counts = counts[counts["n_total"] > 1].sort_values("fp", ascending=True)

    if counts.empty:
        ax.text(0.5, 0.5, "All errors are one-off\n(each accession sampled once)",
                ha="center", va="center", transform=ax.transAxes, fontsize=14)
        ax.set_title("LLM stochasticity", fontsize=20)
        return

    y = range(len(counts))
    ax.barh(list(y), counts["fp"], color="salmon", label="FP")
    ax.barh(list(y), counts["fn"], left=counts["fp"], color="steelblue", label="FN")
    ax.barh(list(y), counts["correct"], left=counts["fp"] + counts["fn"],
            color="lightgrey", label="correct")
    ax.set_yticks(list(y))
    ax.set_yticklabels(counts.index, fontsize=12)
    ax.set_xlabel("Bootstrap appearances", fontsize=16)
    ax.set_title("LLM stochasticity", fontsize=20)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.tick_params(axis="x", labelsize=16)
    ax.legend(fontsize=16)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged", required=True, help="Path to all_merged.tsv")
    parser.add_argument("--output", required=True, help="Output PNG path")
    parser.add_argument("--top_n", type=int, default=15, help="Top N items in bar charts")
    args = parser.parse_args()

    merged = pd.read_csv(args.merged, sep="\t")

    is_fp = (merged["screened_positive"] == True) & (merged["has_perturbation"] == False)
    is_fn = (merged["screened_positive"] == False) & (merged["has_perturbation"] == True)
    fp = merged[is_fp]
    fn = merged[is_fn]

    fig, axes = plt.subplots(1, 3, figsize=(18, 7))
    ax1, ax2, ax3 = axes

    # --- Panel 1: LLM stochasticity ---
    stochasticity_panel(ax1, merged)

    # --- Panel 2: TF names (FP predicted vs FN truth) ---
    fp_tfs = (fp["tf_name_pred"].dropna().astype(str)
              .str.split(r"\s*,\s*").explode().str.strip().str.upper())
    fp_tfs = fp_tfs[fp_tfs.str.len() > 0]
    fp_tf_counts = fp_tfs.value_counts()

    fn_tfs = (fn["tf_name_truth"].dropna().astype(str)
              .str.split(r"\s*,\s*").explode().str.strip().str.upper())
    fn_tfs = fn_tfs[fn_tfs.str.len() > 0]
    fn_tf_counts = fn_tfs.value_counts()

    grouped_barh(ax2, fp_tf_counts, fn_tf_counts, "TF names (FP predicted / FN truth)", args.top_n)

    # --- Panel 3: Organism ---
    fp_org_counts = fp["organism_pred"].fillna("unknown").value_counts()
    fn_org_counts = fn["organism_truth"].fillna("unknown").value_counts()
    grouped_barh(ax3, fp_org_counts, fn_org_counts, "Organism", args.top_n)

    fig.suptitle("Screening errors", fontsize=20)
    fig.tight_layout()
    fig.savefig(args.output, dpi=150, bbox_inches="tight")
    print(f"Saved plot → {args.output}")


if __name__ == "__main__":
    main()
