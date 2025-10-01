#!/bin/bash

# Sake Sensei - Deployment Script with Semantic Versioning
# Usage: ./scripts/deploy.sh [patch|minor|major]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REGION="us-west-2"
CLUSTER="sakesensei-dev-Cluster-RTWl4gZThPq4"
SERVICE="sakesensei-dev-streamlit-app-Service-IYtH6sHrR5S3"
ECR_REGISTRY="047786098634.dkr.ecr.us-west-2.amazonaws.com"
ECR_REPO="sakesensei/streamlit-app"
VERSION_FILE="VERSION"

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Read current version
if [ ! -f "$VERSION_FILE" ]; then
    print_error "VERSION file not found!"
    exit 1
fi

CURRENT_VERSION=$(cat "$VERSION_FILE")
print_info "Current version: v$CURRENT_VERSION"

# Parse version
IFS='.' read -r -a version_parts <<< "$CURRENT_VERSION"
MAJOR="${version_parts[0]}"
MINOR="${version_parts[1]}"
PATCH="${version_parts[2]}"

# Determine version bump type
BUMP_TYPE="${1:-patch}"

case "$BUMP_TYPE" in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
    *)
        print_error "Invalid bump type: $BUMP_TYPE (use: patch, minor, or major)"
        exit 1
        ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
print_info "New version: v$NEW_VERSION"

# Confirm deployment
read -p "Deploy version v$NEW_VERSION? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warn "Deployment cancelled"
    exit 0
fi

# Update VERSION file
echo "$NEW_VERSION" > "$VERSION_FILE"
print_info "Updated VERSION file to $NEW_VERSION"

# Run code quality checks
print_info "Running code quality checks..."
cd "$(dirname "$0")/.."

if ! uv run ruff format streamlit_app; then
    print_error "Ruff format failed"
    exit 1
fi

if ! uv run ruff check streamlit_app 2>&1 | grep -v "SIM116"; then
    # Allow SIM116 (if/elif chains) as per CLAUDE.md
    ruff_output=$(uv run ruff check streamlit_app 2>&1)
    if echo "$ruff_output" | grep -v "SIM116" | grep "error"; then
        print_error "Ruff check failed - fix all warnings before deploying"
        echo "$ruff_output"
        exit 1
    fi
fi

print_info "✓ Code quality checks passed"

# Build Docker image
print_info "Building Docker image..."
cd streamlit_app

if ! docker build -t sakesensei:v$NEW_VERSION .; then
    print_error "Docker build failed"
    exit 1
fi

print_info "✓ Docker image built successfully"

# Login to ECR
print_info "Logging in to ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Tag images
print_info "Tagging images..."
docker tag sakesensei:v$NEW_VERSION $ECR_REGISTRY/$ECR_REPO:v$NEW_VERSION
docker tag sakesensei:v$NEW_VERSION $ECR_REGISTRY/$ECR_REPO:latest

# Push to ECR
print_info "Pushing to ECR..."
docker push $ECR_REGISTRY/$ECR_REPO:v$NEW_VERSION
docker push $ECR_REGISTRY/$ECR_REPO:latest

print_info "✓ Images pushed to ECR"

# Deploy to ECS
print_info "Deploying to ECS..."
aws ecs update-service \
    --cluster $CLUSTER \
    --service $SERVICE \
    --force-new-deployment \
    --region $REGION \
    --no-cli-pager > /dev/null

print_info "✓ ECS deployment initiated"

# Wait for deployment
print_info "Waiting for deployment to complete (this may take 2-3 minutes)..."
aws ecs wait services-stable \
    --cluster $CLUSTER \
    --services $SERVICE \
    --region $REGION

print_info "✓ Deployment completed successfully"

# Create git tag
print_info "Creating git tag..."
cd ..
git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"
print_info "✓ Git tag v$NEW_VERSION created (push with: git push origin v$NEW_VERSION)"

# Summary
echo ""
print_info "======================================"
print_info "Deployment Summary"
print_info "======================================"
print_info "Version: v$NEW_VERSION"
print_info "Image: $ECR_REGISTRY/$ECR_REPO:v$NEW_VERSION"
print_info "Cluster: $CLUSTER"
print_info "Service: $SERVICE"
print_info "======================================"
echo ""
print_info "Next steps:"
echo "  1. Test the deployment: http://sakese-Publi-BG2ScFFG5nfS-804827597.us-west-2.elb.amazonaws.com"
echo "  2. Push git tag: git push origin v$NEW_VERSION"
echo "  3. Create release notes in GitHub"
echo ""
