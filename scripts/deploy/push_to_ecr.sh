#!/bin/bash
# Sake Sensei - Push Docker Image to ECR

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="sakesensei"
SERVICE_NAME="streamlit-app"
AWS_REGION=${AWS_REGION:-us-west-2}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}"
IMAGE_TAG=${1:-latest}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Sake Sensei - ECR Image Push${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not configured or credentials are invalid${NC}"
    exit 1
fi

echo -e "${YELLOW}AWS Account ID:${NC} $AWS_ACCOUNT_ID"
echo -e "${YELLOW}AWS Region:${NC} $AWS_REGION"
echo -e "${YELLOW}ECR Repository:${NC} $ECR_REPOSITORY"
echo -e "${YELLOW}Image Tag:${NC} $IMAGE_TAG"
echo ""

# Create ECR repository if it doesn't exist
echo -e "${GREEN}[1/5] Checking ECR repository...${NC}"
if ! aws ecr describe-repositories --repository-names ${APP_NAME} --region ${AWS_REGION} &> /dev/null; then
    echo "  Creating ECR repository: ${APP_NAME}"
    aws ecr create-repository \
        --repository-name ${APP_NAME} \
        --region ${AWS_REGION} \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256 \
        --tags Key=Application,Value=SakeSensei Key=ManagedBy,Value=Copilot
    echo -e "  ${GREEN}✓ ECR repository created${NC}"
else
    echo -e "  ${GREEN}✓ ECR repository exists${NC}"
fi

# Authenticate Docker to ECR
echo ""
echo -e "${GREEN}[2/5] Authenticating Docker to ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
echo -e "  ${GREEN}✓ Docker authenticated${NC}"

# Build Docker image
echo ""
echo -e "${GREEN}[3/5] Building Docker image...${NC}"
cd streamlit_app
docker build -t ${APP_NAME}:${IMAGE_TAG} .
echo -e "  ${GREEN}✓ Docker image built${NC}"
cd ..

# Tag image for ECR
echo ""
echo -e "${GREEN}[4/5] Tagging image for ECR...${NC}"
docker tag ${APP_NAME}:${IMAGE_TAG} ${ECR_REPOSITORY}:${IMAGE_TAG}
docker tag ${APP_NAME}:${IMAGE_TAG} ${ECR_REPOSITORY}:latest
echo -e "  ${GREEN}✓ Image tagged${NC}"

# Push image to ECR
echo ""
echo -e "${GREEN}[5/5] Pushing image to ECR...${NC}"
docker push ${ECR_REPOSITORY}:${IMAGE_TAG}
docker push ${ECR_REPOSITORY}:latest
echo -e "  ${GREEN}✓ Image pushed${NC}"

# Display image information
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Image successfully pushed to ECR!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}ECR Repository URI:${NC} ${ECR_REPOSITORY}"
echo -e "${YELLOW}Image Tags:${NC} ${IMAGE_TAG}, latest"
echo ""
echo -e "You can now deploy with:"
echo -e "  ${GREEN}copilot svc deploy --name ${SERVICE_NAME} --env dev --tag ${IMAGE_TAG}${NC}"
echo ""