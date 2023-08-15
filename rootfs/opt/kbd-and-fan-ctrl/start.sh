#!/bin/bash
cd "$(dirname $(readlink -f "$0"))"

python3 main.py

cd - >/dev/null
exit 0
