# CLAUDE.md

## Project Overview

This is a Nextflow evaluation pipeline for testing the `biolit` literature search agent
(`/Users/Rachel/Documents/lit-search-agent`) on the TF perturbation use case.

**Goal:** Assess how accurately `biolit` can screen GEO records for transcription factor
perturbation experiments and extract structured metadata, using a manually curated
ground truth spreadsheet as the reference.

**Ground truth source:** `ground_truth.tsv` — derived from `TF_Scrape_Sheet.xlsx` in the
`lit-search-agent` repo. Contains 509 GEO accessions with hand-curated labels for:
- `has_perturbation` (True/False)
- `tf_name` (transcription factor name, parsed from raw label)
- `perturbation_method` (KO / KD / OE / het / mutant / etc.)
- `organism` (from GEO `Taxa` field)
- `platform` (GPL accession from GEO `Platforms` field)

## Pipeline Structure

Three Nextflow processes, run sequentially:

### 1. SAMPLE
**Script:** `bin/sample_eval_set.py`
**Input:** `ground_truth.tsv`, `params.n_pos`, `params.n_neg`, `params.seed`
**Output:** `eval_sample.tsv` — N positives + N negatives randomly sampled from ground truth

### 2. RUN_PIPELINE
**Script:** `bin/run_pipeline.py`
**Input:** `eval_sample.tsv`
**Output:** `predictions.tsv` — one row per GEO accession with pipeline outputs:
  - `geo_accession`, `screened_positive`, `tf_name`, `perturbation_method`, `organism`, `platform`
**Notes:**
  - Calls `biolit` via CLI (`biolit --ids <accession> --criterion ... --fields ...`)
  - Screening criterion: *"Is there a transcription factor perturbation in this experiment?"*
  - Fields to extract: `transcription_factor`, `perturbation_method`, `organism`, `platform`
  - Model: `claude-haiku-4-5-20251001` for cost efficiency
  - Runner selectable via `params.runner` (`cli` or `mcp`)

### 3. SCORE
**Script:** `bin/score_eval.py`
**Input:** `predictions.tsv`, `ground_truth.tsv`
**Output:** `scores.txt` — evaluation report with:
  - Screening accuracy, precision, recall, F1 (has_perturbation)
  - Per-field extraction accuracy for `tf_name`, `perturbation_method`, `organism`, `platform`

## Parameters (`nextflow.config`)

| Parameter | Default | Description |
|---|---|---|
| `ground_truth` | `ground_truth.tsv` | Path to ground truth TSV |
| `n_pos` | `50` | Number of positive examples to sample |
| `n_neg` | `50` | Number of negative examples to sample |
| `seed` | `42` | Random seed for sampling |
| `runner` | `cli` | How to invoke biolit (`cli` or `mcp`) |
| `model` | `claude-haiku-4-5-20251001` | LLM model for screening + extraction |
| `outdir` | `results/` | Output directory |

## Environment

- **Conda:** base env at `/Users/Rachel/miniconda3`
- **Python:** `/Users/Rachel/miniconda3/bin/python3`
- **biolit:** installed in the `lit-search-agent` virtualenv; invoke via CLI
- **Nextflow:** DSL2

## Files

```
tf-perturb-eval/
├── CLAUDE.md
├── main.nf
├── nextflow.config
├── ground_truth.tsv
└── bin/
    ├── sample_eval_set.py
    ├── run_pipeline.py
    └── score_eval.py
```
