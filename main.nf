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

    input:
    path accessions

    output:
    path 'biolit_results.csv'

    script:
    """
    biolit ${accessions} \
        --criterion "${params.criterion}" \
        --fields "${params.fields}" \
        --model ${params.model} \
        --output results.csv
    mv run_*/results.csv biolit_results.csv
    """
}

process PARSE_PREDICTIONS {
publishDir params.outdir, mode: 'copy'

    input:
    path biolit_csv
    path eval_sample

    output:
    path 'predictions.tsv'

    script:
    """
    parse_predictions.py \
        --biolit_csv ${biolit_csv} \
        --eval_sample ${eval_sample} \
        --output predictions.tsv
    """
}

process SCORE {
    publishDir params.outdir, mode: 'copy'

    input:
    path predictions
    path ground_truth

    output:
    path 'scores.tsv'

    script:
    """
    score_eval.py \
        --predictions ${predictions} \
        --ground_truth ${ground_truth} \
        --output scores.tsv
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
    ground_truth = file(params.ground_truth)

    SAMPLE(ground_truth)
    biolit_csv  = RUN_BIOLIT(SAMPLE.out.ids)
    predictions = PARSE_PREDICTIONS(biolit_csv, SAMPLE.out.sample)
    scores      = SCORE(predictions, ground_truth)
    PLOT(scores)
}
