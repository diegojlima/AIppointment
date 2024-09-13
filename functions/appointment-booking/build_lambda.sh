#!/bin/bash

set -e

# Variables
SRC_DIR="src"
ZIP_FILE="lambda_function.zip"

# Remove previous builds
rm -f $ZIP_FILE

# Navigate to source directory
cd $SRC_DIR

# Zip the contents into the deployment package
zip -r ../$ZIP_FILE .

# Return to the root directory
cd ..
