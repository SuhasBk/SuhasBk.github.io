variable "access_key_id" {
    description = "The access key ID for the AWS provider."
    type = string
    sensitive = true
}

variable "access_key_secret" {
    description = "The access key secret for the AWS provider."
    type = string
    sensitive = true
}

variable "aws_region" {
  type        = string
  description = "Target AWS region"
  default     = "us-east-1"
}

variable bucket_name {
  type        = string
  description = "The name of the S3 bucket to create"
  default     = "sk-portfolio-bucket"
}