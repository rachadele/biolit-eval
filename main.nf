#!/usr/bin/env nextflow
nextflow.enable.dsl=2

process SAMPLE {
publishDir params.outdir, mode: 'copy'

    input:
    path ground_truth

    output:
    path 'eval_sample.tsv', emit: sample
    path 'accessions.txt',  emit: ids

    script:
    """
    sample_eval_set.py \
        --ground_truth ${ground_truth} \
        --n_pos ${params.n_pos} \
        --n_neg ${params.n_neg} \
        --seed ${params.seed} \
        --output eval_sample.tsv \
        --ids_output accessions.txt
    """
}

process RUN_BIOLIT {
    conda '/Users/Rachel/miniconda3'
    publishDir params.outdir, mode: 'copy'

    input:
    path accessions
    path biolit_config

    output:
    path 'biolit_results.csv', emit: csv
    path 'artifacts/**',       emit: artifacts, optional: true

    script:
    """
    biolit ${accessions} \
        --config ${biolit_config} \
        --output results.csv
    mv run_*/results.csv biolit_results.csv

    # reorganize artifacts: run_<ts>/artifacts/<GSE>_<title>/ -> artifacts/<GSE>/
    mkdir -p artifacts
    for d in run_*/artifacts/*/; do
        gse=\$(basename "\$d" | grep -oE '^GSE[0-9]+')
        [ -n "\$gse" ] && cp -r "\$d" "artifacts/\$gse"
    done
    """
}

process PARSE_PREDICTIONS {
publishDir params.outdir, mode: 'copy'

    input:
    path biolit_csv
    path eval_sample
    path biolit_config

    output:
    path 'predictions.tsv'

    script:
    """
    parse_predictions.py \
        --biolit_csv ${biolit_csv} \
        --eval_sample ${eval_sample} \
        --config ${biolit_config} \
        --output predictions.tsv
    """
}

process SCORE {
    publishDir params.outdir, mode: 'copy'

    input:
    path predictions
    path ground_truth
    path biolit_config

    output:
    path 'scores.tsv',  emit: scores
    path 'merged.tsv',  emit: merged

    script:
    """
    score_eval.py \
        --predictions ${predictions} \
        --ground_truth ${ground_truth} \
        --config ${biolit_config} \
        --screening_truth_col ${params.screening_truth_col} \
        ${params.field_map ? "--field_map \"${params.field_map}\"" : ""} \
        ${params.jaccard_fields ? "--jaccard_fields \"${params.jaccard_fields}\"" : ""} \
        --output scores.tsv \
        --merged_output merged.tsv
    """
}

process PLOT {
    publishDir params.outdir, mode: 'copy'

    input:
    path scores

    output:
    path 'scores.png'

    script:
    """
    plot_scores.py \
        --scores ${scores} \
        --output scores.png
    """
}

workflow {
    ground_truth  = file(params.ground_truth)
    biolit_config = file(params.biolit_config)

    SAMPLE(ground_truth)
    biolit_csv  = RUN_BIOLIT(SAMPLE.out.ids, biolit_config).csv
    predictions = PARSE_PREDICTIONS(biolit_csv, SAMPLE.out.sample, biolit_config)
    SCORE(predictions, ground_truth, biolit_config)
    PLOT(SCORE.out.scores)
}
