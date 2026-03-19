# K-Fold CV Pipeline Plan

## Files changed

| File | Action |
|---|---|
| `nextflow.config` | Replace `n_pos`/`n_neg` with `k_folds = 5`; keep `seed` |
| `main.nf` | Full rewrite: new process set + fan-out/fan-in workflow |
| `bin/create_folds.py` | **New** — stratified k-fold split, outputs `fold_{i}_test.tsv` + `fold_{i}_accessions.txt` |
| `bin/score_eval.py` | Add `--fold` arg → stamps `fold` column into every output row |
| `bin/aggregate_scores.py` | **New** — concatenates all per-fold `scores.tsv` into `all_scores.tsv` |
| `bin/plot_scores.py` | Replace bar charts with box-and-whisker + scatter overlay |
| `bin/sample_eval_set.py` | Keep on disk (usable standalone), no longer called by pipeline |

---

## Data flow

```
ground_truth.tsv
       │
  CREATE_FOLDS  ──── fold_0_test.tsv, fold_0_accessions.txt
                ──── fold_1_test.tsv, fold_1_accessions.txt
                ──── ...
       │
  (per fold, parallelized)
       │
  RUN_BIOLIT(fold_id, accessions.txt)   →   (fold_id, biolit_results.csv)
       │
  PARSE_PREDICTIONS(fold_id, biolit_csv, test.tsv)   →   (fold_id, predictions.tsv)
       │
  SCORE(fold_id, predictions.tsv)   →   (fold_id, scores.tsv)   ← stamped with fold
       │
  scores.collect()
       │
  AGGREGATE   →   all_scores.tsv
       │
  PLOT   →   scores.png  (box-and-whisker, one box per metric per panel)
```

---

## main.nf channel wiring

The trickiest part. `fold_id` is threaded as a tuple key through all per-fold processes:

1. `CREATE_FOLDS` outputs two globs: `fold_*_test.tsv` and `fold_*_accessions.txt`
2. Both are `.flatten()`-ed and `.map`-ed to `(fold_id, file)` by parsing the fold index from filename
3. Accessions and test TSVs are kept in sync via `.join(by: 0)` on `fold_id`
4. All per-fold processes use `tuple val(fold_id), path(...)` inputs and `publishDir { "${params.outdir}/fold_${fold_id}" }` (closure syntax required — plain string won't have `fold_id` in scope)
5. After SCORE, `.map { id, f -> f }.collect()` strips fold_id and gathers all scores files into a flat list for AGGREGATE

---

## Process definitions

### CREATE_FOLDS
```groovy
process CREATE_FOLDS {
    input:
    path ground_truth

    output:
    path 'folds/fold_*_test.tsv',        emit: test_tsvs
    path 'folds/fold_*_accessions.txt',  emit: acc_txts

    script:
    """
    create_folds.py \
        --ground_truth ${ground_truth} \
        --k ${params.k_folds} \
        --seed ${params.seed} \
        --outdir folds
    """
}
```

### RUN_BIOLIT
Do not publish artifacts from individual fold runs — they are large and not needed for evaluation.

```groovy
process RUN_BIOLIT {
    conda '/Users/Rachel/miniconda3'
    tag "fold_${fold_id}"
    publishDir { "${params.outdir}/fold_${fold_id}" }, mode: 'copy'

    input:
    tuple val(fold_id), path(accessions), path(biolit_config)

    output:
    tuple val(fold_id), path('biolit_results.csv'), emit: csv

    script:
    """
    biolit ${accessions} --config ${biolit_config} --output results.csv
    mv run_*/results.csv biolit_results.csv
    """
}
```

### PARSE_PREDICTIONS
```groovy
process PARSE_PREDICTIONS {
    tag "fold_${fold_id}"
    publishDir { "${params.outdir}/fold_${fold_id}" }, mode: 'copy'

    input:
    tuple val(fold_id), path(biolit_csv), path(eval_sample), path(biolit_config)

    output:
    tuple val(fold_id), path('predictions.tsv')

    script:
    """
    parse_predictions.py \
        --biolit_csv ${biolit_csv} \
        --eval_sample ${eval_sample} \
        --config ${biolit_config} \
        --output predictions.tsv
    """
}
```

### SCORE
```groovy
process SCORE {
    tag "fold_${fold_id}"
    publishDir { "${params.outdir}/fold_${fold_id}" }, mode: 'copy'

    input:
    tuple val(fold_id), path(predictions), path(ground_truth), path(biolit_config)

    output:
    tuple val(fold_id), path('scores.tsv'), emit: scores
    tuple val(fold_id), path('merged.tsv'), emit: merged

    script:
    """
    score_eval.py \
        --predictions ${predictions} \
        --ground_truth ${ground_truth} \
        --config ${biolit_config} \
        --screening_truth_col ${params.screening_truth_col} \
        ${params.field_map ? "--field_map \"${params.field_map}\"" : ""} \
        ${params.jaccard_fields ? "--jaccard_fields \"${params.jaccard_fields}\"" : ""} \
        --fold ${fold_id} \
        --output scores.tsv \
        --merged_output merged.tsv
    """
}
```

### AGGREGATE
```groovy
process AGGREGATE {
    publishDir params.outdir, mode: 'copy'

    input:
    path scores_files

    output:
    path 'all_scores.tsv'

    script:
    """
    aggregate_scores.py --scores ${scores_files} --output all_scores.tsv
    """
}
```

### PLOT
```groovy
process PLOT {
    publishDir params.outdir, mode: 'copy'

    input:
    path all_scores

    output:
    path 'scores.png'

    script:
    """
    plot_scores.py \
        --scores ${all_scores} \
        --screening_truth_col ${params.screening_truth_col} \
        --output scores.png
    """
}
```

### Workflow block
```groovy
workflow {
    ground_truth  = file(params.ground_truth)
    biolit_config = file(params.biolit_config)

    CREATE_FOLDS(ground_truth)

    fold_test_ch = CREATE_FOLDS.out.test_tsvs
        .flatten()
        .map { tsv ->
            def fold_id = (tsv.name =~ /fold_(\d+)_test\.tsv/)[0][1].toInteger()
            tuple(fold_id, tsv)
        }

    fold_acc_ch = CREATE_FOLDS.out.acc_txts
        .flatten()
        .map { acc ->
            def fold_id = (acc.name =~ /fold_(\d+)_accessions\.txt/)[0][1].toInteger()
            tuple(fold_id, acc)
        }

    biolit_input_ch = fold_acc_ch
        .map { fold_id, acc -> tuple(fold_id, acc, biolit_config) }

    RUN_BIOLIT(biolit_input_ch)

    parse_input_ch = RUN_BIOLIT.out.csv
        .join(fold_test_ch, by: 0)
        .map { fold_id, csv, tsv -> tuple(fold_id, csv, tsv, biolit_config) }

    PARSE_PREDICTIONS(parse_input_ch)

    score_input_ch = PARSE_PREDICTIONS.out
        .map { fold_id, preds -> tuple(fold_id, preds, ground_truth, biolit_config) }

    SCORE(score_input_ch)

    all_scores_ch = SCORE.out.scores
        .map { fold_id, scores_tsv -> scores_tsv }
        .collect()

    AGGREGATE(all_scores_ch)
    PLOT(AGGREGATE.out)
}
```

---

## bin/create_folds.py spec

```python
#!/usr/bin/env python3
"""Create stratified k-fold splits from ground_truth.tsv."""
import argparse, os
import pandas as pd
from sklearn.model_selection import StratifiedKFold

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ground_truth", required=True)
    parser.add_argument("--k", type=int, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    df = pd.read_csv(args.ground_truth, sep="\t")
    skf = StratifiedKFold(n_splits=args.k, shuffle=True, random_state=args.seed)

    for fold_id, (_, test_idx) in enumerate(skf.split(df, df["has_perturbation"])):
        test_df = df.iloc[test_idx]
        test_df.to_csv(f"{args.outdir}/fold_{fold_id}_test.tsv", sep="\t", index=False)
        with open(f"{args.outdir}/fold_{fold_id}_accessions.txt", "w") as f:
            f.write("\n".join(test_df["geo_accession"].tolist()) + "\n")
        n_pos = (test_df["has_perturbation"] == True).sum()
        print(f"Fold {fold_id}: {len(test_df)} rows ({n_pos} pos, {len(test_df)-n_pos} neg)")

if __name__ == "__main__":
    main()
```

---

## bin/aggregate_scores.py spec

```python
#!/usr/bin/env python3
"""Concatenate per-fold scores.tsv files into a single all_scores.tsv."""
import argparse
import pandas as pd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    dfs = [pd.read_csv(p, sep="\t") for p in args.scores]
    combined = pd.concat(dfs, ignore_index=True)
    if "fold" not in combined.columns:
        raise ValueError("Input scores files missing 'fold' column — re-run score_eval.py with --fold.")
    combined.to_csv(args.output, sep="\t", index=False)
    folds = sorted(combined["fold"].unique())
    print(f"Aggregated {len(folds)} folds, {len(combined)} rows → {args.output}")

if __name__ == "__main__":
    main()
```

---

## bin/plot_scores.py changes

Replace `ax.bar()` with boxplot + scatter overlay:

```python
def boxplot_panel(ax, data, group_label, title, ylabel):
    sub = data[data["group"] == group_label]
    if sub.empty:
        ax.set_visible(False)
        return
    metrics = sub["metric"].unique()
    plot_data = [sub[sub["metric"] == m]["value"].dropna().tolist() for m in metrics]
    ax.boxplot(plot_data, labels=metrics, patch_artist=True)
    ax.set_ylim(0, 1)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=20)
    for i, vals in enumerate(plot_data, start=1):
        ax.scatter([i] * len(vals), vals, alpha=0.5, s=20, color="black", zorder=3)
```

Use `fig.suptitle(f"K-Fold CV  (k={scores['fold'].nunique()})")` and `bbox_inches="tight"` on `savefig`.

The screening panel title should include the actual truth column name used for screening (e.g. `has_perturbation`). Since `all_scores.tsv` contains the screening rows, derive it from the data: `screening["metric"].unique()` will contain `accuracy`, `precision`, `recall`, `f1` — but the truth column name is not stored there. Two options:
- Pass `params.screening_truth_col` through to `plot_scores.py` as a `--screening_truth_col` arg and use it as a subtitle or axis label on the screening panel
- Store it as a metadata row in `all_scores.tsv` (simpler: just pass as CLI arg)

**Decision:** add `--screening_truth_col` arg to `plot_scores.py`; set the screening panel title to `f"Screening ({screening_truth_col})"`. Pass it from the PLOT process in `main.nf` via `${params.screening_truth_col}`.

---

## score_eval.py change

Add one argument and stamp rows:

```python
parser.add_argument("--fold", type=int, default=None)
...
if args.fold is not None:
    for r in rows:
        r["fold"] = args.fold
```

---

## Edge cases

- **publishDir closure:** must use `{ "${params.outdir}/fold_${fold_id}" }` — plain string won't resolve `fold_id`
- **File collisions:** each fold runs in isolated Nextflow work dir; publishDir routes copies to `results/fold_0/` etc.
- **AGGREGATE path expansion:** `${scores_files}` expands to space-separated paths; `nargs="+"` handles correctly
- **NaN in plots:** `boxplot` drops NaNs silently; `dropna()` before scatter; degenerate box if all folds NaN for a metric
- **Resume:** each `RUN_BIOLIT` fold independently cached — one failed fold can retry with `-resume`
- **Class balance:** 509 rows, 276 pos / 233 neg → ~101 rows/fold, `StratifiedKFold` ensures approximate balance
