#include "logapp/report_writer.hpp"

FILE *open_report(const std::string &path) {
    return std::fopen(path.c_str(), "w");
}

void write_summary(FILE *report, int processed, int failed) {
    std::fprintf(report, "processed=%d failed=%d\n", processed, failed);
}
