terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend configuration (uncomment and configure for remote state)
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "langchain-langgraph-agent/terraform.tfstate"
  #   region = "ap-northeast-2"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "langchain-langgraph-agent"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

