#!/bin/bash

echo "Building AIppointment Lambda package..."

# Create build directory
mkdir -p build

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -t build/ --no-deps

# Copy source files
echo "Copying source files..."
cp -r src/* build/

# Define destination directory relative to the current script
DEST_DIR="../../infrastructure/global/terraform/functions/appointment-booking"
mkdir -p "$DEST_DIR"

# Remove any existing package in the destination
rm -f "$DEST_DIR/lambda_function.zip"

# Create zip package in the build directory and move it to the destination
echo "Creating Lambda package..."
cd build
zip -r ../lambda_function.zip .
cd ..
mv lambda_function.zip "$DEST_DIR/"

# Clean up
echo "Cleaning up..."
rm -rf build

echo "Lambda package created at: $DEST_DIR/lambda_function.zip"
echo ""
echo "To deploy, run:"
echo "aws lambda create-function \\"
echo "  --function-name AIppointment \\"
echo "  --runtime python3.12 \\"
echo "  --handler main.lambda_handler \\"
echo "  --role YOUR_LAMBDA_ROLE_ARN \\"
echo "  --zip-file fileb://$DEST_DIR/lambda_function.zip \\"
echo "  --environment \"Variables={...}\""
