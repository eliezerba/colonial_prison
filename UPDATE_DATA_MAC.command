#!/bin/bash
set -e
cd "$(dirname "$0")"
PY=python3
[ -d .venv ] || "$PY" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r pipeline/requirements.txt
python pipeline/enrich_v7.py
node --check site/assets/app.js
python -m unittest discover -s tests -v
open site/index.html
