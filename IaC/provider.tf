terraform {
    required_providers {
      aws = {
        source = "hashicorp/aws"
        version = "~> 5.0"
      }
      random = {
        source = "hashicorp/random"
        version = "~> 3.0"
      }
    }
}

provider "aws" {
  region = var.aws_region
  access_key = var.access_key_id
  secret_key = var.access_key_secret
}