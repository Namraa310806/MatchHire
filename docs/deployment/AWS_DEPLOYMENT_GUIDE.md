# AWS Deployment Guide for MatchHire

This guide provides comprehensive instructions for deploying MatchHire to AWS using various deployment strategies.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Options](#deployment-options)
3. [Option 1: ECS Fargate (Recommended)](#option-1-ecs-fargate-recommended)
4. [Option 2: EC2 with Docker Compose](#option-2-ec2-with-docker-compose)
5. [Option 3: Elastic Beanstalk](#option-3-elastic-beanstalk)
6. [Infrastructure Components](#infrastructure-components)
7. [Security Considerations](#security-considerations)
8. [Monitoring and Observability](#monitoring-and-observability)
9. [Cost Optimization](#cost-optimization)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### AWS Account Setup

- AWS account with appropriate permissions
- AWS CLI installed and configured
- Docker installed locally
- Domain name configured (optional but recommended)

### Required AWS Services

- **ECS** (Elastic Container Service) or **EC2**
- **Elastic Load Balancer** (ALB)
- **RDS** (PostgreSQL)
- **ElastiCache** (Redis)
- **S3** (Static assets and media storage)
- **CloudFront** (CDN)
- **Secrets Manager** (Secret storage)
- **CloudWatch** (Monitoring and logging)
- **IAM** (Access management)

### Local Prerequisites

```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Install Terraform (if using IaC)
# Download from: https://www.terraform.io/downloads.html

# Install Docker
# Download from: https://www.docker.com/products/docker-desktop
```

## Deployment Options

### Option 1: ECS Fargate (Recommended)

**Pros:**
- Serverless container orchestration
- Auto-scaling capabilities
- No EC2 management overhead
- Pay for actual resource usage

**Cons:**
- Higher cost per compute hour
- Limited control over underlying infrastructure

### Option 2: EC2 with Docker Compose

**Pros:**
- Full control over instances
- Lower cost for sustained workloads
- Familiar Docker Compose workflow

**Cons:**
- Manual scaling required
- EC2 management overhead
- Less resilient than Fargate

### Option 3: Elastic Beanstalk

**Pros:**
- Simplified deployment process
- Managed platform
- Built-in load balancing

**Cons:**
- Less customization
- Platform constraints
- Vendor lock-in

## Option 1: ECS Fargate (Recommended)

### Step 1: Create VPC and Networking

```bash
cd infrastructure/terraform/networking
terraform init
terraform plan
terraform apply
```

### Step 2: Create ECR Repositories

```bash
# Create backend repository
aws ecr create-repository --repository-name matchhire-backend

# Create frontend repository
aws ecr create-repository --repository-name matchhire-frontend

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

### Step 3: Build and Push Docker Images

```bash
# Build backend image
docker build -f docker/Dockerfile.backend.prod -t matchhire-backend .
docker tag matchhire-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/matchhire-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/matchhire-backend:latest

# Build frontend image
docker build -f docker/Dockerfile.frontend -t matchhire-frontend .
docker tag matchhire-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/matchhire-frontend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/matchhire-frontend:latest
```

### Step 4: Create ECS Cluster

```bash
cd infrastructure/terraform/ecs
terraform init
terraform plan
terraform apply
```

### Step 5: Configure Application Load Balancer

```bash
cd infrastructure/terraform/alb
terraform init
terraform plan
terraform apply
```

### Step 6: Deploy Services

```bash
# Deploy backend service
aws ecs update-service --cluster matchhire-cluster --service backend-service --force-new-deployment

# Deploy frontend service
aws ecs update-service --cluster matchhire-cluster --service frontend-service --force-new-deployment
```

### Step 7: Configure DNS

```bash
# Create Route53 hosted zone (if using custom domain)
aws route53 create-hosted-zone --name matchhire.com --caller-reference $(date +%s)

# Add A record pointing to ALB
aws route53 change-resource-record-sets --hosted-zone-id <zone-id> --change-batch file://route53-record.json
```

## Option 2: EC2 with Docker Compose

### Step 1: Launch EC2 Instance

```bash
# Create EC2 instance using Terraform
cd infrastructure/terraform/ec2
terraform init
terraform plan
terraform apply
```

### Step 2: Configure Security Groups

Ensure the following ports are open:
- 22 (SSH)
- 80 (HTTP)
- 443 (HTTPS)
- 8000 (Backend API - internal)

### Step 3: SSH into Instance and Setup

```bash
# SSH into instance
ssh -i ~/.ssh/matchhire-key.pem ec2-user@<public-ip>

# Install Docker
sudo yum update -y
sudo amazon-linux-extras install docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository
git clone https://github.com/your-org/matchhire.git
cd matchhire
```

### Step 4: Configure Environment

```bash
# Copy production environment template
cp .env.production.example .env.production

# Edit with your AWS RDS and ElastiCache endpoints
nano .env.production
```

### Step 5: Deploy with Docker Compose

```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Step 6: Configure Nginx Reverse Proxy

```bash
# Install Nginx
sudo amazon-linux-extras install nginx1.12

# Configure Nginx
sudo cp nginx/nginx-ec2.conf /etc/nginx/nginx.conf
sudo service nginx start
```

## Option 3: Elastic Beanstalk

### Step 1: Create Application

```bash
eb init matchhire
eb create matchhire-production
```

### Step 2: Configure Environment

```bash
eb setenv DB_HOST=<rds-endpoint>
eb setenv REDIS_HOST=<elasticache-endpoint>
eb setenv SECRET_KEY=<your-secret-key>
```

### Step 3: Deploy

```bash
eb deploy
```

## Infrastructure Components

### RDS PostgreSQL

```bash
# Create RDS instance
aws rds create-db-instance \
    --db-instance-identifier matchhire-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username matchhire \
    --master-user-password <secure-password> \
    --allocated-storage 20 \
    --vpc-security-group-ids <sg-id> \
    --db-subnet-group-name matchhire-subnet-group
```

### ElastiCache Redis

```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
    --cache-cluster-id matchhire-redis \
    --engine redis \
    --cache-node-type cache.t3.micro \
    --num-cache-nodes 1 \
    --security-group-ids <sg-id> \
    --cache-subnet-group-name matchhire-cache-subnet-group
```

### S3 Buckets

```bash
# Create static assets bucket
aws s3 mb s3://matchhire-static-assets --region us-east-1

# Create media files bucket
aws s3 mb s3://matchhire-media --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning --bucket matchhire-static-assets --versioning-configuration Status=Enabled

# Configure lifecycle policy
aws s3api put-bucket-lifecycle-configuration --bucket matchhire-static-assets --lifecycle-configuration file://lifecycle.json
```

### CloudFront Distribution

```bash
# Create CloudFront distribution
aws cloudfront create-distribution \
    --distribution-config file://cloudfront-config.json
```

### Secrets Manager

```bash
# Store database credentials
aws secretsmanager create-secret \
    --name matchhire/db-credentials \
    --secret-string '{"username":"matchhire","password":"<secure-password>"}'

# Store JWT secret
aws secretsmanager create-secret \
    --name matchhire/jwt-secret \
    --secret-string '{"secret":"<your-jwt-secret>"}'

# Store API keys
aws secretsmanager create-secret \
    --name matchhire/api-keys \
    --secret-string '{"openai":"<api-key>","sendgrid":"<api-key>"}'
```

## Security Considerations

### IAM Roles

Create least-privilege IAM roles for:

- ECS task execution role
- ECS task role
- EC2 instance profile
- Lambda functions (if used)

### Security Groups

Configure security groups to allow:

- ALB to communicate with ECS tasks
- ECS tasks to communicate with RDS and ElastiCache
- SSH access from specific IP ranges only

### SSL/TLS Certificates

```bash
# Request ACM certificate
aws acm request-certificate \
    --domain-name matchhire.com \
    --validation-method DNS \
    --subject-alternative-names www.matchhire.com

# Validate certificate (DNS validation)
# Add CNAME records to Route53
```

### Encryption

- Enable encryption at rest for RDS
- Enable encryption for S3 buckets
- Use TLS for all communications
- Encrypt EBS volumes

## Monitoring and Observability

### CloudWatch Logs

```bash
# Create log groups
aws logs create-log-group --log-group-name /ecs/matchhire-backend
aws logs create-log-group --log-group-name /ecs/matchhire-frontend
aws logs create-log-group --log-group-name /ecs/matchhire-celery
```

### CloudWatch Alarms

```bash
# Create CPU utilization alarm
aws cloudwatch put-metric-alarm \
    --alarm-name matchhire-high-cpu \
    --alarm-description "Alert when CPU > 80%" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold
```

### X-Ray Tracing

Enable AWS X-Ray for distributed tracing:

```python
# In Django settings
INSTALLED_APPS = [
    ...
    'aws_xray_sdk',
]

XRAY_RECORDER = {
    'AWS_XRAY_TRACING_NAME': 'matchhire',
    'AWS_XRAY_DAEMON_ADDRESS': '127.0.0.1:2000',
}
```

## Cost Optimization

### Right-Sizing

- Use t3 instances for development
- Use m5 or c5 instances for production based on workload
- Enable auto-scaling to scale down during low traffic

### Reserved Instances

- Purchase reserved instances for predictable workloads
- Use savings plans for consistent compute usage

### S3 Lifecycle Policies

```json
{
  "Rules": [
    {
      "Id": "MoveToIA",
      "Status": "Enabled",
      "Prefix": "",
      "Transition": {
        "Days": 30,
        "StorageClass": "STANDARD_IA"
      },
      "NoncurrentVersionTransition": {
        "NoncurrentDays": 30,
        "StorageClass": "STANDARD_IA"
      }
    }
  ]
}
```

## Troubleshooting

### Common Issues

#### ECS Tasks Not Starting

```bash
# Check task logs
aws logs tail /ecs/matchhire-backend --follow

# Check task definition
aws ecs describe-task-definition --task-definition matchhire-backend

# Check container insights
aws ecs describe-tasks --cluster matchhire-cluster --tasks <task-id>
```

#### Database Connection Issues

```bash
# Check RDS instance status
aws rds describe-db-instances --db-instance-identifier matchhire-db

# Check security group rules
aws ec2 describe-security-groups --group-ids <sg-id>

# Test connectivity from ECS task
docker exec -it <container-id> psql -h <rds-endpoint> -U matchhire -d matchhire
```

#### High Memory Usage

```bash
# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/ECS \
    --metric-name MemoryUtilization \
    --dimensions Name=ServiceName,Value=matchhire-backend \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Average
```

### Rollback Procedure

```bash
# Rollback to previous task definition
aws ecs update-service \
    --cluster matchhire-cluster \
    --service backend-service \
    --task-definition <previous-task-definition-arn>

# Force new deployment
aws ecs update-service \
    --cluster matchhire-cluster \
    --service backend-service \
    --force-new-deployment
```

## Additional Resources

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [AWS RDS Documentation](https://docs.aws.amazon.com/rds/)
- [AWS CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
