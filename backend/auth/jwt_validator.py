"""
Sake Sensei - JWT Validator

JWT token validation for Cognito-issued tokens.
"""

import os
from typing import Any

import jwt
from jwt import PyJWKClient


class JWTValidator:
    """JWT token validator for AWS Cognito tokens."""

    def __init__(
        self,
        user_pool_id: str | None = None,
        region: str | None = None,
        client_id: str | None = None,
    ) -> None:
        """Initialize JWT validator.

        Args:
            user_pool_id: Cognito User Pool ID (default: from env)
            region: AWS region (default: from env)
            client_id: Cognito App Client ID for audience validation (default: from env)
        """
        self.user_pool_id = user_pool_id or os.getenv("COGNITO_USER_POOL_ID", "")
        self.region = region or os.getenv("AWS_REGION", "us-west-2")
        self.client_id = client_id or os.getenv("COGNITO_CLIENT_ID", "")

        if not self.user_pool_id:
            raise ValueError("COGNITO_USER_POOL_ID must be set")

        # Construct Cognito JWKS URL
        self.jwks_url = (
            f"https://cognito-idp.{self.region}.amazonaws.com/"
            f"{self.user_pool_id}/.well-known/jwks.json"
        )

        # Initialize PyJWKClient for fetching public keys
        self.jwk_client = PyJWKClient(self.jwks_url, cache_keys=True)

    def validate_token(
        self, token: str, token_use: str = "id", verify_aud: bool = True
    ) -> dict[str, Any]:
        """Validate JWT token.

        Args:
            token: JWT token string
            token_use: Expected token use ('id' or 'access')
            verify_aud: Whether to verify audience claim

        Returns:
            Decoded token claims

        Raises:
            jwt.InvalidTokenError: If token is invalid
            jwt.ExpiredSignatureError: If token is expired
            jwt.InvalidAudienceError: If audience is invalid
        """
        # Get signing key from JWKS
        signing_key = self.jwk_client.get_signing_key_from_jwt(token)

        # Decode and validate token
        options: dict[str, bool] = {}
        if not verify_aud or not self.client_id:
            # Skip audience verification if not required or client_id not set
            options["verify_aud"] = False

        claims: dict[str, Any] = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options=options,
            audience=self.client_id if verify_aud and self.client_id else None,
        )

        # Verify token_use claim
        if claims.get("token_use") != token_use:
            raise jwt.InvalidTokenError(
                f"Token use is '{claims.get('token_use')}', expected '{token_use}'"
            )

        # Verify issuer
        expected_iss = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"
        if claims.get("iss") != expected_iss:
            raise jwt.InvalidTokenError(
                f"Invalid issuer: {claims.get('iss')}, expected {expected_iss}"
            )

        return claims

    def validate_id_token(self, token: str) -> dict[str, Any]:
        """Validate Cognito ID token.

        Args:
            token: ID token string

        Returns:
            Decoded token claims with user info

        Raises:
            jwt.InvalidTokenError: If token is invalid
        """
        return self.validate_token(token, token_use="id", verify_aud=True)

    def validate_access_token(self, token: str) -> dict[str, Any]:
        """Validate Cognito access token.

        Args:
            token: Access token string

        Returns:
            Decoded token claims

        Raises:
            jwt.InvalidTokenError: If token is invalid
        """
        # Access tokens don't have audience claim
        return self.validate_token(token, token_use="access", verify_aud=False)

    def get_user_id(self, token: str) -> str:
        """Extract user ID from token.

        Args:
            token: ID or access token

        Returns:
            User ID (sub claim)

        Raises:
            jwt.InvalidTokenError: If token is invalid
        """
        claims = self.validate_token(token, token_use="id", verify_aud=False)
        user_id = claims.get("sub")
        if not user_id:
            raise jwt.InvalidTokenError("Token does not contain 'sub' claim")
        return str(user_id)

    def get_user_email(self, token: str) -> str:
        """Extract user email from ID token.

        Args:
            token: ID token

        Returns:
            User email

        Raises:
            jwt.InvalidTokenError: If token is invalid or missing email
        """
        claims = self.validate_id_token(token)
        email = claims.get("email")
        if not email:
            raise jwt.InvalidTokenError("Token does not contain 'email' claim")
        return str(email)

    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired without full validation.

        Args:
            token: JWT token

        Returns:
            True if expired, False otherwise
        """
        try:
            # Decode without verification to check expiration
            jwt.decode(token, options={"verify_signature": False})
            return False
        except jwt.ExpiredSignatureError:
            return True
        except jwt.InvalidTokenError:
            # Other errors, consider as expired for safety
            return True
