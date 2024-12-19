#find ./backend/app -type f -name "*.py" | xargs grep -h "def \s*" | sort
find . -name "*.py" -type f -exec grep -H "^[[:space:]]*def" {} \; | sort
