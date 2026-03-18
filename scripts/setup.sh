#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
PYTHON_BIN="${PYTHON:-python}"

cd "${ROOT_DIR}"

"${PYTHON_BIN}" -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
pip install -r requirements.txt

echo "Setup complete. Activate with: source .venv/bin/activate"
