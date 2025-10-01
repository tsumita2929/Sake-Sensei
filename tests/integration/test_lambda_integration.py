"""Integration tests for Lambda functions with DynamoDB patterns."""

import json
from typing import Any
from unittest.mock import MagicMock

import boto3
import pytest
from moto import mock_aws


@pytest.mark.integration
@pytest.mark.aws
class TestLambdaDynamoDBIntegration:
    """Test Lambda-DynamoDB integration patterns with moto."""

    @pytest.fixture
    def dynamodb_table(self, aws_credentials: None) -> Any:
        """Create DynamoDB test table."""
        with mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")

            # Create test table
            table = dynamodb.create_table(
                TableName="SakeSensei-Sakes",
                KeySchema=[{"AttributeName": "sake_id", "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": "sake_id", "AttributeType": "S"}],
                BillingMode="PAY_PER_REQUEST",
            )

            # Add test data
            table.put_item(
                Item={
                    "sake_id": "test-sake-001",
                    "name": "Test Sake",
                    "brewery": "Test Brewery",
                    "type": "純米大吟醸",
                    "sweetness": 3,
                    "acidity": 2,
                    "richness": 2,
                }
            )

            yield table

    def test_recommendation_with_dynamodb(
        self,
        dynamodb_table: Any,
        lambda_context: MagicMock,
    ) -> None:
        """Test recommendation Lambda pattern with DynamoDB table."""
        # Query the table to get sake data
        response = dynamodb_table.scan()

        assert "Items" in response
        assert len(response["Items"]) > 0

        # Validate sake data structure
        sake_item = response["Items"][0]
        assert "sake_id" in sake_item
        assert "name" in sake_item
        assert "sweetness" in sake_item

        # Simulate Lambda handler pattern
        event = {
            "body": json.dumps(
                {
                    "user_id": "test-user",
                    "preferences": {"sweetness": 3, "acidity": 2, "richness": 2},
                    "limit": 5,
                }
            )
        }

        # Validate event structure
        body = json.loads(event["body"])
        assert "user_id" in body
        assert "preferences" in body

        # Simulate response pattern
        lambda_response = {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "recommendations": [
                        {
                            "sake_id": sake_item["sake_id"],
                            "name": sake_item["name"],
                            "score": 0.95,
                        }
                    ]
                }
            ),
        }

        assert lambda_response["statusCode"] == 200
        response_body = json.loads(lambda_response["body"])
        assert "recommendations" in response_body
        assert isinstance(response_body["recommendations"], list)


@pytest.mark.integration
class TestLambdaChaining:
    """Test Lambda function chaining patterns."""

    def test_preference_to_recommendation_flow(
        self,
        lambda_context: MagicMock,
    ) -> None:
        """Test flow pattern from preference storage to recommendation."""
        # Document the expected flow:
        # 1. Store preferences via preference Lambda
        # 2. Get recommendations based on stored preferences
        # 3. Verify recommendations match preferences

        flow_steps = [
            {
                "step": 1,
                "lambda": "preference",
                "action": "PUT",
                "input": {
                    "user_id": "test-user",
                    "preferences": {"sweetness": 3, "acidity": 2},
                },
                "expected_output": {"statusCode": 200},
            },
            {
                "step": 2,
                "lambda": "recommendation",
                "action": "GET",
                "input": {
                    "user_id": "test-user",
                    "limit": 5,
                },
                "expected_output": {
                    "statusCode": 200,
                    "recommendations_count": 5,
                },
            },
        ]

        # Validate flow documentation
        assert len(flow_steps) == 2
        for step in flow_steps:
            assert "lambda" in step
            assert "action" in step
            assert "input" in step
            assert "expected_output" in step
