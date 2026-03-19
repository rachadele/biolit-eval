#!/usr/bin/env python3
"""Map biolit CSV output to predictions.tsv."""

import argparse
import ast
import json

import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--biolit_csv", required=True)
    parser.add_argument("--eval_sample", required=True)
    parser.add_argument("--config", required=True, help="Biolit config JSON")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)
    fields = config.get("fields", {})  # {biolit_field: truth_col}

    sample = pd.read_csv(args.eval_sample, sep="\t")
    biolit = pd.read_csv(args.biolit_csv)

    relevant = set(biolit["geo_accession"].dropna().str.strip().tolist())

    rows = []
    for acc in sample["geo_accession"]:
        base = {"geo_accession": acc}
        if acc in relevant:
            row = biolit[biolit["geo_accession"] == acc].iloc[0]
            base["screened_positive"] = True
            for biolit_field in fields:
                val = row.get(biolit_field, "")
                if isinstance(val, str) and val.startswith("["):
                    try:
                        val = ", ".join(ast.literal_eval(val))
                    except (ValueError, SyntaxError):
                        pass
                base[biolit_field] = val
        else:
            base["screened_positive"] = False
            for biolit_field in fields:
                base[biolit_field] = ""
        rows.append(base)

    predictions = pd.DataFrame(rows)
    predictions.to_csv(args.output, sep="\t", index=False)
    n_pos = predictions["screened_positive"].sum()
    print(f"{n_pos}/{len(predictions)} screened positive → {args.output}")


if __name__ == "__main__":
    main()
