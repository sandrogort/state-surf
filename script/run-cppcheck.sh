#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

BUILD_DIR="${BUILD_DIR:-${ROOT_DIR}/build_static_analysis}"
COMP_DB="${COMP_DB:-${BUILD_DIR}/compile_commands.json}"
CPPCHECK="${CPPCHECK:-cppcheck}"
DEFAULT_TU_REL="cpp/static_analysis/hsm_header_check.cpp"
DEFAULT_TU="${ROOT_DIR}/${DEFAULT_TU_REL}"
DEFAULT_ARGS=(--enable=warning --inline-suppr --suppress=missingIncludeSystem --std=c++11 --quiet)
DEFAULT_FILE_FILTER="${DEFAULT_TU}"

usage() {
  cat <<'EOF'
Usage: run-cppcheck.sh [options] [files...] [-- <cppcheck args>]

Options:
  --build-dir <dir>         Build directory that holds compile_commands.json (default: $ROOT_DIR/build_static_analysis)
  --compile-commands <path> Explicit path to compile_commands.json
  --cppcheck <path>         cppcheck executable to use
  --no-project              Do not use compile_commands.json even if available
  -h, --help                Show this help message
  --                        Everything after '--' is passed to cppcheck

If no files are provided the script analyses the dedicated
cpp/static_analysis/hsm_header_check.cpp translation unit (which pulls in
cpp/generated/hsm.hpp). Pass files explicitly or --no-project to override.
EOF
}

FILES=()
EXTRA_ARGS=()
USE_PROJECT=true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --build-dir)
      if [[ $# -lt 2 ]]; then
        echo "error: --build-dir expects a directory" >&2
        exit 1
      fi
      BUILD_DIR="$2"
      shift 2
      ;;
    --compile-commands)
      if [[ $# -lt 2 ]]; then
        echo "error: --compile-commands expects a path" >&2
        exit 1
      fi
      COMP_DB="$2"
      shift 2
      ;;
    --cppcheck)
      if [[ $# -lt 2 ]]; then
        echo "error: --cppcheck expects a path" >&2
        exit 1
      fi
      CPPCHECK="$2"
      shift 2
      ;;
    --no-project)
      USE_PROJECT=false
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      EXTRA_ARGS=("$@")
      break
      ;;
    -*)
      echo "error: unrecognised option '$1' (pass cppcheck flags after '--')" >&2
      exit 1
      ;;
    *)
      FILES+=("$1")
      shift
      ;;
  esac
done

if ! command -v "$CPPCHECK" >/dev/null 2>&1; then
  echo "error: cppcheck executable '$CPPCHECK' not found" >&2
  echo "       set CPPCHECK or use --cppcheck to override" >&2
  exit 1
fi

if [[ ${#FILES[@]} -gt 0 ]]; then
  USE_PROJECT=false
fi

CMD=("$CPPCHECK")
CMD+=("${DEFAULT_ARGS[@]}")

if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then
  CMD+=("${EXTRA_ARGS[@]}")
fi

if "$USE_PROJECT"; then
  if [[ ! -f "$COMP_DB" ]]; then
    echo "error: compile commands database '$COMP_DB' not found" >&2
    echo "       run 'cmake -S cpp/static_analysis -B ${BUILD_DIR}' first or provide --compile-commands" >&2
    exit 1
  fi
  file_filter_present=false
  for arg in "${EXTRA_ARGS[@]}"; do
    if [[ "$arg" == --file-filter=* ]]; then
      file_filter_present=true
      break
    fi
  done
  CMD+=("--project=$COMP_DB")
  if ! $file_filter_present; then
    CMD+=("--file-filter=${DEFAULT_FILE_FILTER}")
  fi
else
  if [[ ${#FILES[@]} -eq 0 ]]; then
    FILES=("$DEFAULT_TU_REL")
  fi
  CMD+=("${FILES[@]}")
fi

echo "==> cppcheck: ${CMD[*]}"
"${CMD[@]}"
