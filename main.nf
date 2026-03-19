#!/usr/bin/env nextflow
nextflow.enable.dsl=2

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
    biolit ${accessions} \
        --config ${biolit_config} \
        --output results.csv
    mv run_*/results.csv biolit_results.csv
    """
}

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
