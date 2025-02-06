#!/bin/bash
find backend/app frontend/src -type d -not -path "*/\.__pycache__*" -not -path "*/__pycache__*"
