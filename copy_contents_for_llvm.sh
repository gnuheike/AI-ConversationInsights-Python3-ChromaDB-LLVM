#!/bin/bash

find . -not -path "*/.venv/*" \( -name "*.py" -o -name "*.md" -o -name "*.txt" \) -exec sh -c 'echo "[$1]"; cat "$1"' _ {} \; | pbcopy
