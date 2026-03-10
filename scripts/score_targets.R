#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(singscore)
  library(jsonlite)
})

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 3) {
  stop("Usage: Rscript scripts/score_targets.R <input_csv> <geneset_json> <output_csv>")
}

input_csv <- args[[1]]
geneset_json <- args[[2]]
output_csv <- args[[3]]

expr <- read.csv(input_csv, row.names = 1, check.names = FALSE)
genesets <- fromJSON(geneset_json)

score_one <- function(mat, genes) {
  present <- intersect(genes, rownames(mat))
  missing_fraction <- 1 - (length(present) / length(genes))

  if (missing_fraction > 0.10) {
    return(rep(NA_real_, ncol(mat)))
  }

  # singscore expects genes x samples
  scores <- simpleScore(mat[present, , drop = FALSE], upSet = present, centerScore = FALSE)
  return(scores$TotalScore)
}

out <- data.frame(sample_id = colnames(expr))

for (program_name in names(genesets)) {
  out[[program_name]] <- score_one(expr, genesets[[program_name]])
}

write.csv(out, output_csv, row.names = FALSE)
