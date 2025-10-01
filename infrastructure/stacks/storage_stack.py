"""
Sake Sensei - S3 Storage Stack

This stack defines S3 buckets for image storage and static assets.
"""

from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from constructs import Construct


class StorageStack(Stack):
    """Stack for S3 storage resources."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """Initialize the Storage Stack.

        Args:
            scope: CDK scope
            construct_id: Stack identifier
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        # Images Bucket for sake labels and photos
        self.images_bucket = s3.Bucket(
            self,
            "ImagesBucket",
            bucket_name=f"sakesensei-images-{Stack.of(self).account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=False,
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
            # CORS configuration for Streamlit uploads
            cors=[
                s3.CorsRule(
                    allowed_methods=[
                        s3.HttpMethods.GET,
                        s3.HttpMethods.PUT,
                        s3.HttpMethods.POST,
                    ],
                    allowed_origins=["*"],  # TODO: Restrict to actual domain in production
                    allowed_headers=["*"],
                    max_age=3000,
                )
            ],
            # Lifecycle rules
            lifecycle_rules=[
                # Delete incomplete multipart uploads after 7 days
                s3.LifecycleRule(
                    id="DeleteIncompleteMultipartUploads",
                    abort_incomplete_multipart_upload_after=Duration.days(7),
                    enabled=True,
                ),
                # Transition old images to Intelligent-Tiering after 90 days
                s3.LifecycleRule(
                    id="TransitionToIntelligentTiering",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INTELLIGENT_TIERING,
                            transition_after=Duration.days(90),
                        )
                    ],
                    enabled=True,
                ),
                # Delete temporary uploads after 1 day
                s3.LifecycleRule(
                    id="DeleteTempUploads",
                    prefix="temp/",
                    expiration=Duration.days(1),
                    enabled=True,
                ),
            ],
        )

        # Add bucket policy for Lambda access
        self.images_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="AllowLambdaRead",
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal("lambda.amazonaws.com")],
                actions=["s3:GetObject", "s3:ListBucket"],
                resources=[
                    self.images_bucket.bucket_arn,
                    f"{self.images_bucket.bucket_arn}/*",
                ],
                conditions={"StringEquals": {"aws:SourceAccount": Stack.of(self).account}},
            )
        )
