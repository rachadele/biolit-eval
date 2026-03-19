# tf-perturb-eval

Nextflow pipeline for evaluating the `biolit` literature search agent on transcription factor perturbation experiments in GEO.

## Overview

The pipeline samples GEO accessions from a manually curated ground truth (`assets/ground_truth.tsv`, 509 accessions), runs `biolit` to screen and extract metadata, and scores predictions against the ground truth labels.

**Pipeline steps:**
1. **SAMPLE** — stratified sample of N positive + N negative accessions
2. **RUN_BIOLIT** — screens and extracts fields via `biolit` CLI
3. **PARSE_PREDICTIONS** — maps biolit output to structured predictions
4. **SCORE** — computes screening metrics and field extraction accuracy
5. **PLOT** — bar charts of all metrics

## Usage

```bash
nextflow run main.nf -profile conda
```

Override defaults:

```bash
nextflow run main.nf -profile conda --n_pos 20 --n_neg 20 --seed 123
```

## Parameters

| Parameter | Default | Description |
|---|---|---|
| `n_pos` | `50` | Positive examples to sample |
| `n_neg` | `50` | Negative examples to sample |
| `seed` | `42` | Random seed |
| `model` | `claude-haiku-4-5-20251001` | LLM model |
| `criterion` | *Is there a TF perturbation?* | Biolit screening question |
| `fields` | `organism_scientific_name,platform_gpl_accession` | Fields to extract |
| `field_map` | `null` | Optional `biolit_field:truth_col,...` mapping override (see below) |
| `outdir` | `results/` | Output directory |

## Output

Results are written to `results/`:
- `eval_sample.tsv` — sampled accessions with ground truth labels
- `predictions.tsv` — biolit screening and extraction results
- `scores.tsv` — accuracy, precision, recall, F1 and per-field extraction accuracy
- `scores.png` — bar charts of screening and extraction metrics

## Notes

- `notes/tf_name_eval.md` — TF name evaluation strategy (alias resolution is a planned follow-on)
- `notes/field_mapping.md` — field name / prompt coupling and planned decoupling
