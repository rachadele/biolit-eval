# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Nextflow evaluation pipeline for testing the `biolit` literature search agent
(`/Users/Rachel/Documents/lit-search-agent`) on the TF perturbation use case.

**Goal:** Assess how accurately `biolit` can screen GEO records for transcription factor
perturbation experiments and extract structured metadata, using a manually curated
ground truth spreadsheet as the reference.

**Ground truth source:** `assets/ground_truth.tsv` — derived from `assets/TF_Scrape_Sheet.xlsx`.
Contains 509 GEO accessions with hand-curated labels:
- `has_perturbation` (True/False)
- `tf_name` (transcription factor name)
- `perturbation_method` (KO / KD / OE / het / mutant / etc.)
- `organism` (from GEO `Taxa` field)
- `platform` (GPL accession from GEO `Platforms` field)
- `true_perturb_raw` (original raw label from the spreadsheet)

## Commands

```bash
# Run the full pipeline (default: 50 pos + 50 neg, seed=42)
nextflow run main.nf -profile conda

# Override parameters
nextflow run main.nf -profile conda --n_pos 20 --n_neg 20 --seed 123

# Run a single bin/ script standalone for development
python bin/sample_eval_set.py --ground_truth assets/ground_truth.tsv --n_pos 10 --n_neg 10 --seed 42 --output eval_sample.tsv
python bin/run_pipeline.py --input eval_sample.tsv --output predictions.tsv
python bin/score_eval.py --predictions predictions.tsv --ground_truth assets/ground_truth.tsv --output scores.txt

# Resume a failed run
nextflow run main.nf -resume
```

`biolit` is installed in the `lit-search-agent` virtualenv. The CLI call pattern:
```bash
biolit accessions.txt \
       --criterion "Is there a transcription factor perturbation in this experiment?" \
       --fields transcription_factor,perturbation_method,organism,platform \
       --model claude-haiku-4-5-20251001
```

## Pipeline Structure

Three Nextflow processes run sequentially:

### 1. SAMPLE (`bin/sample_eval_set.py`)
Reads `ground_truth.tsv`, samples `n_pos` positives and `n_neg` negatives using `seed`.
Output: `eval_sample.tsv`

### 2. RUN_PIPELINE (`bin/run_pipeline.py`)
Iterates over `eval_sample.tsv`, calls `biolit` per accession, collects results.
Output: `predictions.tsv` with columns `geo_accession`, `screened_positive`, `tf_name`, `perturbation_method`, `organism`, `platform`.
Runner selectable via `params.runner` (`cli` or `mcp`).

### 3. SCORE (`bin/score_eval.py`)
Joins `predictions.tsv` with `ground_truth.tsv` on `geo_accession` and reports:
- Screening metrics: accuracy, precision, recall, F1 for `has_perturbation`
- Per-field extraction accuracy for `tf_name`, `perturbation_method`, `organism`, `platform`

Output: `scores.txt`

## Parameters (`nextflow.config`)

| Parameter | Default | Description |
|---|---|---|
| `ground_truth` | `assets/ground_truth.tsv` | Path to ground truth TSV |
| `n_pos` | `50` | Number of positive examples to sample |
| `n_neg` | `50` | Number of negative examples to sample |
| `seed` | `42` | Random seed for sampling |
| `runner` | `cli` | How to invoke biolit (`cli` or `mcp`) |
| `model` | `claude-haiku-4-5-20251001` | LLM model for screening + extraction |
| `outdir` | `results/` | Output directory |

## Environment

- **Python:** `/Users/Rachel/miniconda3/bin/python3`
- **biolit:** available in the base conda env (`/Users/Rachel/miniconda3`)
- **Nextflow:** DSL2
