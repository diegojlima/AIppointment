#!/bin/bash

# AIppointment Lambda Build Script
# This script packages the Lambda function for deployment

echo "Building AIppointment Lambda package..."

# Create build directory
mkdir -p build

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -t build/ --no-deps

# Copy source files
echo "Copying source files..."
cp -r src/* build/

# Remove any existing package
rm -f lambda_function.zip

# Create zip package
echo "Creating Lambda package..."
cd build
zip -r ../lambda_function.zip .
cd ..

# Clean up
echo "Cleaning up..."
rm -rf build

echo "Lambda package created: lambda_function.zip"
echo ""
echo "To deploy, run:"
echo "aws lambda create-function \\"
echo "  --function-name AIppointment \\"
echo "  --runtime python3.12 \\"
echo "  --handler main.lambda_handler \\"
echo "  --role YOUR_LAMBDA_ROLE_ARN \\"
echo "  --zip-file fileb://lambda_function.zip \\"
echo "  --environment \"Variables={...}\""
