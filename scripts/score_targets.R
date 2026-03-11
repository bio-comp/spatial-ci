#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(arrow)
  library(jsonlite)
  library(singscore)
})

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 6) {
  stop(
    paste(
      "Usage: Rscript scripts/score_targets.R",
      "<expression_input.csv> <signature_input.json>",
      "<scoring_request.json> <detected_membership.parquet>",
      "<score_output.parquet> <runtime_metadata.json>"
    )
  )
}

expression_input <- args[[1]]
signature_input <- args[[2]]
scoring_request_input <- args[[3]]
detected_membership_input <- args[[4]]
score_output <- args[[5]]
runtime_metadata_output <- args[[6]]

validate_input_file <- function(path, label) {
  if (!file.exists(path)) {
    stop(paste(label, "does not exist:", path))
  }
}

validate_input_file(expression_input, "expression_input.csv")
validate_input_file(signature_input, "signature_input.json")
validate_input_file(scoring_request_input, "scoring_request.json")
validate_input_file(detected_membership_input, "detected_membership.parquet")

expr <- read.csv(expression_input, row.names = 1, check.names = FALSE)
expr_mat <- data.matrix(expr)
rank_data <- rankGenes(expr_mat, tiesMethod = "min")
signatures <- fromJSON(signature_input, simplifyVector = FALSE)
scoring_request <- fromJSON(scoring_request_input, simplifyVector = FALSE)

normalize_gene_ids <- function(gene_ids) {
  unique(as.character(unlist(gene_ids, use.names = FALSE)))
}

extract_up_genes <- function(signature_definition) {
  if (is.list(signature_definition) && !is.null(signature_definition$up_genes)) {
    return(normalize_gene_ids(signature_definition$up_genes))
  }

  return(normalize_gene_ids(signature_definition))
}

score_one_program <- function(rank_data, program_name, signature_definition) {
  up_genes <- extract_up_genes(signature_definition)
  present <- intersect(up_genes, rownames(rank_data))
  matched_size <- length(present)

  if (matched_size == 0) {
    return(data.frame(
      observation_id = colnames(rank_data),
      program_name = program_name,
      raw_rank_evidence = NA_real_
    ))
  }

  scores <- simpleScore(
    rank_data,
    upSet = present,
    centerScore = FALSE
  )

  data.frame(
    observation_id = rownames(scores),
    program_name = program_name,
    raw_rank_evidence = as.numeric(scores$TotalScore)
  )
}

rows <- lapply(
  names(signatures),
  function(program_name) {
    score_one_program(rank_data, program_name, signatures[[program_name]])
  }
)

output <- do.call(rbind, rows)

write_parquet(output, score_output)
writeLines(
  toJSON(
    list(
      r_version = paste(R.version$major, R.version$minor, sep = "."),
      singscore_version = as.character(packageVersion("singscore"))
    ),
    auto_unbox = TRUE
  ),
  runtime_metadata_output
)
