#!/usr/bin/env python3
"""Sample a balanced eval set from the ground truth TSV."""

import argparse
import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ground_truth", required=True)
    parser.add_argument("--n_pos", type=int, required=True)
    parser.add_argument("--n_neg", type=int, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ids_output", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.ground_truth, sep="\t")

    pos = df[df["has_perturbation"] == True].sample(
        n=args.n_pos, random_state=args.seed, replace=False
    )
    neg = df[df["has_perturbation"] == False].sample(
        n=args.n_neg, random_state=args.seed, replace=False
    )

    sample = pd.concat([pos, neg]).sample(frac=1, random_state=args.seed)
    sample.to_csv(args.output, sep="\t", index=False)

    with open(args.ids_output, "w") as f:
        f.write("\n".join(sample["geo_accession"].tolist()) + "\n")

    print(f"Sampled {len(pos)} positives + {len(neg)} negatives → {args.output}, {args.ids_output}")


if __name__ == "__main__":
    main()
