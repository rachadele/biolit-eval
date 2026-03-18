# TF Name Evaluation

The ground truth uses informal/aliased gene names (`tp53`, `pu.1`, `aml1-eto`, `runx1/eto`)
while biolit should return HGNC symbols. Simple string matching underestimates performance.

## Options

### 1. MyGene.io lookup (recommended follow-on)
Query both predicted and truth names against the MyGene.io API to resolve to canonical
Entrez gene IDs, then compare IDs. Handles aliases, capitalisation, and outdated symbols.
Requires `mygene` pip package and API calls at scoring time.

### 2. Hardcoded alias map
Map known aliases in the ground truth (`tp53→TP53`, `pu.1→SPI1`, `aml1→RUNX1`) manually.
Brittle and incomplete.

### 3. Jaccard on normalised sets (current baseline)
Split comma-separated lists, lowercase + strip both sides, compute intersection/union.
Zero-dependency and handles capitalisation and multi-TF partial credit, but will
underestimate performance wherever aliases differ (e.g. `pu.1` vs `SPI1`).

## Decision
Implement option 3 as a baseline. Add option 1 as a follow-on once the rest of the
pipeline is validated.
