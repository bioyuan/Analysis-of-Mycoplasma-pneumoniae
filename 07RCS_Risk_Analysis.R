library(rcssci)
library(dplyr)
library(readr)
library(optparse)

# Define command line arguments
option_list <- list(
  make_option(c("-f", "--file"), type = "character", default = "01prov_age_group_RCS.txt",
              help = "Input file name [default = %default]", metavar = "character"),
  make_option(c("-y", "--response"), type = "character", default = "Infected",
              help = "Response variable (y) [default = %default]", metavar = "character"),
  make_option(c("-x", "--predictor"), type = "character", default = "Age",
              help = "Predictor variable (x) [default = %default]", metavar = "character"),
  make_option(c("-g", "--groupby"), type = "character", default = NULL,
              help = "Column name to group data by (e.g., 'Sex') [default = Analyze whole dataset]", metavar = "character"),
  make_option(c("-c", "--covariates"), type = "character", default = NULL,
              help = "Covariates (comma separated, e.g., 'Region,Group')", metavar = "character")
)

# Parse command line arguments
opt_parser <- OptionParser(option_list = option_list)
opt <- parse_args(opt_parser)

# Convert covariates to a vector
covariates <- if (!is.null(opt$covariates)) strsplit(opt$covariates, ",")[[1]] else NULL

# Read input file
data <- read_csv(opt$file, show_col_types = FALSE)

# Convert data types and round Age values
data <- data %>%
  mutate(
    Age = round(as.numeric(Age), 1),
    Infected = as.numeric(Infected)
  )

# Function to perform logistic analysis and save results
perform_logistic_analysis <- function(data, y, x, covars, prob, dir_path) {
  if (!dir.exists(dir_path)) {
    dir.create(dir_path, recursive = TRUE)  # Create directory including parent directories if not exists
  }
  logistic_results <- rcssci_logistic(
    data = data,
    y = y,
    x = x,
    covars = covars,
    prob = prob,
    filepath = dir_path
  )
  print(logistic_results)
  write.table(logistic_results, file = file.path(dir_path, "logistic_results.txt"), sep = "\t", row.names = FALSE)
}

# Analyze data
if (is.null(opt$groupby)) {
  # No grouping, analyze the whole dataset
  perform_logistic_analysis(
    data = data,
    y = opt$response,
    x = opt$predictor,
    covars = covariates,
    prob = 0.1,
    dir_path = "AllData"
  )
} else {
  # Group data by the specified column and analyze each group
  groups <- unique(data[[opt$groupby]])
  for (group in groups) {
    group_data <- data %>% filter(!!sym(opt$groupby) == group)
    group_dir <- file.path(opt$groupby, as.character(group))
    perform_logistic_analysis(
      data = group_data,
      y = opt$response,
      x = opt$predictor,
      covars = covariates,
      prob = 0.1,
      dir_path = group_dir
    )
  }
}