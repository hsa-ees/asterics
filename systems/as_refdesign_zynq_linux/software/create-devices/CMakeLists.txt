cmake_minimum_required(VERSION 3.0)
project(create-devices C)

add_executable(create-devices create-devices.c as_hardware.c)

set(SRC_DIR "../../../../")
add_library(asterics SHARED
  ${SRC_DIR}support/software/asp/as_support.c
  ${SRC_DIR}modules/as_reader_writer/software/driver/as_reader_writer.c
  ${SRC_DIR}modules/as_invert/software/driver/as_invert.c
)

# Forces the use of the POSIX config
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -include ./as_config.h")
include_directories(${Boost_INCLUDE_DIRS} . ${SRC_DIR}support/software/asp ${SRC_DIR}support/software/as-linux/src/kernel_module/asterics-driver ${SRC_DIR}modules/as_reader_writer/software/driver ${SRC_DIR}modules/as_invert/software/driver) 
target_link_libraries(create-devices ${Boost_UNIT_TEST_FRAMEWORK_LIBRARY} asterics)
