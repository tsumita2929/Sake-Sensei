#!/usr/bin/env python3
"""
Sake Sensei - AWS CDK Application Entry Point

This file defines the CDK application and instantiates all infrastructure stacks.
"""

import os

import aws_cdk as cdk

# Import stacks
from stacks.auth_stack import AuthStack
from stacks.database_stack import DatabaseStack
from stacks.lambda_stack import LambdaStack
from stacks.storage_stack import StorageStack

# from stacks.security_stack import SecurityStack
# from stacks.monitoring_stack import MonitoringStack

app = cdk.App()

# Environment configuration
env_name = os.getenv("APP_ENV", "dev")
aws_account = os.getenv("AWS_ACCOUNT_ID", os.getenv("CDK_DEFAULT_ACCOUNT"))
aws_region = os.getenv("AWS_REGION", os.getenv("CDK_DEFAULT_REGION", "us-west-2"))

# CDK Environment
env = cdk.Environment(account=aws_account, region=aws_region)

# Tags applied to all resources
tags = {
    "Project": "SakeSensei",
    "Environment": env_name,
    "ManagedBy": "CDK",
}

# Stack name prefix
stack_prefix = f"SakeSensei-{env_name.capitalize()}"

# Instantiate Storage Stack (S3 buckets)
storage_stack = StorageStack(
    app,
    f"{stack_prefix}-Storage",
    env=env,
    description="S3 buckets for Sake Sensei",
)

# Instantiate Database Stack (DynamoDB tables)
database_stack = DatabaseStack(
    app,
    f"{stack_prefix}-Database",
    env=env,
    description="DynamoDB tables for Sake Sensei",
)

# Instantiate Auth Stack (Cognito User Pool)
auth_stack = AuthStack(
    app,
    f"{stack_prefix}-Auth",
    env=env,
    description="Cognito authentication for Sake Sensei",
)

# Instantiate Lambda Stack (Lambda layers and functions)
lambda_stack = LambdaStack(
    app,
    f"{stack_prefix}-Lambda",
    database_stack=database_stack,
    storage_stack=storage_stack,
    env=env,
    description="Lambda layers and functions for Sake Sensei",
)

# Apply tags to all stacks
for key, value in tags.items():
    cdk.Tags.of(app).add(key, value)

# Synthesize the CloudFormation templates
app.synth()
