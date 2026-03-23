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


def to_set(val, synonym_map=None):
    """Normalize a field value to a set of lowercase tokens, splitting on , / ;

    If synonym_map is provided, each token is resolved to its canonical form
    before the set is returned (e.g. 'p53' → 'tp53').
    """
    s = norm(val)
    if not s:
        return set()
    tokens = {t.strip() for t in re.split(r"[,/;]+", s) if t.strip()}
    if synonym_map:
        tokens = {synonym_map.get(t, t) for t in tokens}
    return tokens


def jaccard(a, b):
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def field_jaccard(merged, pred_col, truth_col, synonym_map=None):
    """Mean Jaccard similarity over rows where ground truth is non-empty."""
    sub = merged[merged[truth_col].apply(norm) != ""]
    if sub.empty:
        return float("nan"), 0
    scores = sub.apply(
        lambda r: jaccard(to_set(r[pred_col], synonym_map), to_set(r[truth_col], synonym_map)),
        axis=1,
    )
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
    parser.add_argument("--jaccard_fields", default=None,
                        help="Comma-separated field names to score with Jaccard instead of exact match")
    parser.add_argument("--synonym_map", default=None,
                        help="Path to gene_synonyms.json for synonym-aware Jaccard scoring of TF names")
    parser.add_argument("--output", required=True)
    parser.add_argument("--merged_output", default=None, help="Optional path to write merged predictions+ground truth TSV")
    parser.add_argument("--errors_output", default=None, help="Optional path to write false positive / false negative rows TSV")
    parser.add_argument("--bootstrap", type=int, default=None, help="Bootstrap index to stamp into output rows")
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    synonym_map = None
    if args.synonym_map:
        with open(args.synonym_map) as f:
            synonym_map = json.load(f)
    # fields dict keys are biolit output column names; default truth col = same name
    field_map = {k: k for k in config.get("fields", {}).keys()}
    jaccard_fields = set(args.jaccard_fields.split(",")) if args.jaccard_fields else set()

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
    # Field extraction is evaluated only on true positives (ground truth positive
    # AND biolit screened positive), isolating extraction quality from screening recall.
    pos = merged[(merged[args.screening_truth_col] == True) & (merged["screened_positive"] == True)]

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
        if biolit_field in jaccard_fields:
            val, n = field_jaccard(pos, pred_col, tc, synonym_map=synonym_map)
            group = "extraction_jaccard"
        else:
            sub = pos[pos[tc].apply(norm) != ""]
            val = sub.apply(lambda r: norm(r[pred_col]) == norm(r[tc]), axis=1).mean() if not sub.empty else float("nan")
            n = len(sub)
            group = "extraction_exact"
        rows.append({"metric": truth_col, "group": group, "value": val, "n": n})

    if args.bootstrap is not None:
        for r in rows:
            r["bootstrap"] = args.bootstrap

    scores = pd.DataFrame(rows)
    scores.to_csv(args.output, sep="\t", index=False)

    if args.merged_output:
        if args.bootstrap is not None:
            merged["bootstrap"] = args.bootstrap
        merged.to_csv(args.merged_output, sep="\t", index=False)

    if args.errors_output:
        fp = merged[(~y_true) & y_pred].copy()
        fn = merged[y_true & (~y_pred)].copy()
        fp["error_type"] = "fp"
        fn["error_type"] = "fn"
        errors = pd.concat([fp, fn], ignore_index=True)
        if args.bootstrap is not None:
            errors["bootstrap"] = args.bootstrap
        errors.to_csv(args.errors_output, sep="\t", index=False)

    # human-readable report
    screening = scores[scores["group"] == "screening"].set_index("metric")

    lines = [
        "=== Screening (has_perturbation) ===",
        f"  Accuracy:  {screening.loc['accuracy',  'value']:.3f}",
        f"  Precision: {screening.loc['precision', 'value']:.3f}",
        f"  Recall:    {screening.loc['recall',    'value']:.3f}",
        f"  F1:        {screening.loc['f1',        'value']:.3f}",
        f"  N:         {int(screening.loc['accuracy', 'n'])}",
    ]
    exact = scores[scores["group"] == "extraction_exact"].set_index("metric")
    jaccard_ex = scores[scores["group"] == "extraction_jaccard"].set_index("metric")
    if not exact.empty:
        lines += ["", "=== Field Extraction Accuracy (true positives only) ==="]
        for metric, row in exact.iterrows():
            lines.append(f"  {metric:<22} {row['value']:.3f}  (n={int(row['n'])})")
    if not jaccard_ex.empty:
        lines += ["", "=== Field Extraction Mean Jaccard (true positives only) ==="]
        for metric, row in jaccard_ex.iterrows():
            lines.append(f"  {metric:<22} {row['value']:.3f}  (n={int(row['n'])})")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
