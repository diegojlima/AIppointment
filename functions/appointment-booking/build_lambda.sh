#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status.

# Variables
SRC_DIR="src"
BUILD_DIR="build"
ZIP_FILE="lambda_function.zip"

# Remove previous builds
rm -rf $BUILD_DIR/ $ZIP_FILE

# Create build directory
mkdir -p $BUILD_DIR

# Copy source code
cp -r $SRC_DIR/* $BUILD_DIR/

# Install dependencies into build directory
pip install -r requirements.txt --target $BUILD_DIR/

# Navigate to build directory
cd $BUILD_DIR

# Zip the contents into the deployment package
zip -r ../$ZIP_FILE .

# Return to the root directory
cd ..

# Clean up build directory
rm -rf $BUILD_DIR/
