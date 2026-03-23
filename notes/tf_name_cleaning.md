# tf_name Ground Truth Cleaning

Proposed changes to `assets/ground_truth.tsv` `tf_name` column before re-running `build_synonym_map.py`.

## 1. Remove noise/descriptor text
Strip "vs", "pos vs neg", "high vs low", mutation annotations (+/-, K288X, Q202L, mKO, del, null, truncation, ΔNHR1, hum/hum, etc.) and "construct" suffixes.

- `'bcl11a +/- vs'` → `bcl11a`
- `'klf1 K288X/+'` → `klf1`
- `'prox1 del, prox1 & apc del, apc del'` → `prox1`
- `'p53 mKO vs'` → `tp53`
- `'cbfb , cbfb +/- (wt)'` → `cbfb`
- `'foxp2 hum/hum, foxp2 +/-'` → `foxp2`
- `'pu.1 Q202L/pu.1 Q202L'` → `pu.1`
- `'aml1-eto , aml1-eto ΔNHR1 construct'` → `runx1, runx1t1`
- `'aml1/eto , aml1/eto W692A'` → `runx1, runx1t1`
- `'runx1 at different efficacies'` → `runx1`
- `'runx1 mut and correction'` → `runx1`
- `'runx1 null'` → `runx1`
- `'runx1-eto truncation'` → `runx1, runx1t1`
- `'etv4 vs'` → `etv4`
- `'pouf1 vs'` → `pou5f1`
- `'id2 pos vs neg'` → `id2`
- `'id3 high vs id3 low'` → `id3`
- `'high vs intermediate id2 expression'` → `id2`
- `'MEF2B-V5'` → `mef2b`  (V5 is a tag)
- `'cebpa methylation'` → `cebpa`

## 2. Normalize separators & deduplicate
Replace "and", "&", "+" with comma; deduplicate within a cell.

- `'Gfi-1 , Gfi-1 and id2'` → `Gfi-1, id2`
- `'cbfb , cbfb , cbfb +/-'` → `cbfb`
- `'mef2c , mef2c'` → `mef2c`
- `'rbpj , rbpj'` → `rbpj`
- `'cebpa + pu.1 simultaneous'` → `cebpa, pu.1`
- `'foxl2 , runx1 , foxl2 &runx1'` → `foxl2, runx1`
- `'id1 id2'` → `id1, id2`
- `'runx1 runx2 runx3 and all combos'` → `runx1, runx2, runx3`
- `'runx1 tal1 prmt6 prmt3'` → `runx1, tal1, prmt6, prmt3`

## 3. Split fusion proteins
Expand hyphen/slash fusions into component genes.

- `'aml1-eto'`, `'aml1/eto'`, `'runx1/eto'` → `runx1, runx1t1`
- `'etv6/runx1'` → `etv6, runx1`
- `'Runx1/Cbfb'` → `runx1, cbfb`
- `'twist1/2'` → `twist1, twist2`
- `'mef2a/d'` → `mef2a, mef2d`
- `'cebp a/b'` → `cebpa, cebpb`
- `'tip5/baz2a'` → `baz2a`  (tip5 is an alias for baz2a)
- `'runx1&3'` → `runx1, runx3`

## 4. Fix typos / informal names

- `'mfe2a'` → `mef2a`
- `'kl4'` → `klf4`  (NCBI matched to Igkv4-60 — clearly wrong)
- `'cebp a'` → `cebpa`
- `'cbf-b'` → `cbfb`

## 5. Expand abbreviations

- `'oksm'` / `'OKSM'` → `oct4, klf4, sox2, myc`
- `'jarid2 , jarid2 , prdm14 , esrrb , sall14 , myc , OKSM'` → `jarid2, prdm14, esrrb, sall14, myc, oct4, klf4, sox2`

## 6. Ambiguous / non-resolvable → NaN

- `'multiple'`
- `'foxp'`  (no number — ambiguous family)
- `'foxa'`  (no number — ambiguous family)
- `'runx'`  (no number — ambiguous)
- `'induced runx'`
- `'koxp1'`  (doesn't exist as a gene)
- `'m2rta'`  (construct name, not a gene symbol)
- `'Fv2E-eif2ak3'`  (inducible construct — strip, leave just `eif2ak3, atf4`)
- `'etv6 runx1 pbx1 rearrangements, snps'` → `etv6, runx1, pbx1`  (or NaN — uncertain)

## 7. NR4A redundancy
Collapse pairwise/triple combos to unique genes.

- `'NR4A1 , NR4A2 , NR4A3 , NR4A1/2 , NR4A1/3 , NR4A2/3 , NR4A1/2/3'` → `NR4A1, NR4A2, NR4A3`

## After cleaning
Re-run `build_synonym_map.py` to regenerate `assets/gene_synonyms.json`.
