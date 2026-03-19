#!/usr/bin/env python3
"""Score predictions against ground truth."""

import argparse
import json
import re

import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


def norm(val):
    """Lowercase and strip for loose string matching."""
    if pd.isna(val) or str(val).strip() == "":
        return ""
    return str(val).strip().lower()


def to_set(val):
    """Normalize a field value to a set of lowercase tokens, splitting on , / ;"""
    s = norm(val)
    if not s:
        return set()
    return {t.strip() for t in re.split(r"[,/;]+", s) if t.strip()}


def jaccard(a, b):
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def field_jaccard(merged, pred_col, truth_col):
    """Mean Jaccard similarity over rows where ground truth is non-empty."""
    sub = merged[merged[truth_col].apply(norm) != ""]
    if sub.empty:
        return float("nan"), 0
    scores = sub.apply(lambda r: jaccard(to_set(r[pred_col]), to_set(r[truth_col])), axis=1)
    return scores.mean(), len(sub)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--ground_truth", required=True)
    parser.add_argument("--config", required=True, help="Biolit config JSON")
    parser.add_argument("--screening_truth_col", default="has_perturbation",
                        help="Ground truth column for screening evaluation")
    parser.add_argument("--field_map", default=None,
                        help="Optional key:value,... override for biolit→ground-truth column mapping")
    parser.add_argument("--output", required=True)
    parser.add_argument("--merged_output", default=None, help="Optional path to write merged predictions+ground truth TSV")
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)
    # fields dict keys are biolit output column names; default truth col = same name
    field_map = {k: k for k in config.get("fields", {}).keys()}

    # allow runtime override: biolit_field:truth_col,...
    if args.field_map:
        for pair in args.field_map.split(","):
            k, v = pair.split(":")
            field_map[k.strip()] = v.strip()

    preds = pd.read_csv(args.predictions, sep="\t")
    truth = pd.read_csv(args.ground_truth, sep="\t")

    merged = preds.merge(truth, on="geo_accession", suffixes=("_pred", "_truth"))

    y_true = merged[args.screening_truth_col].astype(bool)
    y_pred = merged["screened_positive"].astype(bool)
    pos = merged[merged[args.screening_truth_col] == True]

    rows = [
        {"metric": "accuracy",  "group": "screening", "value": accuracy_score(y_true, y_pred),                   "n": len(merged)},
        {"metric": "precision", "group": "screening", "value": precision_score(y_true, y_pred, zero_division=0), "n": len(merged)},
        {"metric": "recall",    "group": "screening", "value": recall_score(y_true, y_pred, zero_division=0),    "n": len(merged)},
        {"metric": "f1",        "group": "screening", "value": f1_score(y_true, y_pred, zero_division=0),        "n": len(merged)},
    ]

    for biolit_field, truth_col in field_map.items():
        pred_col = f"{biolit_field}_pred" if f"{biolit_field}_pred" in merged.columns else biolit_field
        tc = f"{truth_col}_truth" if f"{truth_col}_truth" in merged.columns else truth_col
        if pred_col not in merged.columns or tc not in merged.columns:
            continue
        acc, n = field_jaccard(pos, pred_col, tc)
        rows.append({"metric": truth_col, "group": "extraction", "value": acc, "n": n})

    scores = pd.DataFrame(rows)
    scores.to_csv(args.output, sep="\t", index=False)

    if args.merged_output:
        merged.to_csv(args.merged_output, sep="\t", index=False)

    # human-readable report
    screening = scores[scores["group"] == "screening"].set_index("metric")
    extraction = scores[scores["group"] == "extraction"].set_index("metric")

    lines = [
        "=== Screening (has_perturbation) ===",
        f"  Accuracy:  {screening.loc['accuracy',  'value']:.3f}",
        f"  Precision: {screening.loc['precision', 'value']:.3f}",
        f"  Recall:    {screening.loc['recall',    'value']:.3f}",
        f"  F1:        {screening.loc['f1',        'value']:.3f}",
        f"  N:         {int(screening.loc['accuracy', 'n'])}",
    ]
    if not extraction.empty:
        lines += ["", "=== Field Extraction Mean Jaccard (positives only) ==="]
        for metric, row in extraction.iterrows():
            lines.append(f"  {metric:<22} {row['value']:.3f}  (n={int(row['n'])})")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
