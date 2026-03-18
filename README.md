# tf-perturb-eval

Nextflow pipeline for evaluating the [`biolit`](https://github.com/your-org/lit-search-agent) literature search agent on transcription factor perturbation experiments in GEO.

## Overview

The pipeline samples GEO accessions from a manually curated ground truth, runs `biolit` to screen and extract metadata, and scores predictions against the ground truth labels.

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
| `criterion` | *(TF perturbation question)* | Biolit screening criterion |
| `fields` | `transcription_factor,...` | Fields to extract |
| `outdir` | `results/` | Output directory |

## Output

Results are written to `results/`:
- `eval_sample.tsv` — sampled accessions with ground truth labels
- `predictions.tsv` — biolit screening and extraction results
- `scores.txt` — accuracy, precision, recall, F1 and per-field extraction accuracy
