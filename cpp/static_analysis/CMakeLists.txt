cmake_minimum_required(VERSION 3.20)
project(StateSurfStaticAnalysis LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_library(statesurf_static_analysis STATIC EXCLUDE_FROM_ALL
  hsm_header_check.cpp
)

target_compile_features(statesurf_static_analysis PRIVATE cxx_std_11)

target_include_directories(statesurf_static_analysis PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}/../generated
)
