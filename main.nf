#!/usr/bin/env nextflow
nextflow.enable.dsl=2

process CREATE_BOOTSTRAP_SAMPLES {
    input:
    path ground_truth

    output:
    path 'bootstraps/bootstrap_*_sample.tsv',        emit: sample_tsvs
    path 'bootstraps/bootstrap_*_accessions.txt',    emit: acc_txts

    script:
    """
    create_bootstrap_samples.py \
        --ground_truth ${ground_truth} \
        --n_bootstraps ${params.n_bootstraps} \
        ${params.bootstrap_size ? "--bootstrap_size ${params.bootstrap_size}" : ""} \
        --seed ${params.seed} \
        --outdir bootstraps
    """
}

process RUN_BIOLIT {
    conda '/Users/Rachel/miniconda3'
    tag "bootstrap_${bootstrap_id}"
    storeDir "${params.outdir}/bootstrap_${bootstrap_id}"
    publishDir { "${params.outdir}/bootstrap_${bootstrap_id}" }, mode: 'move'

    input:
    tuple val(bootstrap_id), path(accessions), path(biolit_config)

    output:
    tuple val(bootstrap_id), path('biolit_results.csv'), emit: csv
    path 'artifacts', optional: true

    script:
    """
    biolit ${accessions} \
        --config ${biolit_config} \
        --output results.csv
    mv run_*/results.csv biolit_results.csv
    """
}

process PARSE_PREDICTIONS {
    tag "bootstrap_${bootstrap_id}"
    publishDir { "${params.outdir}/bootstrap_${bootstrap_id}" }, mode: 'copy'

    input:
    tuple val(bootstrap_id), path(biolit_csv), path(eval_sample), path(biolit_config)

    output:
    tuple val(bootstrap_id), path('predictions.tsv')

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
    tag "bootstrap_${bootstrap_id}"
    publishDir { "${params.outdir}/bootstrap_${bootstrap_id}" }, mode: 'copy'

    input:
    tuple val(bootstrap_id), path(predictions), path(ground_truth), path(biolit_config)

    output:
    tuple val(bootstrap_id), path("bootstrap_${bootstrap_id}_scores.tsv"), emit: scores
    tuple val(bootstrap_id), path("bootstrap_${bootstrap_id}_merged.tsv"), emit: merged
    tuple val(bootstrap_id), path("bootstrap_${bootstrap_id}_errors.tsv"), emit: errors

    script:
    """
    score_eval.py \
        --predictions ${predictions} \
        --ground_truth ${ground_truth} \
        --config ${biolit_config} \
        --screening_truth_col ${params.screening_truth_col} \
        ${params.field_map ? "--field_map \"${params.field_map}\"" : ""} \
        ${params.jaccard_fields ? "--jaccard_fields \"${params.jaccard_fields}\"" : ""} \
        ${params.synonym_map ? "--synonym_map ${params.synonym_map}" : ""} \
        --bootstrap ${bootstrap_id} \
        --output bootstrap_${bootstrap_id}_scores.tsv \
        --merged_output bootstrap_${bootstrap_id}_merged.tsv \
        --errors_output bootstrap_${bootstrap_id}_errors.tsv
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

process AGGREGATE_ERRORS {
    publishDir params.outdir, mode: 'copy'

    input:
    path errors_files

    output:
    path 'screening_errors.tsv'

    script:
    """
    aggregate_scores.py --scores ${errors_files} --output screening_errors.tsv
    """
}

process AGGREGATE_MERGED {
    publishDir params.outdir, mode: 'copy'

    input:
    path merged_files

    output:
    path 'all_merged.tsv'

    script:
    """
    aggregate_scores.py --scores ${merged_files} --output all_merged.tsv
    """
}

process PLOT_ERRORS {
    publishDir params.outdir, mode: 'copy'

    input:
    path screening_errors

    output:
    path 'errors.png'

    script:
    """
    plot_errors.py \
        --errors ${screening_errors} \
        --output errors.png
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

    CREATE_BOOTSTRAP_SAMPLES(ground_truth)

    sample_ch = CREATE_BOOTSTRAP_SAMPLES.out.sample_tsvs
        .flatten()
        .map { tsv ->
            def bootstrap_id = (tsv.name =~ /bootstrap_(\d+)_sample\.tsv/)[0][1].toInteger()
            tuple(bootstrap_id, tsv)
        }

    acc_ch = CREATE_BOOTSTRAP_SAMPLES.out.acc_txts
        .flatten()
        .map { acc ->
            def bootstrap_id = (acc.name =~ /bootstrap_(\d+)_accessions\.txt/)[0][1].toInteger()
            tuple(bootstrap_id, acc)
        }

    biolit_input_ch = acc_ch
        .map { bootstrap_id, acc -> tuple(bootstrap_id, acc, biolit_config) }

    RUN_BIOLIT(biolit_input_ch)

    parse_input_ch = RUN_BIOLIT.out.csv
        .join(sample_ch, by: 0)
        .map { bootstrap_id, csv, tsv -> tuple(bootstrap_id, csv, tsv, biolit_config) }

    PARSE_PREDICTIONS(parse_input_ch)

    score_input_ch = PARSE_PREDICTIONS.out
        .map { bootstrap_id, preds -> tuple(bootstrap_id, preds, ground_truth, biolit_config) }

    SCORE(score_input_ch)

    all_scores_ch = SCORE.out.scores
        .map { bootstrap_id, scores_tsv -> scores_tsv }
        .collect()

    all_errors_ch = SCORE.out.errors
        .map { bootstrap_id, errors_tsv -> errors_tsv }
        .collect()

    all_merged_ch = SCORE.out.merged
        .map { bootstrap_id, merged_tsv -> merged_tsv }
        .collect()

    AGGREGATE(all_scores_ch)
    AGGREGATE_ERRORS(all_errors_ch)
    AGGREGATE_MERGED(all_merged_ch)
    PLOT(AGGREGATE.out)
    PLOT_ERRORS(AGGREGATE_ERRORS.out)
}
