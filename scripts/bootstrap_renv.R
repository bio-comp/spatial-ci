#!/usr/bin/env Rscript

# bootstrap_renv.R
# Initializes and restores the R environment for target scoring using renv

if (!requireNamespace("renv", quietly = TRUE)) {
  install.packages("renv", repos = "https://cloud.r-project.org")
}

# If renv.lock exists, restore. Otherwise initialize.
if (file.exists("renv.lock")) {
  message("Restoring R environment from renv.lock...")
  renv::restore()
} else {
  message("Initializing R environment...")
  renv::init(bare = TRUE)
  
  # Install necessary Bioconductor dependencies
  if (!requireNamespace("BiocManager", quietly = TRUE)) {
    install.packages("BiocManager", repos = "https://cloud.r-project.org")
  }
  
  # singscore and dependencies
  BiocManager::install(c("singscore", "SummarizedExperiment", "arrow", "optparse"), update = FALSE)
  
  # Save the current state to renv.lock
  renv::snapshot(type = "all")
}

message("R environment bootstrap complete.")
