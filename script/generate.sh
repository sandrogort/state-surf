#!/usr/bin/env bash
set -euo pipefail

# Resolve repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
GENERATOR="${ROOT_DIR}/python/statesurf.py"
PLANTUML_DIR="${ROOT_DIR}/plantuml"
OUTPUT_DIR="${ROOT_DIR}/cpp/generated"
RUST_OUTPUT_DIR="${ROOT_DIR}/rust/generated"
PYTHON_OUTPUT_DIR="${ROOT_DIR}/python/generated"
SIM_OUTPUT_DIR="${ROOT_DIR}/simulation/generated"

mkdir -p "${OUTPUT_DIR}"
mkdir -p "${RUST_OUTPUT_DIR}"
mkdir -p "${PYTHON_OUTPUT_DIR}"
shopt -s nullglob
for puml in "${PLANTUML_DIR}"/*.puml; do
  name="$(basename "${puml}" .puml)"
  python3 "${GENERATOR}" generate -i "${puml}" -o "${OUTPUT_DIR}/${name}.hpp" -l cpp
  python3 "${GENERATOR}" generate -i "${puml}" -o "${RUST_OUTPUT_DIR}/${name}.rs" -l rust
  python3 "${GENERATOR}" generate -i "${puml}" -o "${PYTHON_OUTPUT_DIR}/${name}.py" -l python
done

python3 "${GENERATOR}" simulate -i "${PLANTUML_DIR}/fsm.puml" --sim-dir "${SIM_OUTPUT_DIR}"
