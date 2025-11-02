#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

BUILD_DIR="${BUILD_DIR:-${ROOT_DIR}/build_static_analysis}"
COMP_DB="${COMP_DB:-${BUILD_DIR}/compile_commands.json}"
CLANG_TIDY="${CLANG_TIDY:-clang-tidy}"
DEFAULT_SOURCE="cpp/static_analysis/hsm_header_check.cpp"
HEADER_FILTER=".*hsm\\.hpp$"
DEFAULT_CLANG_TIDY_ARGS=(--header-filter="${HEADER_FILTER}")

usage() {
  cat <<'EOF'
Usage: run-clang-tidy.sh [options] [files...] [-- <clang-tidy args>]

Options:
  --build-dir <dir>         Build directory that holds compile_commands.json (default: $ROOT_DIR/build_static_analysis)
  --compile-commands <path> Explicit path to compile_commands.json
  --clang-tidy <path>       clang-tidy executable to use
  -h, --help                Show this help message
  --                        Everything after '--' is passed to clang-tidy

If no files are provided the script runs clang-tidy on
cpp/static_analysis/hsm_header_check.cpp, limiting diagnostics to hsm.hpp.
EOF
}

FILES=()
EXTRA_ARGS=()

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
    --clang-tidy)
      if [[ $# -lt 2 ]]; then
        echo "error: --clang-tidy expects a path" >&2
        exit 1
      fi
      CLANG_TIDY="$2"
      shift 2
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
      echo "error: unrecognised option '$1' (pass clang-tidy flags after '--')" >&2
      exit 1
      ;;
    *)
      FILES+=("$1")
      shift
      ;;
  esac
done

if ! command -v "$CLANG_TIDY" >/dev/null 2>&1; then
  echo "error: clang-tidy executable '$CLANG_TIDY' not found" >&2
  echo "       set CLANG_TIDY or use --clang-tidy to override" >&2
  exit 1
fi

if [[ ! -f "$COMP_DB" ]]; then
  echo "error: compile commands database '$COMP_DB' not found" >&2
  echo "       run 'cmake -S cpp/static_analysis -B ${BUILD_DIR}' first or provide --compile-commands" >&2
  exit 1
fi

if [[ ${#FILES[@]} -eq 0 ]]; then
  FILES=("$DEFAULT_SOURCE")
fi

CMD_ARGS=()
header_filter_present=false
for arg in "${EXTRA_ARGS[@]}"; do
  if [[ "$arg" == --header-filter=* ]]; then
    header_filter_present=true
    break
  fi
done
if ! $header_filter_present; then
  CMD_ARGS+=("${DEFAULT_CLANG_TIDY_ARGS[@]}")
fi
CMD_ARGS+=("${EXTRA_ARGS[@]}")

status=0

for source in "${FILES[@]}"; do
  echo "==> clang-tidy: ${source}"
  if ! "$CLANG_TIDY" -p "$BUILD_DIR" "${CMD_ARGS[@]}" "$source"; then
    status=1
  fi
done

exit $status
