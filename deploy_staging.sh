#!/bin/bash
set -e

# Build lambda packages for action groups
echo "Building Lambda packages..."
cd functions/appointment-booking
chmod +x build_action_group_lambdas.sh
./build_action_group_lambdas.sh
cd ../..

# Deploy to staging environment
echo "Deploying to staging environment..."
cd infrastructure/global/terraform

# Initialize Terraform
terraform init

# Validate Terraform configurations
terraform validate

# Plan the deployment
terraform plan -var-file=staging.tfvars -out=tfplan_staging

# Apply the deployment (uncomment when ready to deploy)
# terraform apply tfplan_staging

echo "Staging deployment planned successfully!"
echo "To deploy, run: terraform apply tfplan_staging"
