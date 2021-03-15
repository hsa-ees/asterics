cmake_minimum_required(VERSION 3.0)
project(unit_test C CXX)

find_package(Boost 1.67 COMPONENTS unit_test_framework)

add_executable(unit_test main.cpp unit_test.cpp)

set(SRC_DIR "../../../../")
add_library(asterics SHARED
  ${SRC_DIR}support/software/asp/as_support.c
  ${SRC_DIR}modules/as_reader_writer/software/driver/as_reader_writer.c
  ${SRC_DIR}modules/as_invert/software/driver/as_invert.c
)

include_directories(${Boost_INCLUDE_DIRS} . ${SRC_DIR}support/software/asp ${SRC_DIR}support/software/as-linux/src/kernel_module/asterics-driver ${SRC_DIR}modules/as_reader_writer/software/driver ${SRC_DIR}modules/as_invert/software/driver) 
target_link_libraries(unit_test ${Boost_UNIT_TEST_FRAMEWORK_LIBRARY} asterics)
