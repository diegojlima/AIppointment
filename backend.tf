# Root directory backend.tf

terraform {
  # Using S3 backend with DynamoDB locking
  backend "s3" {
    bucket         = "delima-aippointment-terraform-state"
    key            = "root/terraform.tfstate"
    region         = "us-west-2" # Use your preferred region
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
