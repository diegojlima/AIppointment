#!/bin/bash
set -e

# Define source directory and lambda handlers
SRC_DIR="src"
BEDROCK_AGENT_DIR="$SRC_DIR/bedrock_agent"

# Create temp directory for packaging
mkdir -p lambda_packages

# Install dependencies in a temporary directory
TEMP_DIR="lambda_packages/temp"
mkdir -p $TEMP_DIR
python -m pip install -r requirements.txt -t $TEMP_DIR --upgrade --index-url https://pypi.org/simple/

# Function to create action group lambda packages
create_lambda_package() {
    action_group=$1
    handler=$2
    output_zip=$3
    
    echo "Creating Lambda package for $action_group..."
    
    # Create a temporary directory for this action group
    package_dir="lambda_packages/$action_group"
    mkdir -p $package_dir
    
    # Copy common files
    cp -r $SRC_DIR/*.py $package_dir/ 2>/dev/null || true
    cp -r $SRC_DIR/config $package_dir/ 2>/dev/null || true
    cp -r $SRC_DIR/calendar_services $package_dir/ 2>/dev/null || true
    
    # Copy bedrock agent directory
    mkdir -p $package_dir/bedrock_agent
    cp $BEDROCK_AGENT_DIR/*.py $package_dir/bedrock_agent/ 2>/dev/null || true
    
    # Copy action group specific file
    cp $BEDROCK_AGENT_DIR/$handler.py $package_dir/bedrock_agent/
    
    # Copy schema directory
    mkdir -p $package_dir/bedrock_agent/schema
    cp -r $BEDROCK_AGENT_DIR/schema/* $package_dir/bedrock_agent/schema/ 2>/dev/null || true
    
    # Copy dependencies
    cp -r $TEMP_DIR/* $package_dir/
    
    # Remove unnecessary files to reduce size
    find $package_dir -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find $package_dir -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
    find $package_dir -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    
    # Create zip package
    cd $package_dir
    zip -r ../../$output_zip . -q
    cd ../../
    
    echo "Created $output_zip"
}

# Create individual lambda packages for each action group
# Create the appointment_booking lambda differently since main.py is in src/ not in bedrock_agent/
echo "Creating Lambda package for appointment_booking..."
package_dir="lambda_packages/appointment_booking"
mkdir -p $package_dir

# Copy all files from src
cp -r $SRC_DIR/*.py $package_dir/ 2>/dev/null || true
cp -r $SRC_DIR/config $package_dir/ 2>/dev/null || true
cp -r $SRC_DIR/calendar_services $package_dir/ 2>/dev/null || true

# Copy bedrock agent directory
mkdir -p $package_dir/bedrock_agent
cp $BEDROCK_AGENT_DIR/*.py $package_dir/bedrock_agent/ 2>/dev/null || true

# Copy schema directory
mkdir -p $package_dir/bedrock_agent/schema
cp -r $BEDROCK_AGENT_DIR/schema/* $package_dir/bedrock_agent/schema/ 2>/dev/null || true

# Copy dependencies
cp -r $TEMP_DIR/* $package_dir/

# Remove unnecessary files to reduce size
find $package_dir -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find $package_dir -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find $package_dir -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Create zip package
cd $package_dir
zip -r ../../appointment_booking_lambda.zip . -q
cd ../../

echo "Created appointment_booking_lambda.zip"
create_lambda_package "appointment_creator" "appointment_creator" "appointment_creator_lambda.zip"
create_lambda_package "appointment_manager" "appointment_manager" "appointment_manager_lambda.zip"
create_lambda_package "calendar_integrator" "calendar_integrator" "calendar_integrator_lambda.zip"

# Clean up temporary directories
rm -rf lambda_packages

echo "Lambda packages created successfully!"
