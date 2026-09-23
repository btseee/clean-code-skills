library(dplyr)
source("R/load_data.R")

site_a <- load_scores("data/site_a.csv")
site_a <- site_a[!is.na(site_a$score), ]
site_a$region <- trimws(site_a$region)
site_a <- site_a[site_a$score >= 0, ]

site_b <- load_scores("data/site_b.csv")
site_b <- site_b[!is.na(site_b$score), ]
site_b$region <- trimws(site_b$region)
site_b <- site_b[site_b$score >= 0, ]

combined <- rbind(site_a, site_b)
summary(combined$score)
