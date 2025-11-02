#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
STATIC_ANALYSIS_DIR="${ROOT_DIR}/build_static_analysis"

declare -a cmake_args
cmake_args=(-S "${ROOT_DIR}/cpp/static_analysis" -B "${STATIC_ANALYSIS_DIR}")
if [[ ! -f "${STATIC_ANALYSIS_DIR}/CMakeCache.txt" ]]; then
  cmake_args+=("-G" "Ninja")
fi

cmake "${cmake_args[@]}"
cmake --build "${STATIC_ANALYSIS_DIR}"
