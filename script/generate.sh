#!/usr/bin/env bash
set -euo pipefail

# Resolve repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
GENERATOR="${ROOT_DIR}/python/statesurf.py"
PLANTUML_DIR="${ROOT_DIR}/plantuml"
OUTPUT_DIR="${ROOT_DIR}/cpp/generated"

mkdir -p "${OUTPUT_DIR}"
shopt -s nullglob
for puml in "${PLANTUML_DIR}"/*.puml; do
  name="$(basename "${puml}" .puml)"
  python3 "${GENERATOR}" generate -i "${puml}" -o "${OUTPUT_DIR}/${name}.hpp"
done
