#!/usr/bin/env python3
"""Create bootstrap samples from ground_truth.tsv for CI estimation."""
import argparse, os
import pandas as pd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ground_truth", required=True)
    parser.add_argument("--n_bootstraps", type=int, required=True)
    parser.add_argument("--bootstrap_size", type=int, default=None,
                        help="Records per bootstrap sample (default: len(ground_truth))")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    df = pd.read_csv(args.ground_truth, sep="\t")
    n = args.bootstrap_size if args.bootstrap_size is not None else len(df)

    for i in range(args.n_bootstraps):
        sample = df.sample(n=n, replace=True, random_state=args.seed + i)
        sample.to_csv(f"{args.outdir}/bootstrap_{i}_sample.tsv", sep="\t", index=False)
        unique_accs = sample["geo_accession"].unique().tolist()
        with open(f"{args.outdir}/bootstrap_{i}_accessions.txt", "w") as f:
            f.write("\n".join(unique_accs) + "\n")
        n_pos = (sample["has_perturbation"] == True).sum()
        print(f"Bootstrap {i}: {len(sample)} rows ({n_pos} pos, {len(sample)-n_pos} neg), "
              f"{len(unique_accs)} unique accessions")

if __name__ == "__main__":
    main()
