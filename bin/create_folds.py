#!/usr/bin/env python3
"""Create stratified k-fold splits from ground_truth.tsv."""
import argparse, os
import pandas as pd
from sklearn.model_selection import StratifiedKFold

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ground_truth", required=True)
    parser.add_argument("--k", type=int, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    df = pd.read_csv(args.ground_truth, sep="\t")
    skf = StratifiedKFold(n_splits=args.k, shuffle=True, random_state=args.seed)

    for fold_id, (_, test_idx) in enumerate(skf.split(df, df["has_perturbation"])):
        test_df = df.iloc[test_idx]
        test_df.to_csv(f"{args.outdir}/fold_{fold_id}_test.tsv", sep="\t", index=False)
        with open(f"{args.outdir}/fold_{fold_id}_accessions.txt", "w") as f:
            f.write("\n".join(test_df["geo_accession"].tolist()) + "\n")
        n_pos = (test_df["has_perturbation"] == True).sum()
        print(f"Fold {fold_id}: {len(test_df)} rows ({n_pos} pos, {len(test_df)-n_pos} neg)")

if __name__ == "__main__":
    main()
