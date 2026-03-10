if (!requireNamespace("renv", quietly = TRUE)) {
  install.packages("renv", repos = "https://cloud.r-project.org")
}

renv::init(bare = TRUE)

if (!requireNamespace("BiocManager", quietly = TRUE)) {
  install.packages("BiocManager", repos = "https://cloud.r-project.org")
}

BiocManager::install("singscore", ask = FALSE, update = FALSE)

renv::snapshot()
