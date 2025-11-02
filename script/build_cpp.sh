#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build"

declare -a cmake_args
cmake_args=(-S "${ROOT_DIR}" -B "${BUILD_DIR}")
if [[ ! -f "${BUILD_DIR}/CMakeCache.txt" ]]; then
  cmake_args+=("-G" "Ninja")
fi

cmake "${cmake_args[@]}"
cmake --build "${BUILD_DIR}"
