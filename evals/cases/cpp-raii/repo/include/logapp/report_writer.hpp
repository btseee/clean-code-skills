#pragma once

#include <cstdio>
#include <string>

FILE *open_report(const std::string &path);
void write_summary(FILE *report, int processed, int failed);
