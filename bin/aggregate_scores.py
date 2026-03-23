#!/usr/bin/env python3
"""Concatenate per-fold scores.tsv files into a single all_scores.tsv."""
import argparse
import pandas as pd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    dfs = [pd.read_csv(p, sep="\t") for p in args.scores]
    combined = pd.concat(dfs, ignore_index=True)
    if "bootstrap" not in combined.columns:
        raise ValueError("Input scores files missing 'bootstrap' column — re-run score_eval.py with --bootstrap.")
    combined.to_csv(args.output, sep="\t", index=False)
    bootstraps = sorted(combined["bootstrap"].unique())
    print(f"Aggregated {len(bootstraps)} bootstraps, {len(combined)} rows → {args.output}")

if __name__ == "__main__":
    main()
