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

    lines = []
    lines.append("=== Screening (has_perturbation) ===")
    lines.append(f"  Accuracy:  {accuracy_score(y_true, y_pred):.3f}")
    lines.append(f"  Precision: {precision_score(y_true, y_pred, zero_division=0):.3f}")
    lines.append(f"  Recall:    {recall_score(y_true, y_pred, zero_division=0):.3f}")
    lines.append(f"  F1:        {f1_score(y_true, y_pred, zero_division=0):.3f}")
    lines.append(f"  N:         {len(merged)}")

    lines.append("")
    lines.append("=== Field Extraction Accuracy (positives only) ===")

    pos = merged[merged["has_perturbation"] == True]
    for pred_col, truth_col, label in [
        ("tf_name_pred",            "tf_name_truth",            "tf_name"),
        ("perturbation_method_pred","perturbation_method_truth","perturbation_method"),
        ("organism_pred",           "organism_truth",           "organism"),
        ("platform_pred",           "platform_truth",           "platform"),
    ]:
        acc, n = field_accuracy(pos, pred_col, truth_col)
        lines.append(f"  {label:<22} {acc:.3f}  (n={n})")

    report = "\n".join(lines)
    print(report)
    with open(args.output, "w") as f:
        f.write(report + "\n")


if __name__ == "__main__":
    main()
