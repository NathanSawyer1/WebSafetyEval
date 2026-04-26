#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${VENV_DIR:-${ROOT_DIR}/.venv}"
PYTHON_BIN="${PYTHON:-python3}"
RECREATE="${RECREATE_VENV:-0}"

cd "${ROOT_DIR}"

if [[ -d "${VENV_DIR}" && "${RECREATE}" != "1" ]]; then
  echo "WARNING: virtual environment already exists at ${VENV_DIR}"
  echo ""
  echo "This setup script installs and upgrades packages inside that environment."
  echo "It will not touch system Python, but it will modify the existing venv."
  echo ""
  echo "If you want a fresh environment instead, either:"
  echo "  RECREATE_VENV=1 bash setup.sh"
  echo "or"
  echo "  VENV_DIR=${ROOT_DIR}/.venv-fresh bash setup.sh"
  echo ""
  read -r -p "Continue using the existing virtual environment? [y/N] " reply
  if [[ ! "${reply}" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
  fi
elif [[ -d "${VENV_DIR}" && "${RECREATE}" == "1" ]]; then
  echo "==> Recreating virtual environment at ${VENV_DIR}"
  rm -rf "${VENV_DIR}"
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "==> Creating virtual environment at ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "==> Upgrading pip"
python -m pip install --upgrade pip

echo "==> Installing project and dev dependencies"
python -m pip install -e '.[dev]'

echo "==> Running preflight"
python scripts/preflight.py

echo
echo "Setup complete."
echo ""
echo "Virtual environment: ${VENV_DIR}"
echo ""
echo "Next steps:"
echo " source ${VENV_DIR}/bin/activate"
echo " WEB_SAFETY_DEV=1 python3 run_demo.py --backend mock"
echo ""
echo "Or run a real OpenClaw eval once openclaw is installed:"
echo " WEB_SAFETY_AGENT=openclaw python3 run_all.py"
