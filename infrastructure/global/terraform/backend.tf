# ./global-infra/terraform/backend.tf

terraform {
  backend "s3" {
    bucket         = "delima-appointment-state-tf"
    key            = "terraform.tfstate"
    region         = "us-west-2"  # Use your preferred region
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}