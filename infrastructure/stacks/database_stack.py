"""
Sake Sensei - DynamoDB Database Stack

This stack defines all DynamoDB tables for the Sake Sensei application.
"""

from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct


class DatabaseStack(Stack):
    """Stack for DynamoDB tables."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """Initialize the Database Stack.

        Args:
            scope: CDK scope
            construct_id: Stack identifier
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        # Users Table
        self.users_table = dynamodb.Table(
            self,
            "UsersTable",
            table_name="SakeSensei-Users",
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            # TODO: Migrate to point_in_time_recovery_specification in CDK v3
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Add GSI for email lookup
        self.users_table.add_global_secondary_index(
            index_name="EmailIndex",
            partition_key=dynamodb.Attribute(name="email", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Sake Master Table
        self.sake_master_table = dynamodb.Table(
            self,
            "SakeMasterTable",
            table_name="SakeSensei-SakeMaster",
            partition_key=dynamodb.Attribute(name="sake_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            # TODO: Migrate to point_in_time_recovery_specification in CDK v3
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Add GSI for brewery lookup
        self.sake_master_table.add_global_secondary_index(
            index_name="BreweryIndex",
            partition_key=dynamodb.Attribute(name="brewery_id", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Add GSI for category filter
        self.sake_master_table.add_global_secondary_index(
            index_name="CategoryIndex",
            partition_key=dynamodb.Attribute(name="category", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="price", type=dynamodb.AttributeType.NUMBER),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Brewery Master Table
        self.brewery_master_table = dynamodb.Table(
            self,
            "BreweryMasterTable",
            table_name="SakeSensei-BreweryMaster",
            partition_key=dynamodb.Attribute(name="brewery_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            # TODO: Migrate to point_in_time_recovery_specification in CDK v3
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Add GSI for prefecture search
        self.brewery_master_table.add_global_secondary_index(
            index_name="PrefectureIndex",
            partition_key=dynamodb.Attribute(name="prefecture", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Tasting Records Table
        self.tasting_records_table = dynamodb.Table(
            self,
            "TastingRecordsTable",
            table_name="SakeSensei-TastingRecords",
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="record_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            # TODO: Migrate to point_in_time_recovery_specification in CDK v3
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Add GSI for sake lookup (to find all tastings of a specific sake)
        self.tasting_records_table.add_global_secondary_index(
            index_name="SakeIndex",
            partition_key=dynamodb.Attribute(name="sake_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="tasting_date", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Add GSI for user timeline (sort by date)
        self.tasting_records_table.add_global_secondary_index(
            index_name="UserTimelineIndex",
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="tasting_date", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )
