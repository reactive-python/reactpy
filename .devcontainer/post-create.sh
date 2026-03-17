#!/usr/bin/env bash

set -euo pipefail

# Workaround for hatch/virtualenv incompatibility
python3 -m pip install --upgrade "virtualenv==20.25.1"

# Install core ReactPy dependencies
pip install fastjsonschema requests lxml anyio typing-extensions

# Install ASGI dependencies for server functionality
pip install orjson asgiref asgi-tools servestatic uvicorn fastapi

# Optional: Install additional servers
pip install flask sanic tornado

export BUN_INSTALL="${BUN_INSTALL:-$HOME/.bun}"
export PATH="$BUN_INSTALL/bin:$PATH"

if [[ -f /etc/apt/sources.list.d/yarn.list ]]; then
  echo "Refreshing Yarn APT keyring..."
  curl -fsSL https://dl.yarnpkg.com/debian/pubkey.gpg \
    | gpg --dearmor \
    | sudo tee /usr/share/keyrings/yarn-archive-keyring.gpg >/dev/null
fi

if ! command -v hatch >/dev/null 2>&1; then
  echo "Installing Hatch..."
  python3 -m pip install --user hatch
fi

if ! command -v bun >/dev/null 2>&1; then
  echo "Installing Bun..."
  curl -fsSL https://bun.sh/install | bash
fi

echo "Building JavaScript packages..."
hatch run javascript:build --dev

echo "Building Python package..."
hatch build --clean

python3 -m pip install .[all]

echo "Running ReactPy smoke test..."
hatch run python - <<'PY'
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
