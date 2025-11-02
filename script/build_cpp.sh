#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build"
STATIC_ANALYSIS_DIR="${ROOT_DIR}/build_static_analysis"

CLANG_TIDY_PATH="$(command -v clang-tidy || true)"
declare -a cmake_args
cmake_args=(-S "${ROOT_DIR}" -B "${BUILD_DIR}")
if [[ ! -f "${BUILD_DIR}/CMakeCache.txt" ]]; then
  cmake_args+=("-G" "Ninja")
fi
if [[ -n "${CLANG_TIDY_PATH}" ]]; then
  cmake_args+=("-DSTATE_SURF_CLANG_TIDY_EXE=${CLANG_TIDY_PATH}")
fi

cmake "${cmake_args[@]}"
cmake --build "${BUILD_DIR}"

declare -a static_cmake_args
static_cmake_args=(-S "${ROOT_DIR}/cpp/static_analysis" -B "${STATIC_ANALYSIS_DIR}")
if [[ ! -f "${STATIC_ANALYSIS_DIR}/CMakeCache.txt" ]]; then
  static_cmake_args+=("-G" "Ninja")
fi

cmake "${static_cmake_args[@]}"
cmake --build "${STATIC_ANALYSIS_DIR}"
