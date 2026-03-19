# TF Name Harmonization Issues

Diagnosed from `results/merged.tsv` (run 2026-03-19, seed=42, n=100).

`organism` and `platform` match perfectly after adding merge suffixes. All issues below are specific to `tf_name`.

## Problem categories

### 1. Case differences (handled by `norm()`)
Not a real problem — `norm()` lowercases both sides before comparison.

### 2. Multi-TF experiments — biolit returns only one
Will always fail exact match. Requires set/Jaccard matching.

| GSE | pred | truth |
|---|---|---|
| GSE42979 | `PIAS3` | `stat3, pias3` |
| GSE163291 | `HEY1` | `runx2 , hey1` |
| GSE47350 | `RUNX1` | `Runx1/Cbfb` |
| GSE94835 | `RUNX1` | `runx1 runx2 runx3 and all combos` |
| GSE13504 | `TP73` | `tp53, tp73` |

### 3. Alias mismatches — biolit uses HGNC symbol, truth uses alias
Requires alias resolution (e.g. MyGene.io).

| GSE | pred | truth | note |
|---|---|---|---|
| GSE43713 | `CHOP` | `ddit3` | CHOP is alias for DDIT3 |
| GSE27914 | `COP1` | `etv1 , c-jun` | completely wrong TF |

### 4. Empty prediction on true positives
Biolit failed to extract a TF name despite screening positive.

GSE23038, GSE32675, GSE9144, GSE125811, GSE81723, GSE27869

### 5. Python list format from biolit (parse bug)
Biolit returns a list; `parse_predictions.py` stores the raw Python repr instead of a normalized string. Exact match always fails.

| GSE | pred | truth |
|---|---|---|
| GSE48486 | `['HNF1B', 'FOXA3']` | `foxa3, hnf1b` |
| GSE27304 | `['SPI1', 'CEBPA', 'MNDA', 'IRF8']` | `spi1 , cebpa , irf8` |

**Fix:** in `parse_predictions.py`, detect list values and join them as a comma-separated string.

### 6. Family name vs individual members
| GSE | pred | truth |
|---|---|---|
| GSE68458 | `NR4A` | `NR4A1 , NR4A2 , NR4A3 , NR4A1/2 , NR4A1/3 , NR4A2/3 , NR4A1/2/3` |

## Recommended fixes (priority order)

1. **Fix Python list format** in `parse_predictions.py` — low effort, immediate gain
2. **Jaccard/set matching** for multi-TF cases — implement as alternative metric in `score_eval.py`
3. **Alias resolution** via MyGene.io — see `tf_name_eval.md` for strategy
