cmake_minimum_required(VERSION 3.20)
project(listdemo C)

set(CMAKE_C_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)

add_library(list src/list.c)
target_include_directories(list PUBLIC src)

add_executable(list_tests tests/test_list.c)
target_link_libraries(list_tests PRIVATE list)
