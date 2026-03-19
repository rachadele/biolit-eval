# tf-perturb-eval

Nextflow pipeline for evaluating the `biolit` literature search agent on transcription factor perturbation experiments in GEO.

## Overview

The pipeline runs stratified k-fold cross-validation over a manually curated ground truth (`assets/ground_truth.tsv`, 509 accessions). Each fold runs `biolit` to screen and extract metadata; per-fold scores are aggregated and plotted.

**Pipeline steps:**
1. **CREATE_FOLDS** — stratified k-fold split of all 509 accessions
2. **RUN_BIOLIT** — screens and extracts fields via `biolit` CLI (one job per fold, parallelized)
3. **PARSE_PREDICTIONS** — maps biolit output to structured predictions
4. **SCORE** — computes screening metrics and field extraction accuracy per fold
5. **AGGREGATE** — concatenates per-fold scores into `all_scores.tsv`
6. **PLOT** — box-and-whisker plots with scatter overlay (one box per metric per fold)

## Usage

```bash
nextflow run main.nf -profile conda
```

Override defaults:

```bash
nextflow run main.nf -profile conda --k_folds 10 --seed 123
```

## Parameters

| Parameter | Default | Description |
|---|---|---|
| `k_folds` | `5` | Number of CV folds |
| `seed` | `42` | Random seed for fold splitting |
| `field_map` | `null` | Optional `biolit_field:truth_col,...` mapping override |
| `jaccard_fields` | `tf_name` | Fields scored with Jaccard instead of exact match |
| `screening_truth_col` | `has_perturbation` | Ground truth column for screening evaluation |
| `biolit_config` | `config.json` | Biolit config JSON |
| `outdir` | `results` | Output directory |

## Output

Results are written to `results/`:
- `fold_{i}/biolit_results.csv` — raw biolit output per fold
- `fold_{i}/predictions.tsv` — parsed predictions per fold
- `fold_{i}/scores.tsv` — per-fold metrics (includes `fold` column)
- `fold_{i}/merged.tsv` — predictions joined with ground truth per fold
- `all_scores.tsv` — all folds concatenated
- `scores.png` — box-and-whisker plots of screening and extraction metrics

## Notes

- `notes/tf_name_eval.md` — TF name evaluation strategy (alias resolution is a planned follow-on)
- `notes/field_mapping.md` — field name / prompt coupling and planned decoupling
