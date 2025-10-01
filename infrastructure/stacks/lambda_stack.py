"""
Sake Sensei - Lambda Stack

This stack defines Lambda layers and functions for the Sake Sensei application.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from aws_cdk import Duration, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from constructs import Construct

if TYPE_CHECKING:
    from .database_stack import DatabaseStack
    from .storage_stack import StorageStack


class LambdaStack(Stack):
    """Stack for Lambda layers and functions."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        database_stack: "DatabaseStack | None" = None,
        storage_stack: "StorageStack | None" = None,
        **kwargs,
    ) -> None:
        """Initialize the Lambda Stack.

        Args:
            scope: CDK scope
            construct_id: Stack identifier
            database_stack: Database stack for table access
            storage_stack: Storage stack for S3 bucket access
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        # Get the path to the Lambda layer code
        layer_path = Path(__file__).parent.parent.parent / "backend" / "lambdas" / "layer"

        # Create Lambda Layer for shared utilities
        self.common_layer = lambda_.LayerVersion(
            self,
            "CommonLayer",
            layer_version_name="SakeSensei-Common",
            code=lambda_.Code.from_asset(str(layer_path)),
            compatible_runtimes=[
                lambda_.Runtime.PYTHON_3_12,
                lambda_.Runtime.PYTHON_3_13,
            ],
            description="Shared utilities for Sake Sensei Lambda functions (logger, response, error_handler)",
        )

        # Export layer ARN for use in other stacks
        self.layer_arn = self.common_layer.layer_version_arn

        # Recommendation Lambda Function
        if database_stack:
            recommendation_path = (
                Path(__file__).parent.parent.parent / "backend" / "lambdas" / "recommendation"
            )

            self.recommendation_function = lambda_.Function(
                self,
                "RecommendationFunction",
                function_name="SakeSensei-Recommendation",
                runtime=lambda_.Runtime.PYTHON_3_13,
                handler="handler.handler",
                code=lambda_.Code.from_asset(str(recommendation_path)),
                layers=[self.common_layer],
                timeout=Duration.seconds(30),
                memory_size=512,
                environment={
                    "SAKE_TABLE": database_stack.sake_master_table.table_name,
                    "BREWERY_TABLE": database_stack.brewery_master_table.table_name,
                    "TASTING_TABLE": database_stack.tasting_records_table.table_name,
                    "LOG_LEVEL": "INFO",
                },
                description="Generate personalized sake recommendations",
                tracing=lambda_.Tracing.ACTIVE,
            )

            # Grant read access to DynamoDB tables
            database_stack.sake_master_table.grant_read_data(self.recommendation_function)
            database_stack.brewery_master_table.grant_read_data(self.recommendation_function)
            database_stack.tasting_records_table.grant_read_data(self.recommendation_function)

            # Preference Lambda Function
            preference_path = (
                Path(__file__).parent.parent.parent / "backend" / "lambdas" / "preference"
            )

            self.preference_function = lambda_.Function(
                self,
                "PreferenceFunction",
                function_name="SakeSensei-Preference",
                runtime=lambda_.Runtime.PYTHON_3_13,
                handler="handler.handler",
                code=lambda_.Code.from_asset(str(preference_path)),
                layers=[self.common_layer],
                timeout=Duration.seconds(10),
                memory_size=256,
                environment={
                    "USERS_TABLE": database_stack.users_table.table_name,
                    "LOG_LEVEL": "INFO",
                },
                description="Manage user preference settings",
                tracing=lambda_.Tracing.ACTIVE,
            )

            # Grant read/write access to Users table
            database_stack.users_table.grant_read_write_data(self.preference_function)

            # Tasting Lambda Function
            tasting_path = Path(__file__).parent.parent.parent / "backend" / "lambdas" / "tasting"

            self.tasting_function = lambda_.Function(
                self,
                "TastingFunction",
                function_name="SakeSensei-Tasting",
                runtime=lambda_.Runtime.PYTHON_3_13,
                handler="handler.handler",
                code=lambda_.Code.from_asset(str(tasting_path)),
                layers=[self.common_layer],
                timeout=Duration.seconds(15),
                memory_size=256,
                environment={
                    "TASTING_TABLE": database_stack.tasting_records_table.table_name,
                    "LOG_LEVEL": "INFO",
                },
                description="Manage tasting records (CRUD)",
                tracing=lambda_.Tracing.ACTIVE,
            )

            # Grant read/write access to Tasting Records table
            database_stack.tasting_records_table.grant_read_write_data(self.tasting_function)

            # Brewery Lambda Function
            brewery_path = Path(__file__).parent.parent.parent / "backend" / "lambdas" / "brewery"

            self.brewery_function = lambda_.Function(
                self,
                "BreweryFunction",
                function_name="SakeSensei-Brewery",
                runtime=lambda_.Runtime.PYTHON_3_13,
                handler="handler.handler",
                code=lambda_.Code.from_asset(str(brewery_path)),
                layers=[self.common_layer],
                timeout=Duration.seconds(10),
                memory_size=256,
                environment={
                    "BREWERY_TABLE": database_stack.brewery_master_table.table_name,
                    "SAKE_TABLE": database_stack.sake_master_table.table_name,
                    "LOG_LEVEL": "INFO",
                },
                description="Brewery information and sake listings (read-only)",
                tracing=lambda_.Tracing.ACTIVE,
            )

            # Grant read access to Brewery and Sake tables
            database_stack.brewery_master_table.grant_read_data(self.brewery_function)
            database_stack.sake_master_table.grant_read_data(self.brewery_function)

        # Image Recognition Lambda Function (requires Bedrock access)
        if storage_stack:
            image_recognition_path = (
                Path(__file__).parent.parent.parent / "backend" / "lambdas" / "image_recognition"
            )

            self.image_recognition_function = lambda_.Function(
                self,
                "ImageRecognitionFunction",
                function_name="SakeSensei-ImageRecognition",
                runtime=lambda_.Runtime.PYTHON_3_13,
                handler="handler.handler",
                code=lambda_.Code.from_asset(str(image_recognition_path)),
                layers=[self.common_layer],
                timeout=Duration.seconds(60),  # Longer timeout for Bedrock API
                memory_size=1024,  # More memory for image processing
                environment={
                    "IMAGES_BUCKET": storage_stack.images_bucket.bucket_name,
                    "LOG_LEVEL": "INFO",
                },
                description="Sake label image recognition using Bedrock Claude 4.5 Sonnet",
                tracing=lambda_.Tracing.ACTIVE,
            )

            # Grant read access to S3 images bucket
            storage_stack.images_bucket.grant_read(self.image_recognition_function)

            # Grant access to Bedrock for Claude 4.5 Sonnet
            self.image_recognition_function.add_to_role_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["bedrock:InvokeModel"],
                    resources=[
                        "arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-4-5-v2:0",
                        # Allow access to Claude 4.5 Sonnet in any region
                        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-sonnet-4-5-v2:0",
                        "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-sonnet-4-5-v2:0",
                    ],
                )
            )
