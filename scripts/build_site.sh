#!/usr/bin/env bash
# Build the public site into _site/: the page, plus Idea X-ray and Markdown as wheels Pyodide loads in the browser.
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf _site && cp -r site _site && mkdir -p _site/py
pip wheel . --no-deps -w _site/py -q
pip download "markdown==3.7" --no-deps --only-binary=:all: -d _site/py -q
(cd _site/py && python -c "import json, glob; print(json.dumps(sorted(glob.glob('*.whl'))))" > manifest.json)
echo "Built _site/ with $(cat _site/py/manifest.json)"
