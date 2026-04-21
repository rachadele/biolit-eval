#!/usr/bin/env python3
"""Audit screening errors (FPs and FNs) with biolit artifact context.

For each unique FP (screened_positive=True, has_perturbation=False) and FN
(screened_positive=False, has_perturbation=True) in all_merged.tsv, finds the
corresponding selected_text.txt from any bootstrap's artifacts directory and
assembles a context TSV for human review.

Usage:
    audit_false_positives.py \
        --merged all_merged.tsv \
        --ground_truth assets/ground_truth.tsv \
        --artifacts_dirs results/bootstrap_*/artifacts \
        --output errors_audit.tsv
"""

import argparse
import re
from pathlib import Path

import pandas as pd


EXCERPT_CHARS = 800


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--merged", required=True)
    p.add_argument("--ground_truth", required=True)
    p.add_argument("--artifacts_dirs", nargs="+", required=True,
                   help="One or more artifacts/ directories from biolit runs")
    p.add_argument("--output", required=True)
    return p.parse_args()


def build_artifact_index(artifacts_dirs):
    """Return dict: accession -> Path(selected_text.txt), using first match found."""
    index = {}
    for artifacts_dir in artifacts_dirs:
        artifacts_path = Path(artifacts_dir)
        if not artifacts_path.is_dir():
            continue
        for entry in sorted(artifacts_path.iterdir()):
            if not entry.is_dir():
                continue
            accession = entry.name.split("_")[0]
            if accession not in index:
                txt = entry / "selected_text.txt"
                if txt.exists():
                    index[accession] = txt
    return index


def extract_title(text):
    m = re.search(r"^Title:\s*(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def extract_excerpt(text, chars=EXCERPT_CHARS):
    """Return first N chars of content after the GEO metadata block."""
    split = re.split(r"--- Linked Publication ---", text, maxsplit=1)
    body = split[1].strip() if len(split) > 1 else text
    return body[:chars].replace("\n", " ").strip()


def union_tfs(series):
    tfs = set()
    for val in series.dropna():
        for tf in re.split(r"\s*,\s*", str(val)):
            tf = tf.strip()
            if tf:
                tfs.add(tf)
    return ", ".join(sorted(tfs))


def dedup_errors(df, error_type, ground_truth):
    """Deduplicate one error type, returning a single row per accession."""
    if error_type == "fp":
        mask = (df["screened_positive"] == True) & (df["has_perturbation"] == False)
    else:
        mask = (df["screened_positive"] == False) & (df["has_perturbation"] == True)

    sub = df[mask].copy()
    if sub.empty:
        return pd.DataFrame()

    dedup = (sub.groupby("geo_accession")
               .agg(
                   tf_name_pred=("tf_name_pred", union_tfs),
                   n_bootstraps=("bootstrap", "count"),
               )
               .reset_index())

    # Pull truth columns from ground_truth (authoritative) rather than merged,
    # since FN rows have empty tf_name_truth/perturbation_method in merged
    gt_cols = ["geo_accession", "tf_name", "perturbation_method"]
    dedup = dedup.merge(ground_truth[gt_cols], on="geo_accession", how="left")
    dedup = dedup.rename(columns={"tf_name": "tf_name_truth"})

    dedup.insert(0, "error_type", error_type)
    return dedup


def attach_artifact_context(df, artifact_index, ground_truth):
    """Add true_perturb_raw, title, text_excerpt, artifact_found columns."""
    df = df.merge(ground_truth[["geo_accession", "true_perturb_raw"]],
                  on="geo_accession", how="left")

    titles, excerpts, found = [], [], []
    for acc in df["geo_accession"]:
        txt_path = artifact_index.get(acc)
        if txt_path:
            text = txt_path.read_text(errors="replace")
            titles.append(extract_title(text))
            excerpts.append(extract_excerpt(text))
            found.append(True)
        else:
            titles.append("")
            excerpts.append("")
            found.append(False)

    df["title"] = titles
    df["text_excerpt"] = excerpts
    df["artifact_found"] = found
    return df


def main():
    args = parse_args()

    merged = pd.read_csv(args.merged, sep="\t")
    gt = pd.read_csv(args.ground_truth, sep="\t")
    artifact_index = build_artifact_index(args.artifacts_dirs)

    fp = dedup_errors(merged, "fp", gt)
    fn = dedup_errors(merged, "fn", gt)
    combined = pd.concat([fp, fn], ignore_index=True)

    combined = attach_artifact_context(combined, artifact_index, gt)

    cols = ["error_type", "geo_accession", "tf_name_pred", "tf_name_truth",
            "perturbation_method", "n_bootstraps", "true_perturb_raw",
            "title", "text_excerpt", "artifact_found"]
    combined[cols].to_csv(args.output, sep="\t", index=False)

    n_fp = (combined["error_type"] == "fp").sum()
    n_fn = (combined["error_type"] == "fn").sum()
    missing = combined["artifact_found"].eq(False).sum()
    print(f"Wrote {n_fp} unique FPs + {n_fn} unique FNs → {args.output}")
    if missing:
        print(f"  {missing} accession(s) had no artifact text found")


if __name__ == "__main__":
    main()
