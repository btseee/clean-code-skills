cmake_minimum_required(VERSION 3.20)
project(reportapp CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(reportlib src/report_writer.cpp)
target_include_directories(reportlib PUBLIC include)

add_executable(reportapp src/main.cpp)
target_link_libraries(reportapp PRIVATE reportlib)
