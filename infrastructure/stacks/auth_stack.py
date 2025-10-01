"""
Sake Sensei - Cognito Authentication Stack

This stack defines Cognito User Pool and authentication resources.
"""

from typing import Any

from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk import aws_cognito as cognito
from constructs import Construct


class AuthStack(Stack):
    """Stack for Cognito authentication resources."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        """Initialize the Auth Stack.

        Args:
            scope: CDK scope
            construct_id: Stack identifier
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        # Cognito User Pool with email authentication
        self.user_pool = cognito.UserPool(
            self,
            "UserPool",
            user_pool_name=f"SakeSensei-Users-{Stack.of(self).account}",
            # Email as username (no separate username field)
            sign_in_aliases=cognito.SignInAliases(email=True, username=False),
            # Email verification required
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            # Standard attributes
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=False),
                given_name=cognito.StandardAttribute(required=False, mutable=True),
                family_name=cognito.StandardAttribute(required=False, mutable=True),
            ),
            # Password policy (strong security requirements)
            password_policy=cognito.PasswordPolicy(
                min_length=12,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
                temp_password_validity=Duration.days(3),
            ),
            # Account recovery
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            # MFA configuration (optional, user can enable)
            mfa=cognito.Mfa.OPTIONAL,
            mfa_second_factor=cognito.MfaSecondFactor(sms=False, otp=True),
            # Email configuration (use Cognito default for now)
            email=cognito.UserPoolEmail.with_cognito(),
            # User invitation email
            user_invitation=cognito.UserInvitationConfig(
                email_subject="Welcome to Sake Sensei!",
                email_body=(
                    "Hello {username},\n\n"
                    "Welcome to Sake Sensei, your AI-powered sake sommelier!\n\n"
                    "Your temporary password is: {####}\n\n"
                    "Please sign in and change your password.\n\n"
                    "Best regards,\n"
                    "Sake Sensei Team"
                ),
            ),
            # User verification email
            user_verification=cognito.UserVerificationConfig(
                email_subject="Verify your Sake Sensei account",
                email_body=(
                    "Hello,\n\n"
                    "Thank you for signing up for Sake Sensei!\n\n"
                    "Your verification code is: {####}\n\n"
                    "Best regards,\n"
                    "Sake Sensei Team"
                ),
                email_style=cognito.VerificationEmailStyle.CODE,
            ),
            # Removal policy (retain for production safety)
            removal_policy=RemovalPolicy.RETAIN,
            # Advanced security (optional, incurs cost)
            # advanced_security_mode=cognito.AdvancedSecurityMode.ENFORCED,
        )

        # User Pool Client for Streamlit application
        self.user_pool_client = self.user_pool.add_client(
            "StreamlitClient",
            user_pool_client_name="SakeSensei-Streamlit",
            # OAuth flows for web application
            auth_flows=cognito.AuthFlow(
                user_password=True,  # Allow username/password auth
                user_srp=True,  # Secure Remote Password protocol
                admin_user_password=False,  # Disable admin-initiated auth
            ),
            # OAuth 2.0 configuration
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                    implicit_code_grant=False,  # Not recommended for web apps
                ),
                scopes=[
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.PROFILE,
                ],
                # Callback URLs (update with actual Streamlit URLs)
                callback_urls=[
                    "http://localhost:8501",  # Local development
                    "https://sakesensei.example.com",  # Production (update)
                ],
                logout_urls=[
                    "http://localhost:8501",
                    "https://sakesensei.example.com",
                ],
            ),
            # Token validity periods
            id_token_validity=Duration.hours(1),
            access_token_validity=Duration.hours(1),
            refresh_token_validity=Duration.days(30),
            # Prevent user existence errors (security best practice)
            prevent_user_existence_errors=True,
            # Generate client secret (required for server-side apps)
            generate_secret=False,  # Streamlit is a public client
        )

        # User Pool Domain for Hosted UI (optional)
        # Uncomment if using Cognito Hosted UI
        # self.user_pool_domain = self.user_pool.add_domain(
        #     "UserPoolDomain",
        #     cognito_domain=cognito.CognitoDomainOptions(
        #         domain_prefix=f"sakesensei-{Stack.of(self).account}"
        #     ),
        # )

        # Identity Pool for AWS credentials (optional)
        # Uncomment if Streamlit needs direct AWS access
        # self.identity_pool = cognito.CfnIdentityPool(
        #     self,
        #     "IdentityPool",
        #     identity_pool_name="SakeSenseiIdentityPool",
        #     allow_unauthenticated_identities=False,
        #     cognito_identity_providers=[
        #         cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
        #             client_id=self.user_pool_client.user_pool_client_id,
        #             provider_name=self.user_pool.user_pool_provider_name,
        #         )
        #     ],
        # )
