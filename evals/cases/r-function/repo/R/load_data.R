#' Load raw scores for one site
#'
#' @param path Path to a site's CSV export.
#' @return A data frame with at least `score` and `region` columns.
#' @export
load_scores <- function(path) {
  read.csv(path, stringsAsFactors = FALSE)
}
