#!/bin/bash
# Script to migrate local state to S3 backend

cd infrastructure/global/terraform

echo "Initializing Terraform with S3 backend..."
terraform init -migrate-state -force-copy

echo "Verifying state..."
terraform state list

echo "State migration complete! Your state file should now be stored in S3."
