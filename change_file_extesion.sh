#!/bin/bash

# Find all .tf files, excluding specified directories, and rename them to .txt
find . -type f -name "*.txt.tf.tf" \
    ! -path "*/__pycache__/*" \
    ! -path "*/.pytest_cache/*" \
    ! -path "*/.terraform/*" \
    ! -path "*/.env" \
    ! -path "*/myenv/*" \
    ! -path "*/new_env/*" \
    ! -path "*/.venv/*" \
    -exec bash -c 'mv "$0" "${0%.txt.tf.tf}.tf"' {} \;
