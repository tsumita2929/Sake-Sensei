"""
Sake Sensei - Cognito Client

AWS Cognito API wrapper for user authentication operations.
"""

import os
from typing import Any

import boto3


class CognitoClient:
    """AWS Cognito client wrapper for authentication operations."""

    def __init__(
        self,
        user_pool_id: str | None = None,
        client_id: str | None = None,
        region: str | None = None,
    ) -> None:
        """Initialize Cognito client.

        Args:
            user_pool_id: Cognito User Pool ID (default: from env)
            client_id: Cognito App Client ID (default: from env)
            region: AWS region (default: from env)
        """
        self.user_pool_id = user_pool_id or os.getenv("COGNITO_USER_POOL_ID", "")
        self.client_id = client_id or os.getenv("COGNITO_CLIENT_ID", "")
        self.region = region or os.getenv("AWS_REGION", "us-west-2")

        if not self.user_pool_id or not self.client_id:
            raise ValueError("COGNITO_USER_POOL_ID and COGNITO_CLIENT_ID must be set")

        self.client = boto3.client("cognito-idp", region_name=self.region)

    def sign_up(
        self,
        email: str,
        password: str,
        given_name: str | None = None,
        family_name: str | None = None,
    ) -> dict[str, Any]:
        """Register a new user.

        Args:
            email: User email address
            password: User password
            given_name: User's given name (optional)
            family_name: User's family name (optional)

        Returns:
            Response from Cognito

        Raises:
            ClientError: If registration fails
        """
        user_attributes = [{"Name": "email", "Value": email}]

        if given_name:
            user_attributes.append({"Name": "given_name", "Value": given_name})
        if family_name:
            user_attributes.append({"Name": "family_name", "Value": family_name})

        return self.client.sign_up(
            ClientId=self.client_id,
            Username=email,
            Password=password,
            UserAttributes=user_attributes,
        )

    def confirm_sign_up(self, email: str, confirmation_code: str) -> dict[str, Any]:
        """Confirm user registration with verification code.

        Args:
            email: User email address
            confirmation_code: Verification code sent to email

        Returns:
            Response from Cognito

        Raises:
            ClientError: If confirmation fails
        """
        return self.client.confirm_sign_up(
            ClientId=self.client_id, Username=email, ConfirmationCode=confirmation_code
        )

    def sign_in(self, email: str, password: str) -> dict[str, Any]:
        """Sign in a user.

        Args:
            email: User email address
            password: User password

        Returns:
            Authentication result with tokens

        Raises:
            ClientError: If sign-in fails
        """
        return self.client.initiate_auth(
            ClientId=self.client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": email, "PASSWORD": password},
        )

    def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token from previous sign-in

        Returns:
            New authentication tokens

        Raises:
            ClientError: If token refresh fails
        """
        return self.client.initiate_auth(
            ClientId=self.client_id,
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={"REFRESH_TOKEN": refresh_token},
        )

    def sign_out(self, access_token: str) -> dict[str, Any]:
        """Sign out a user (invalidate tokens).

        Args:
            access_token: User's access token

        Returns:
            Response from Cognito

        Raises:
            ClientError: If sign-out fails
        """
        return self.client.global_sign_out(AccessToken=access_token)

    def forgot_password(self, email: str) -> dict[str, Any]:
        """Initiate password reset flow.

        Args:
            email: User email address

        Returns:
            Response from Cognito

        Raises:
            ClientError: If request fails
        """
        return self.client.forgot_password(ClientId=self.client_id, Username=email)

    def confirm_forgot_password(
        self, email: str, confirmation_code: str, new_password: str
    ) -> dict[str, Any]:
        """Confirm password reset with verification code.

        Args:
            email: User email address
            confirmation_code: Verification code sent to email
            new_password: New password

        Returns:
            Response from Cognito

        Raises:
            ClientError: If password reset fails
        """
        return self.client.confirm_forgot_password(
            ClientId=self.client_id,
            Username=email,
            ConfirmationCode=confirmation_code,
            Password=new_password,
        )

    def change_password(
        self, access_token: str, previous_password: str, proposed_password: str
    ) -> dict[str, Any]:
        """Change user password.

        Args:
            access_token: User's access token
            previous_password: Current password
            proposed_password: New password

        Returns:
            Response from Cognito

        Raises:
            ClientError: If password change fails
        """
        return self.client.change_password(
            AccessToken=access_token,
            PreviousPassword=previous_password,
            ProposedPassword=proposed_password,
        )

    def get_user(self, access_token: str) -> dict[str, Any]:
        """Get user attributes from access token.

        Args:
            access_token: User's access token

        Returns:
            User attributes

        Raises:
            ClientError: If request fails
        """
        return self.client.get_user(AccessToken=access_token)

    def update_user_attributes(
        self, access_token: str, attributes: dict[str, str]
    ) -> dict[str, Any]:
        """Update user attributes.

        Args:
            access_token: User's access token
            attributes: Dictionary of attributes to update

        Returns:
            Response from Cognito

        Raises:
            ClientError: If update fails
        """
        user_attributes = [{"Name": k, "Value": v} for k, v in attributes.items()]
        return self.client.update_user_attributes(
            AccessToken=access_token, UserAttributes=user_attributes
        )

    def delete_user(self, access_token: str) -> dict[str, Any]:
        """Delete user account.

        Args:
            access_token: User's access token

        Returns:
            Response from Cognito

        Raises:
            ClientError: If deletion fails
        """
        return self.client.delete_user(AccessToken=access_token)
