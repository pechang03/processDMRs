#!/bin/zsh

find backend/app frontend/src backend/tests -type f -name "*.py" \
    -not -path "*/\.__pycache__*" \
    -not -path "*/__pycache__*" \
    -exec grep -H "^[[:space:]]*def" {} \; \
    | sort
