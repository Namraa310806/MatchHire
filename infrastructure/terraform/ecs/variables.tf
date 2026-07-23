# Variables for ECS Fargate Infrastructure

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "production"
}

# Backend configuration
variable "backend_cpu" {
  description = "CPU units for backend task (1024 = 1 vCPU)"
  type        = number
  default     = 1024
}

variable "backend_memory" {
  description = "Memory for backend task in MB"
  type        = number
  default     = 2048
}

variable "backend_desired_count" {
  description = "Desired number of backend tasks"
  type        = number
  default     = 2
}

variable "backend_min_capacity" {
  description = "Minimum number of backend tasks for auto-scaling"
  type        = number
  default     = 1
}

variable "backend_max_capacity" {
  description = "Maximum number of backend tasks for auto-scaling"
  type        = number
  default     = 10
}

# Frontend configuration
variable "frontend_cpu" {
  description = "CPU units for frontend task (256 = 0.25 vCPU)"
  type        = number
  default     = 256
}

variable "frontend_memory" {
  description = "Memory for frontend task in MB"
  type        = number
  default     = 512
}

variable "frontend_desired_count" {
  description = "Desired number of frontend tasks"
  type        = number
  default     = 2
}

variable "frontend_min_capacity" {
  description = "Minimum number of frontend tasks for auto-scaling"
  type        = number
  default     = 1
}

variable "frontend_max_capacity" {
  description = "Maximum number of frontend tasks for auto-scaling"
  type        = number
  default     = 10
}

# Celery configuration
variable "celery_cpu" {
  description = "CPU units for celery task"
  type        = number
  default     = 512
}

variable "celery_memory" {
  description = "Memory for celery task in MB"
  type        = number
  default     = 1024
}

variable "celery_desired_count" {
  description = "Desired number of celery worker tasks"
  type        = number
  default     = 2
}

# Network configuration
variable "private_subnet_ids" {
  description = "List of private subnet IDs"
  type        = list(string)
}

variable "backend_security_group_id" {
  description = "Security group ID for backend service"
  type        = string
}

variable "frontend_security_group_id" {
  description = "Security group ID for frontend service"
  type        = string
}

# Load balancer configuration
variable "backend_target_group_arn" {
  description = "Target group ARN for backend service"
  type        = string
}

variable "frontend_target_group_arn" {
  description = "Target group ARN for frontend service"
  type        = string
}

# Notification configuration
variable "sns_topic_arn" {
  description = "SNS topic ARN for alarm notifications"
  type        = string
  default     = ""
}
