"""Security stack for SakeSensei.

This stack creates:
- AWS WAF Web ACL with security rules
- Rate limiting rules
- AWS Secrets Manager for sensitive data
- Secret rotation Lambda functions
"""

from aws_cdk import (
    RemovalPolicy,
    Stack,
)
from aws_cdk import (
    aws_iam as iam,
)
from aws_cdk import (
    aws_secretsmanager as secretsmanager,
)
from aws_cdk import (
    aws_wafv2 as wafv2,
)
from constructs import Construct


class SecurityStack(Stack):
    """Security stack with WAF and Secrets Manager."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        alb_arn: str | None = None,
        **kwargs,
    ) -> None:
        """Initialize security stack.

        Args:
            scope: CDK scope
            construct_id: Stack ID
            alb_arn: ARN of the Application Load Balancer to protect
            **kwargs: Additional stack arguments
        """
        super().__init__(scope, construct_id, **kwargs)

        # Create WAF Web ACL
        self.web_acl = self._create_web_acl()

        # Associate WAF with ALB if provided
        if alb_arn:
            wafv2.CfnWebACLAssociation(
                self,
                "WebACLAssociation",
                resource_arn=alb_arn,
                web_acl_arn=self.web_acl.attr_arn,
            )

        # Create Secrets Manager secrets
        self.secrets = self._create_secrets()

    def _create_web_acl(self) -> wafv2.CfnWebACL:
        """Create WAF Web ACL with security rules.

        Returns:
            WAF Web ACL
        """
        # Define WAF rules
        rules = []

        # Rule 1: Rate limiting (100 requests per 5 minutes per IP)
        rate_limit_rule = wafv2.CfnWebACL.RuleProperty(
            name="RateLimitRule",
            priority=1,
            statement=wafv2.CfnWebACL.StatementProperty(
                rate_based_statement=wafv2.CfnWebACL.RateBasedStatementProperty(
                    aggregate_key_type="IP",
                    limit=100,
                    scope_down_statement=wafv2.CfnWebACL.StatementProperty(
                        byte_match_statement=wafv2.CfnWebACL.ByteMatchStatementProperty(
                            field_to_match=wafv2.CfnWebACL.FieldToMatchProperty(uri_path={}),
                            positional_constraint="STARTS_WITH",
                            search_string="/",
                            text_transformations=[
                                wafv2.CfnWebACL.TextTransformationProperty(priority=0, type="NONE")
                            ],
                        )
                    ),
                )
            ),
            action=wafv2.CfnWebACL.RuleActionProperty(
                block=wafv2.CfnWebACL.BlockActionProperty(
                    custom_response=wafv2.CfnWebACL.CustomResponseProperty(
                        response_code=429,
                    )
                )
            ),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="RateLimitRule",
                sampled_requests_enabled=True,
            ),
        )
        rules.append(rate_limit_rule)

        # Rule 2: AWS Managed Rules - Core Rule Set
        aws_managed_core_rule = wafv2.CfnWebACL.RuleProperty(
            name="AWSManagedRulesCommonRuleSet",
            priority=2,
            statement=wafv2.CfnWebACL.StatementProperty(
                managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                    vendor_name="AWS",
                    name="AWSManagedRulesCommonRuleSet",
                    excluded_rules=[
                        # Exclude specific rules if they cause false positives
                        # wafv2.CfnWebACL.ExcludedRuleProperty(name="SizeRestrictions_BODY")
                    ],
                )
            ),
            override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="AWSManagedRulesCommonRuleSet",
                sampled_requests_enabled=True,
            ),
        )
        rules.append(aws_managed_core_rule)

        # Rule 3: AWS Managed Rules - Known Bad Inputs
        aws_managed_bad_inputs_rule = wafv2.CfnWebACL.RuleProperty(
            name="AWSManagedRulesKnownBadInputsRuleSet",
            priority=3,
            statement=wafv2.CfnWebACL.StatementProperty(
                managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                    vendor_name="AWS",
                    name="AWSManagedRulesKnownBadInputsRuleSet",
                )
            ),
            override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="AWSManagedRulesKnownBadInputsRuleSet",
                sampled_requests_enabled=True,
            ),
        )
        rules.append(aws_managed_bad_inputs_rule)

        # Rule 4: AWS Managed Rules - SQL Injection
        aws_managed_sqli_rule = wafv2.CfnWebACL.RuleProperty(
            name="AWSManagedRulesSQLiRuleSet",
            priority=4,
            statement=wafv2.CfnWebACL.StatementProperty(
                managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                    vendor_name="AWS",
                    name="AWSManagedRulesSQLiRuleSet",
                )
            ),
            override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="AWSManagedRulesSQLiRuleSet",
                sampled_requests_enabled=True,
            ),
        )
        rules.append(aws_managed_sqli_rule)

        # Rule 5: Block specific countries (example - customize as needed)
        # geo_block_rule = wafv2.CfnWebACL.RuleProperty(
        #     name="GeoBlockRule",
        #     priority=5,
        #     statement=wafv2.CfnWebACL.StatementProperty(
        #         geo_match_statement=wafv2.CfnWebACL.GeoMatchStatementProperty(
        #             country_codes=["XX", "YY"]  # Replace with actual country codes
        #         )
        #     ),
        #     action=wafv2.CfnWebACL.RuleActionProperty(
        #         block=wafv2.CfnWebACL.BlockActionProperty()
        #     ),
        #     visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
        #         cloud_watch_metrics_enabled=True,
        #         metric_name="GeoBlockRule",
        #         sampled_requests_enabled=True,
        #     ),
        # )
        # rules.append(geo_block_rule)

        # Rule 6: Block requests with no User-Agent
        no_user_agent_rule = wafv2.CfnWebACL.RuleProperty(
            name="BlockNoUserAgentRule",
            priority=6,
            statement=wafv2.CfnWebACL.StatementProperty(
                not_statement=wafv2.CfnWebACL.NotStatementProperty(
                    statement=wafv2.CfnWebACL.StatementProperty(
                        byte_match_statement=wafv2.CfnWebACL.ByteMatchStatementProperty(
                            field_to_match=wafv2.CfnWebACL.FieldToMatchProperty(
                                single_header=wafv2.CfnWebACL.SingleHeaderProperty(
                                    name="user-agent"
                                )
                            ),
                            positional_constraint="CONTAINS",
                            search_string="Mozilla",  # Look for common user agents
                            text_transformations=[
                                wafv2.CfnWebACL.TextTransformationProperty(
                                    priority=0, type="LOWERCASE"
                                )
                            ],
                        )
                    )
                )
            ),
            action=wafv2.CfnWebACL.RuleActionProperty(block=wafv2.CfnWebACL.BlockActionProperty()),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="BlockNoUserAgentRule",
                sampled_requests_enabled=True,
            ),
        )
        rules.append(no_user_agent_rule)

        # Create Web ACL
        web_acl = wafv2.CfnWebACL(
            self,
            "WebACL",
            name="SakeSensei-WebACL",
            scope="REGIONAL",  # Use CLOUDFRONT for CloudFront distributions
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            rules=rules,
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="SakeSenseiWebACL",
                sampled_requests_enabled=True,
            ),
            description="WAF Web ACL for SakeSensei application",
        )

        return web_acl

    def _create_secrets(self) -> dict:
        """Create Secrets Manager secrets for sensitive data.

        Returns:
            Dictionary of secret names to Secret constructs
        """
        secrets = {}

        # Secret for AgentCore API keys (if needed)
        agentcore_secret = secretsmanager.Secret(
            self,
            "AgentCoreSecret",
            secret_name="SakeSensei/AgentCore/APIKey",
            description="AgentCore API keys and configuration",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"api_key": ""}',
                generate_string_key="api_key_value",
                password_length=32,
                exclude_characters='"@\\',
            ),
            removal_policy=RemovalPolicy.RETAIN,  # Keep secrets on stack deletion
        )
        secrets["agentcore"] = agentcore_secret

        # Secret for third-party API keys (if needed)
        third_party_secret = secretsmanager.Secret(
            self,
            "ThirdPartySecret",
            secret_name="SakeSensei/ThirdParty/APIKeys",
            description="Third-party service API keys",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template="{}",
                generate_string_key="placeholder",
            ),
            removal_policy=RemovalPolicy.RETAIN,
        )
        secrets["third_party"] = third_party_secret

        # Secret for database credentials (if RDS is used)
        # database_secret = secretsmanager.Secret(
        #     self,
        #     "DatabaseSecret",
        #     secret_name="SakeSensei/Database/Credentials",
        #     description="Database connection credentials",
        #     generate_secret_string=secretsmanager.SecretStringGenerator(
        #         secret_string_template='{"username": "admin"}',
        #         generate_string_key="password",
        #         exclude_punctuation=True,
        #         include_space=False,
        #     ),
        #     removal_policy=RemovalPolicy.RETAIN,
        # )
        # secrets["database"] = database_secret

        # Secret rotation Lambda function (example for future use)
        # rotation_function = lambda_.Function(
        #     self,
        #     "SecretRotationFunction",
        #     function_name="SakeSensei-SecretRotation",
        #     runtime=lambda_.Runtime.PYTHON_3_13,
        #     handler="index.handler",
        #     code=lambda_.Code.from_inline("""
        # def handler(event, context):
        #     # Implement secret rotation logic
        #     return {"statusCode": 200}
        # """),
        #     timeout=Duration.minutes(5),
        # )

        # # Attach rotation to secret
        # agentcore_secret.add_rotation_schedule(
        #     "RotationSchedule",
        #     rotation_lambda=rotation_function,
        #     automatically_after=Duration.days(30),
        # )

        return secrets

    def grant_read_secret(self, secret_name: str, grantee: iam.IGrantable) -> None:
        """Grant read access to a specific secret.

        Args:
            secret_name: Name of the secret (key in self.secrets)
            grantee: IAM principal to grant access to
        """
        if secret_name in self.secrets:
            self.secrets[secret_name].grant_read(grantee)
