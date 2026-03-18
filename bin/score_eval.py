#!/usr/bin/env python3
"""Score predictions against ground truth."""

import argparse

import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


def norm(val):
    """Lowercase and strip for loose string matching."""
    if pd.isna(val) or str(val).strip() == "":
        return ""
    return str(val).strip().lower()


def field_accuracy(merged, pred_col, truth_col):
    """Accuracy over rows where ground truth is non-empty."""
    sub = merged[merged[truth_col].apply(norm) != ""]
    if sub.empty:
        return float("nan"), 0
    correct = sub.apply(lambda r: norm(r[pred_col]) == norm(r[truth_col]), axis=1)
    return correct.mean(), len(sub)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--ground_truth", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    preds = pd.read_csv(args.predictions, sep="\t")
    truth = pd.read_csv(args.ground_truth, sep="\t")

    merged = preds.merge(truth, on="geo_accession", suffixes=("_pred", "_truth"))

    y_true = merged["has_perturbation"].astype(bool)
    y_pred = merged["screened_positive"].astype(bool)
    pos = merged[merged["has_perturbation"] == True]

    rows = [
        {"metric": "accuracy",  "group": "screening", "value": accuracy_score(y_true, y_pred),                   "n": len(merged)},
        {"metric": "precision", "group": "screening", "value": precision_score(y_true, y_pred, zero_division=0), "n": len(merged)},
        {"metric": "recall",    "group": "screening", "value": recall_score(y_true, y_pred, zero_division=0),    "n": len(merged)},
        {"metric": "f1",        "group": "screening", "value": f1_score(y_true, y_pred, zero_division=0),        "n": len(merged)},
    ]
    for pred_col, truth_col, label in [
        ("organism_pred", "organism_truth", "organism"),
        ("platform_pred", "platform_truth", "platform"),
    ]:
        acc, n = field_accuracy(pos, pred_col, truth_col)
        rows.append({"metric": label, "group": "extraction", "value": acc, "n": n})

    scores = pd.DataFrame(rows)
    scores.to_csv(args.output, sep="\t", index=False)

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
        "",
        "=== Field Extraction Accuracy (positives only) ===",
    ]
    for metric, row in extraction.iterrows():
        lines.append(f"  {metric:<22} {row['value']:.3f}  (n={int(row['n'])})")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
