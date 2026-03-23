# TF Name Mismatches (True Positives)

Across 5 folds, **65 mismatches** out of all true-positive records where both `tf_name_pred` and `tf_name_truth` were compared (exact string match after lowercasing/stripping).

---

## 1. Empty prediction (8)

Model screened positive but extracted no TF name.

| GSE | tf_name_truth | perturbation_method | fold |
|-----|---------------|---------------------|------|
| GSE72350 | multiple | OE | 0 |
| GSE14336 | HIF1a | — | 0 |
| GSE43175 | tp53 | — | 0 |
| GSE24760 | tp53 | — | 1 |
| GSE9144 | tp53 | — | 2 |
| GSE54374 | ngn3 | KO | 2 |
| GSE21361 | oksm | — | 3 |
| GSE44401 | m2rta, gata4, tbx5, mef2c, SMARCD3, MYOCD, SRF, mesp1 | OE | 4 |

---

## 2. Alias / synonym — same gene, different name (7)

The predicted and ground truth names refer to the same gene but use different naming conventions.

| GSE | tf_name_pred | tf_name_truth | note | fold |
|-----|--------------|---------------|------|------|
| GSE10520 | RUNX1 | aml1/eto | AML1 is the old name for RUNX1 (fusion with ETO) | 0 |
| GSE29929 | PERK | eif2ak3 | PERK is protein name; EIF2AK3 is gene symbol | 0 |
| GSE43713 | CHOP | ddit3 | CHOP is protein name; DDIT3 is gene symbol | 0 |
| GSE33292 | TCF7 | tcf1 | TCF7 gene encodes the TCF1 protein | 2 |
| GSE33967 | MLXIP | mondoa | MLXIP gene encodes the MondoA protein | 3 |
| GSE21296 | KLF4 | kl4 | Likely typo in ground truth ("kl4" → "klf4") | 4 |
| GSE95364 | MEF2A | mfe2a | Typo in ground truth ("mfe2a" → "mef2a") | 3 |

---

## 3. Fusion / truncation / construct variants (5)

Pred identifies the canonical TF; truth specifies a fusion protein or engineered construct.

| GSE | tf_name_pred | tf_name_truth | fold |
|-----|--------------|---------------|------|
| GSE57658 | RUNX1 | runx1-eto truncation | 0 |
| GSE7324 | RUNX1T1 | aml1/eto, aml1/eto W692A | 1 |
| GSE28317 | RUNX1T1 | aml1-eto, aml1-eto ΔNHR1 | 2 |
| GSE8023 | RUNX1-RUNX1T1 | aml1-eto | 4 |
| GSE15646 | RUNX1T1 | aml1-eto | 4 |

---

## 4. Pred is subset of multi-TF truth (20)

Model correctly identified one TF but missed additional co-perturbed TFs listed in the ground truth.

| GSE | tf_name_pred | tf_name_truth | fold |
|-----|--------------|---------------|------|
| GSE40415 | TP53 | tp53, myc | 0 |
| GSE36804 | RBPJ | rbpj , rbpj | 0 |
| GSE19194 | CBFB | cbfb , cbfb , cbfb +/- | 1 |
| GSE19114 | CEBPB | cebpb , stat3 , bhlhb2 , fosl2, runx1 | 1 |
| GSE29179 | TAL1 | tal1 , tcf12/heb , e2a , gata3 , myb | 1 |
| GSE40155 | RUNX1 | runx1 , runx1 | 2 |
| GSE42234 | CEBPA | cebpa + pu.1 simultaneous | 2 |
| GSE92861 | MEF2A | mef2a , mef2c , mef2d | 2 |
| GSE152884 | MEF2A, MEF2C, MEF2D | Mef2a, Mef2c and Mef2d | 2 |
| GSE75150 | ATF4 | atf4 , cebpg | 3 |
| GSE63798 | MEF2A | mef2a, mef2b, mef2c, mef2d | 3 |
| GSE47350 | RUNX1 | Runx1/Cbfb | 3 |
| GSE53847 | ID1 | id1 id2 | 3 |
| GSE123797 | ZEB2 | zeb2 , zeb2 & nfil3 , zeb2 & id2 | 3 |
| GSE17231 | MEF2C | mef2c , mef2c | 4 |
| GSE64128 | MEF2 | mef2a/d | 4 |
| GSE49598 | ATF4 | eif2ak3 , atf4 , eIF2a S51A/S51A, Fv2E-eif2ak3 | 4 |
| GSE52200 | JARID2 | jarid2 , prdm14 , esrrb , sall14 , myc , OKSM | 4 |
| GSE123799 | BATF3 | id2 , batf3 | 4 |
| GSE68458 | NR4A | NR4A1, NR4A2, NR4A3, NR4A1/2, NR4A1/3, NR4A2/3, NR4A1/2/3 | 4 |

---

## 5. Pred is superset of truth / over-prediction (3)

Model predicted more TFs than the ground truth specifies.

| GSE | tf_name_pred | tf_name_truth | fold |
|-----|--------------|---------------|------|
| GSE1676 | ATM, TP53, RELA | tp53 | 1 |
| GSE118036 | CITED2, PU.1 | pu.1 | 4 |
| GSE48891 | PU.1, Spi-B | spi-b , pu.1 | 4 |

---

## 6. Wrong TF — completely different gene (8)

| GSE | tf_name_pred | tf_name_truth | fold |
|-----|--------------|---------------|------|
| GSE56875 | SNAI1 | gata4, mef2c, tbx5 | 0 |
| GSE122371 | ETV1 | FGFR1 | 0 |
| GSE173135 | EZH2 | Runx1 | 1 |
| GSE26366 | HES1 | etv6 runx1 pbx1 rearrangements, snps | 3 |
| GSE27914 | COP1 | etv1 , c-jun | 3 |
| GSE23692 | HDAC7 | mef2c | 4 |
| GSE21155 | RUNX1 | cbf-b | 4 |
| GSE45467 | PU.1 | irf8 | 4 |

---

## 7. Description noise / context in ground truth (14)

Ground truth contains genotype suffixes, ranking descriptors, or spacing differences that prevent exact matching even though the core gene name is correct.

| GSE | tf_name_pred | tf_name_truth | note | fold |
|-----|--------------|---------------|------|------|
| GSE67417 | MEF2B | MEF2B-V5 | construct tag in truth | 1 |
| GSE21209 | ETV4 | etv4 vs | stray "vs" in truth | 1 |
| GSE62897 | TP53 | p53 mKO vs | context suffix | 2 |
| GSE44140 | ID2 | high vs intermediate id2 expression | expression level description | 2 |
| GSE35897 | CUX2 | cux 2 | spacing in truth | 2 |
| GSE11756 | TWIST1 | twist1/2 | family notation | 3 |
| GSE19997 | POU4F1 | pouf1 vs | typo + context suffix | 3 |
| GSE13588 | FOXP2 | foxp2 hum/hum, foxp2 +/- | genotype details | 3 |
| GSE47568 | PROX1 | prox1 del, prox1 & apc del, apc del | deletion context | 3 |
| GSE98748 | RUNX1 | runx1 at different efficacies | description in truth | 3 |
| GSE117981 | PROX1 | prox1 pos vs neg | expression context | 4 |
| GSE47750 | JMJD2A, ETV1 | jmjd2a , etv1 | spacing only | 4 |
| GSE19684 | ATOH1 | gli1, math1/atoh1 | ATOH1 also called MATH1; gli1 not in pred | 3 |
| GSE33549 | THPOK | multiple | truth too vague | 2 |

---

## Summary

65 mismatches across 5 folds, broken down by category and root cause.

### By category (count / share)

| # | Category | Count | % of mismatches |
|---|----------|-------|-----------------|
| 4 | Pred is subset of multi-TF truth | 20 | 31% |
| 7 | Description noise in ground truth | 14 | 22% |
| 1 | Empty prediction | 8 | 12% |
| 6 | Wrong TF entirely | 8 | 12% |
| 2 | Alias / synonym | 7 | 11% |
| 3 | Fusion / construct variant | 5 | 8% |
| 5 | Pred is superset | 3 | 5% |

### What the source data reveals

**Category 4 — subset (20 cases, largest):** biolit reliably finds the first or most prominent TF in a study but stops there. Multi-perturbation designs (e.g., GSE29179: TAL1 predicted, but truth is tal1 + tcf12/heb + e2a + gata3 + myb) and family-wide knockdowns (GSE68458: NR4A predicted, truth lists NR4A1/2/3 and all double/triple combos) are systematically under-extracted.

**Category 7 — ground truth noise (14 cases):** Many of these are not biolit errors at all — the ground truth contains stray suffixes, spacing, typos, and genotype descriptors that break exact-match scoring. Examples:
- `etv4 vs` (stray "vs"), `cux 2` (extra space), `MEF2B-V5` (construct tag)
- `prox1 del, prox1 & apc del, apc del` (deletion context embedded in name field)
- `mfe2a` / `kl4` (typos in ground truth)
These inflate the mismatch count and should be cleaned before re-scoring.

**Category 6 — wrong TF (8 cases):** Four failure modes visible in the source data:
- *Contextually prominent co-factor mistaken for perturbation target:* GSE45467 — study is about how PU.1 regulates Irf8 for DC fate; biolit extracted PU.1 (the causal narrative actor) rather than IRF8 (the gene actually perturbed).
- *Named inhibitor/control confused with experimental variable:* GSE56875 — GMT (Gata4/Mef2c/Tbx5) reprogramming study; SNAI1 appears as a negative control whose overexpression was tested, and biolit latched onto it instead.
- *Complex multi-gene model:* GSE173135 — BRSST sgRNA background (includes Runx1) plus sgEzh2 added on top; biolit identified EZH2 (the experimentally varied gene) while ground truth records Runx1 as the TF of interest.
- *Non-TF perturbed, downstream TF extracted:* GSE122371 — dominant-negative FGFR1 (a receptor kinase) is the perturbation; ETV1 is a downstream transcriptional target that biolit named instead.

**Category 2 — alias/synonym (7 cases):** biolit consistently uses standard HGNC gene symbols or widely-used protein names. Ground truth uses a mix of protein names (CHOP, PERK, MondoA, TCF1, AML1) and gene symbols (DDIT3, EIF2AK3, MLXIP, TCF7, RUNX1). In every alias case (GSE29929, GSE43713, GSE33967, GSE33292), biolit's answer is biologically correct — this is purely a normalization gap in scoring.

**Category 1 — empty prediction (8 cases):** Three sub-patterns:
- *Multi-TF OE screens:* GSE72350 (49 TFs induced), GSE44401 (8-TF cardiac reprogramming cocktail) — too many TFs for biolit to commit to one name.
- *TP53 studies where p53 is mechanistic context, not the stated subject:* GSE43175 (neuronal conversion efficiency study), GSE24760, GSE9144 — biolit screens positive (correctly) but can't identify which TF to name.
- *Unusual TF:* GSE14336 — HIF1a in p53-mutant lymphoma study; both HIF1a and p53 are present, and the complex design may prevent extraction.

### Actionable fixes

| Fix | Addresses | Effort |
|-----|-----------|--------|
| Normalize ground truth TF names (aliases, typos, strip suffixes) | Cat. 2, 7 | Low — ground truth cleanup |
| Map protein names ↔ gene symbols in scoring (CHOP→DDIT3 etc.) | Cat. 2 | Low — scoring script |
| Prompt biolit to extract *all* perturbed TFs, not just the primary | Cat. 4 | Medium — prompt engineering |
| Add Jaccard partial-credit for subset/superset matches | Cat. 4, 5 | Low — already partially done for tf_name |
| Improve fusion/construct normalization (AML1/ETO → RUNX1-RUNX1T1) | Cat. 3 | Medium — alias table |

### Not fixable in scoring

Categories 6 (wrong TF) and parts of category 1 (empty on complex designs) reflect genuine model limitations — biolit is extracting the most contextually salient TF rather than the experimentally manipulated one. Fixing these requires changes to the biolit prompt or retrieval strategy, not the scoring pipeline.
