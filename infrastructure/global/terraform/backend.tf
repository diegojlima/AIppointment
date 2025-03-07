# ./global-infra/terraform/backend.tf

terraform {
  backend "s3" {
    bucket         = "delima-aippointment-terraform-state"
    key            = "terraform.tfstate"
    region         = "us-west-2"  # Use your preferred region
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}