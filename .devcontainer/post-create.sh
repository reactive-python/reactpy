#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SYSTEM_PYTHON="$(command -v python3)"
USER_BASE_BIN="$("$SYSTEM_PYTHON" -m site --user-base)/bin"
export PATH="$USER_BASE_BIN:$PATH"

# Workaround for hatch/virtualenv incompatibility
"$SYSTEM_PYTHON" -m pip install --upgrade "virtualenv==20.25.1"

export BUN_INSTALL="${BUN_INSTALL:-$HOME/.bun}"
export PATH="$BUN_INSTALL/bin:$PATH"
DEVCONTAINER_PYTHON_DIR="${HOME}/.local/share/reactpy-devcontainer/python"

if [[ -f /etc/apt/sources.list.d/yarn.list ]]; then
  echo "Refreshing Yarn APT keyring..."
  curl -fsSL https://dl.yarnpkg.com/debian/pubkey.gpg \
    | gpg --dearmor \
    | sudo tee /usr/share/keyrings/yarn-archive-keyring.gpg >/dev/null
fi

if ! command -v hatch >/dev/null 2>&1; then
  echo "Installing Hatch..."
  "$SYSTEM_PYTHON" -m pip install --user hatch
fi

HATCH_CMD=("$SYSTEM_PYTHON" -m hatch)

echo "Creating Hatch devcontainer environment..."
"${HATCH_CMD[@]}" env create devcontainer
DEVCONTAINER_ENV_DIR="$("${HATCH_CMD[@]}" env find devcontainer)"
mkdir -p "$(dirname "$DEVCONTAINER_PYTHON_DIR")"
ln -sfn "$DEVCONTAINER_ENV_DIR" "$DEVCONTAINER_PYTHON_DIR"
export PATH="$DEVCONTAINER_PYTHON_DIR/bin:$PATH"
export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

if ! command -v bun >/dev/null 2>&1; then
  echo "Installing Bun..."
  curl -fsSL https://bun.sh/install | bash
fi

echo "Building JavaScript packages..."
"${HATCH_CMD[@]}" run javascript:build --dev

echo "Building Python package..."
"${HATCH_CMD[@]}" build --clean

echo "Running ReactPy smoke test..."
"$DEVCONTAINER_PYTHON_DIR/bin/python" - <<'PY'
from reactpy import component, html


@component
def test_component():
    return html.div([
        html.h1("Test"),
        html.p("ReactPy is working"),
    ])


vdom = test_component()
print(type(vdom).__name__)
PY
