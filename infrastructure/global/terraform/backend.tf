# ./global-infra/terraform/backend.tf

terraform {
  # Temporarily using local state for testing
  backend "local" {}

  # Original S3 backend (commented out until permissions are fixed)
  # backend "s3" {
  #   bucket         = "dijoseh-aippointment-terraform-state"
  #   key            = "terraform.tfstate"
  #   region         = "us-west-2" # Use your preferred region
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}