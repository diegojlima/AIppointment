#!/bin/bash

set -e  # Exit on error

# Variables
SRC_DIR="src"
BUILD_DIR="build"
ZIP_FILE="lambda_function.zip"

# Remove previous builds
rm -rf $BUILD_DIR/ $ZIP_FILE

# Create build directory
mkdir -p $BUILD_DIR

# Copy source code only
cp -r $SRC_DIR/* $BUILD_DIR/

# Remove any __pycache__ directories
find $BUILD_DIR/ -name "__pycache__" -type d -exec rm -r {} +

# Zip the contents into the deployment package
cd $BUILD_DIR
zip -r9 ../$ZIP_FILE .
cd ..

# Clean up build directory
rm -rf $BUILD_DIR/
