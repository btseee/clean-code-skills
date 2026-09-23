#include "logapp/report_writer.hpp"

#include <cstdio>
#include <string>

int run_report(const std::string &path, int processed, int failed) {
    FILE *report = open_report(path);
    if (!report) {
        return 1;
    }
    write_summary(report, processed, failed);
    fclose(report);
    return 0;
}

int main() {
    return run_report("report.txt", 10, 2);
}
