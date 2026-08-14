variable "aws_region" {
  default = "us-east-1"
}

variable "ami_id" {
  description = "Ubuntu AMI"
}

variable "key_name" {
  description = "AWS Key Pair Name"
}

variable "instance_type" {
  default = "t3.small"
}
