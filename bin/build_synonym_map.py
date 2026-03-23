#!/usr/bin/env python3
"""Build a gene synonym lookup from NCBI Entrez for TF names in ground_truth.tsv.

Reads unique TF name tokens from ground_truth.tsv, queries the NCBI Gene database
for each, and writes a JSON mapping {lowercase_alias: lowercase_canonical_symbol}.

Run once to produce assets/gene_synonyms.json, which score_eval.py can load via
--synonym_map.

Usage:
    python bin/build_synonym_map.py \
        --ground_truth assets/ground_truth.tsv \
        --email you@example.com \
        --output assets/gene_synonyms.json
"""
import argparse
import json
import re
import time

import pandas as pd
from Bio import Entrez


def is_plausible_gene_name(tok):
    """Return True if tok looks like a gene symbol worth querying."""
    if len(tok) < 3:
        return False
    if " " in tok:
        return False
    if re.match(r"^\d+$", tok):  # purely numeric
        return False
    if not re.match(r"^[A-Za-z0-9][A-Za-z0-9.\-]+$", tok):
        return False
    return True


def parse_tf_names(ground_truth_path):
    df = pd.read_csv(ground_truth_path, sep="\t")
    names = set()
    for val in df["tf_name"].dropna():
        for tok in re.split(r"[,/;&]+", str(val)):
            tok = tok.strip()
            if tok and is_plausible_gene_name(tok):
                names.add(tok)
    return sorted(names)


def fetch_gene(name, organisms=("Homo sapiens", "Mus musculus")):
    """Return (canonical_symbol, [aliases]) for the first organism hit, or None."""
    for organism in organisms:
        query = f"{name}[Gene Name] AND {organism}[Organism]"
        handle = Entrez.esearch(db="gene", term=query, retmax=5)
        record = Entrez.read(handle)
        handle.close()
        ids = record["IdList"]
        if not ids:
            continue
        handle = Entrez.esummary(db="gene", id=ids[0])
        summary = Entrez.read(handle)
        handle.close()
        doc = summary["DocumentSummarySet"]["DocumentSummary"][0]
        canonical = doc["NomenclatureSymbol"] or doc["Name"]
        aliases_raw = doc.get("OtherAliases", "")
        aliases = [a.strip() for a in aliases_raw.split(",") if a.strip()] if aliases_raw else []
        return canonical, aliases
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ground_truth", required=True)
    parser.add_argument("--email", required=True, help="Email address for NCBI Entrez")
    parser.add_argument("--output", default="assets/gene_synonyms.json")
    parser.add_argument("--delay", type=float, default=0.35,
                        help="Seconds between requests (default 0.35 → ~3/sec, the no-API-key limit)")
    args = parser.parse_args()

    Entrez.email = args.email

    tf_names = parse_tf_names(args.ground_truth)
    print(f"Querying NCBI for {len(tf_names)} unique TF name tokens\n")

    synonym_map = {}  # lowercase alias → lowercase canonical
    failed = []

    for i, name in enumerate(tf_names, 1):
        result = fetch_gene(name)
        if result is None:
            print(f"[{i:3d}/{len(tf_names)}] NOT FOUND: {name}")
            failed.append(name)
        else:
            canonical, aliases = result
            canonical_l = canonical.lower()
            for tok in [canonical, name] + aliases:
                synonym_map[tok.lower()] = canonical_l
            print(f"[{i:3d}/{len(tf_names)}] {name} → {canonical}  ({len(aliases)} aliases)")
        time.sleep(args.delay)

    with open(args.output, "w") as f:
        json.dump(synonym_map, f, indent=2, sort_keys=True)

    print(f"\nWrote {len(synonym_map)} entries → {args.output}")
    if failed:
        print(f"Not found ({len(failed)}): {', '.join(failed)}")


if __name__ == "__main__":
    main()
