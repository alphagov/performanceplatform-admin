#!/bin/bash -e

PORT=${1:-3104}
VENV_DIR=~/.virtualenvs/$(basename $(cd $(dirname $0) && pwd -P))-$PORT-$2

if [ -z "$VIRTUAL_ENV" ]; then
  if [ ! -f "${VENV_DIR}/bin/activate" ]; then
    mkdir -p "${VENV_DIR}"
    virtualenv --no-site-packages "$VENV_DIR"
  fi

  source "$VENV_DIR/bin/activate"
fi

echo "Installing dependencies"
pip install -r requirements.txt

export PYTHONUNBUFFERED=1

exec python start.py $PORT
