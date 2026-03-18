#!/usr/bin/env python3
"""Map biolit CSV output to predictions.tsv."""

import argparse

import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--biolit_csv", required=True)
    parser.add_argument("--eval_sample", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    sample = pd.read_csv(args.eval_sample, sep="\t")
    biolit = pd.read_csv(args.biolit_csv)

    relevant = set(biolit["geo_accession"].dropna().str.strip().tolist())

    rows = []
    for acc in sample["geo_accession"]:
        if acc in relevant:
            row = biolit[biolit["geo_accession"] == acc].iloc[0]
            rows.append({
                "geo_accession": acc,
                "screened_positive": True,
                "organism": row.get("organism_scientific_name", ""),
                "platform": row.get("platform_gpl_accession", ""),
            })
        else:
            rows.append({
                "geo_accession": acc,
                "screened_positive": False,
                "organism": "",
                "platform": "",
            })

    predictions = pd.DataFrame(rows)
    predictions.to_csv(args.output, sep="\t", index=False)
    n_pos = predictions["screened_positive"].sum()
    print(f"{n_pos}/{len(predictions)} screened positive → {args.output}")


if __name__ == "__main__":
    main()
