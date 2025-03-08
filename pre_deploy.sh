#!/bin/bash
set -e

echo "Running pre-deployment tasks..."

# Build Lambda zip files for Bedrock Agent action groups
echo "Building Lambda packages for Bedrock Agent action groups..."
cd functions/appointment-booking
./build_action_group_lambdas.sh
cd ../..

echo "Pre-deployment completed successfully."
