#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"${SCRIPT_DIR}/generate.sh"

"${SCRIPT_DIR}/build_cpp.sh"
"${SCRIPT_DIR}/build_static_analysis.sh"
"${SCRIPT_DIR}/run_cpp_test.sh"
"${SCRIPT_DIR}/run-clang-tidy.sh"
"${SCRIPT_DIR}/run-cppcheck.sh"

"${SCRIPT_DIR}/build_rust.sh"
"${SCRIPT_DIR}/run_rust_test.sh"

"${SCRIPT_DIR}/run_python_test.sh"
