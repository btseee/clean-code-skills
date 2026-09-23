test_that("load_scores reads a csv into a data frame", {
  path <- withr::local_tempfile(fileext = ".csv")
  writeLines(c("score,region", "10, north"), path)

  result <- load_scores(path)

  expect_s3_class(result, "data.frame")
  expect_equal(result$score, 10)
})
