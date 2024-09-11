#!/bin/bash

# Function to prepend the file path as a comment in the first line
prepend_path() {
    local file="$1"
    local ext="${file##*.}"

    # If the file is Python (.py), add a '#' comment
    if [[ "$ext" == "txt" ]]; then
        sed -i '' "1s|^|# ${file}\n|" "$file"
    fi

    # If the file is Terraform (.tf), add a '#' comment
    if [[ "$ext" == "md" ]]; then
        sed -i '' "1s|^|# ${file}\n|" "$file"
    fi
}

export -f prepend_path

# Find all .py and .tf files, ignoring the specified directories
find . -type f \( -name "*.txt" -o -name "*.md" \) \
    ! -path "*/__pycache__/*" \
    ! -path "*/.pytest_cache/*" \
    ! -path "*/.terraform/*" \
    ! -path "*/.env" \
    ! -path "*/myenv/*" \
    ! -path "*/new_env/*" \
    ! -path "*/.venv/*" \
    -exec bash -c 'prepend_path "$0"' {} \;
