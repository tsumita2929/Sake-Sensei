"""CloudWatch monitoring stack for SakeSensei.

This stack creates:
- CloudWatch Log Groups for all services
- CloudWatch Alarms for critical metrics
- CloudWatch Dashboard for unified monitoring
"""

from aws_cdk import (
    Duration,
    Stack,
)
from aws_cdk import (
    aws_cloudwatch as cloudwatch,
)
from aws_cdk import (
    aws_cloudwatch_actions as cw_actions,
)
from aws_cdk import (
    aws_logs as logs,
)
from aws_cdk import (
    aws_sns as sns,
)
from aws_cdk import (
    aws_sns_subscriptions as subscriptions,
)
from constructs import Construct


class MonitoringStack(Stack):
    """CloudWatch monitoring stack."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        lambda_functions: dict,
        ecs_cluster_name: str,
        ecs_service_name: str,
        alarm_email: str | None = None,
        **kwargs,
    ) -> None:
        """Initialize monitoring stack.

        Args:
            scope: CDK scope
            construct_id: Stack ID
            lambda_functions: Dictionary of Lambda function names to IFunction
            ecs_cluster_name: ECS cluster name
            ecs_service_name: ECS service name
            alarm_email: Email address for alarm notifications
            **kwargs: Additional stack arguments
        """
        super().__init__(scope, construct_id, **kwargs)

        # SNS topic for alarms
        self.alarm_topic = sns.Topic(
            self,
            "AlarmTopic",
            topic_name="SakeSensei-Alarms",
            display_name="SakeSensei CloudWatch Alarms",
        )

        if alarm_email:
            self.alarm_topic.add_subscription(subscriptions.EmailSubscription(alarm_email))

        # Create log groups
        self.log_groups = self._create_log_groups(lambda_functions)

        # Create metric alarms
        self.alarms = self._create_alarms(lambda_functions, ecs_cluster_name, ecs_service_name)

        # Create dashboard
        self.dashboard = self._create_dashboard(
            lambda_functions, ecs_cluster_name, ecs_service_name
        )

    def _create_log_groups(self, lambda_functions: dict) -> dict:
        """Create CloudWatch log groups for all services.

        Args:
            lambda_functions: Dictionary of Lambda functions

        Returns:
            Dictionary of log group names to LogGroup constructs
        """
        log_groups = {}

        # Lambda log groups (created automatically by Lambda, but we configure retention)
        for name, function in lambda_functions.items():
            log_group = logs.LogGroup(
                self,
                f"{name}LogGroup",
                log_group_name=f"/aws/lambda/{function.function_name}",
                retention=logs.RetentionDays.ONE_MONTH,
                removal_policy=None,  # Retain logs on stack deletion
            )
            log_groups[f"lambda_{name}"] = log_group

        # ECS application log group
        log_groups["ecs_app"] = logs.LogGroup(
            self,
            "ECSAppLogGroup",
            log_group_name="/ecs/sakesensei/streamlit-app",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=None,
        )

        # Agent log group (if using AgentCore logging)
        log_groups["agent"] = logs.LogGroup(
            self,
            "AgentLogGroup",
            log_group_name="/agentcore/sakesensei/agent",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=None,
        )

        return log_groups

    def _create_alarms(
        self,
        lambda_functions: dict,
        ecs_cluster_name: str,
        ecs_service_name: str,
    ) -> dict:
        """Create CloudWatch alarms for critical metrics.

        Args:
            lambda_functions: Dictionary of Lambda functions
            ecs_cluster_name: ECS cluster name
            ecs_service_name: ECS service name

        Returns:
            Dictionary of alarm names to Alarm constructs
        """
        alarms = {}
        alarm_action = cw_actions.SnsAction(self.alarm_topic)

        # Lambda alarms
        for name, function in lambda_functions.items():
            # Error rate alarm
            error_alarm = cloudwatch.Alarm(
                self,
                f"{name}ErrorAlarm",
                alarm_name=f"SakeSensei-{name}-Errors",
                metric=function.metric_errors(
                    period=Duration.minutes(5),
                    statistic="Sum",
                ),
                threshold=5,
                evaluation_periods=2,
                datapoints_to_alarm=2,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
                alarm_description=f"Lambda {name} error rate is too high",
            )
            error_alarm.add_alarm_action(alarm_action)
            alarms[f"{name}_errors"] = error_alarm

            # Duration alarm (P99)
            duration_alarm = cloudwatch.Alarm(
                self,
                f"{name}DurationAlarm",
                alarm_name=f"SakeSensei-{name}-Duration",
                metric=function.metric_duration(
                    period=Duration.minutes(5),
                    statistic="p99",
                ),
                threshold=3000,  # 3 seconds
                evaluation_periods=2,
                datapoints_to_alarm=2,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
                alarm_description=f"Lambda {name} P99 duration exceeds 3s",
            )
            duration_alarm.add_alarm_action(alarm_action)
            alarms[f"{name}_duration"] = duration_alarm

            # Throttle alarm
            throttle_alarm = cloudwatch.Alarm(
                self,
                f"{name}ThrottleAlarm",
                alarm_name=f"SakeSensei-{name}-Throttles",
                metric=function.metric_throttles(
                    period=Duration.minutes(5),
                    statistic="Sum",
                ),
                threshold=10,
                evaluation_periods=1,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
                alarm_description=f"Lambda {name} is being throttled",
            )
            throttle_alarm.add_alarm_action(alarm_action)
            alarms[f"{name}_throttles"] = throttle_alarm

        # ECS service alarms
        # CPU utilization
        ecs_cpu_alarm = cloudwatch.Alarm(
            self,
            "ECSCPUAlarm",
            alarm_name="SakeSensei-ECS-HighCPU",
            metric=cloudwatch.Metric(
                namespace="AWS/ECS",
                metric_name="CPUUtilization",
                dimensions_map={
                    "ClusterName": ecs_cluster_name,
                    "ServiceName": ecs_service_name,
                },
                period=Duration.minutes(5),
                statistic="Average",
            ),
            threshold=80,  # 80% CPU
            evaluation_periods=2,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            alarm_description="ECS service CPU utilization is high",
        )
        ecs_cpu_alarm.add_alarm_action(alarm_action)
        alarms["ecs_cpu"] = ecs_cpu_alarm

        # Memory utilization
        ecs_memory_alarm = cloudwatch.Alarm(
            self,
            "ECSMemoryAlarm",
            alarm_name="SakeSensei-ECS-HighMemory",
            metric=cloudwatch.Metric(
                namespace="AWS/ECS",
                metric_name="MemoryUtilization",
                dimensions_map={
                    "ClusterName": ecs_cluster_name,
                    "ServiceName": ecs_service_name,
                },
                period=Duration.minutes(5),
                statistic="Average",
            ),
            threshold=80,  # 80% Memory
            evaluation_periods=2,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            alarm_description="ECS service memory utilization is high",
        )
        ecs_memory_alarm.add_alarm_action(alarm_action)
        alarms["ecs_memory"] = ecs_memory_alarm

        # Application Load Balancer alarms
        # Target response time
        alb_response_alarm = cloudwatch.Alarm(
            self,
            "ALBResponseTimeAlarm",
            alarm_name="SakeSensei-ALB-SlowResponse",
            metric=cloudwatch.Metric(
                namespace="AWS/ApplicationELB",
                metric_name="TargetResponseTime",
                dimensions_map={
                    # Note: You'll need to provide the actual ALB name
                    # "LoadBalancer": "app/...",
                },
                period=Duration.minutes(5),
                statistic="p99",
            ),
            threshold=5,  # 5 seconds
            evaluation_periods=2,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            alarm_description="ALB P99 response time exceeds 5s",
        )
        alb_response_alarm.add_alarm_action(alarm_action)
        alarms["alb_response"] = alb_response_alarm

        # 5XX errors
        alb_5xx_alarm = cloudwatch.Alarm(
            self,
            "ALB5XXAlarm",
            alarm_name="SakeSensei-ALB-5XXErrors",
            metric=cloudwatch.Metric(
                namespace="AWS/ApplicationELB",
                metric_name="HTTPCode_Target_5XX_Count",
                dimensions_map={
                    # Note: You'll need to provide the actual ALB name
                },
                period=Duration.minutes(5),
                statistic="Sum",
            ),
            threshold=10,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            alarm_description="ALB is returning too many 5XX errors",
        )
        alb_5xx_alarm.add_alarm_action(alarm_action)
        alarms["alb_5xx"] = alb_5xx_alarm

        return alarms

    def _create_dashboard(
        self,
        lambda_functions: dict,
        ecs_cluster_name: str,
        ecs_service_name: str,
    ) -> cloudwatch.Dashboard:
        """Create CloudWatch dashboard for unified monitoring.

        Args:
            lambda_functions: Dictionary of Lambda functions
            ecs_cluster_name: ECS cluster name
            ecs_service_name: ECS service name

        Returns:
            CloudWatch Dashboard
        """
        dashboard = cloudwatch.Dashboard(
            self,
            "MonitoringDashboard",
            dashboard_name="SakeSensei-Monitoring",
        )

        # Lambda metrics widgets
        lambda_widgets = []

        # Lambda invocations
        lambda_invocations_widget = cloudwatch.GraphWidget(
            title="Lambda Invocations",
            left=[
                func.metric_invocations(period=Duration.minutes(5))
                for func in lambda_functions.values()
            ],
            width=12,
            height=6,
        )
        lambda_widgets.append(lambda_invocations_widget)

        # Lambda errors
        lambda_errors_widget = cloudwatch.GraphWidget(
            title="Lambda Errors",
            left=[
                func.metric_errors(period=Duration.minutes(5)) for func in lambda_functions.values()
            ],
            width=12,
            height=6,
        )
        lambda_widgets.append(lambda_errors_widget)

        # Lambda duration
        lambda_duration_widget = cloudwatch.GraphWidget(
            title="Lambda Duration (P99)",
            left=[
                func.metric_duration(period=Duration.minutes(5), statistic="p99")
                for func in lambda_functions.values()
            ],
            width=12,
            height=6,
        )
        lambda_widgets.append(lambda_duration_widget)

        # Lambda throttles
        lambda_throttles_widget = cloudwatch.GraphWidget(
            title="Lambda Throttles",
            left=[
                func.metric_throttles(period=Duration.minutes(5))
                for func in lambda_functions.values()
            ],
            width=12,
            height=6,
        )
        lambda_widgets.append(lambda_throttles_widget)

        # ECS metrics widgets
        ecs_widgets = []

        # ECS CPU/Memory
        ecs_resources_widget = cloudwatch.GraphWidget(
            title="ECS Resource Utilization",
            left=[
                cloudwatch.Metric(
                    namespace="AWS/ECS",
                    metric_name="CPUUtilization",
                    dimensions_map={
                        "ClusterName": ecs_cluster_name,
                        "ServiceName": ecs_service_name,
                    },
                    period=Duration.minutes(5),
                    statistic="Average",
                    label="CPU %",
                ),
            ],
            right=[
                cloudwatch.Metric(
                    namespace="AWS/ECS",
                    metric_name="MemoryUtilization",
                    dimensions_map={
                        "ClusterName": ecs_cluster_name,
                        "ServiceName": ecs_service_name,
                    },
                    period=Duration.minutes(5),
                    statistic="Average",
                    label="Memory %",
                ),
            ],
            width=12,
            height=6,
        )
        ecs_widgets.append(ecs_resources_widget)

        # ALB metrics
        alb_widgets = []

        # ALB requests and errors
        alb_requests_widget = cloudwatch.GraphWidget(
            title="ALB Requests & Errors",
            left=[
                cloudwatch.Metric(
                    namespace="AWS/ApplicationELB",
                    metric_name="RequestCount",
                    period=Duration.minutes(5),
                    statistic="Sum",
                    label="Total Requests",
                ),
            ],
            right=[
                cloudwatch.Metric(
                    namespace="AWS/ApplicationELB",
                    metric_name="HTTPCode_Target_5XX_Count",
                    period=Duration.minutes(5),
                    statistic="Sum",
                    label="5XX Errors",
                ),
                cloudwatch.Metric(
                    namespace="AWS/ApplicationELB",
                    metric_name="HTTPCode_Target_4XX_Count",
                    period=Duration.minutes(5),
                    statistic="Sum",
                    label="4XX Errors",
                ),
            ],
            width=12,
            height=6,
        )
        alb_widgets.append(alb_requests_widget)

        # ALB response time
        alb_latency_widget = cloudwatch.GraphWidget(
            title="ALB Response Time",
            left=[
                cloudwatch.Metric(
                    namespace="AWS/ApplicationELB",
                    metric_name="TargetResponseTime",
                    period=Duration.minutes(5),
                    statistic="p99",
                    label="P99",
                ),
                cloudwatch.Metric(
                    namespace="AWS/ApplicationELB",
                    metric_name="TargetResponseTime",
                    period=Duration.minutes(5),
                    statistic="Average",
                    label="Average",
                ),
            ],
            width=12,
            height=6,
        )
        alb_widgets.append(alb_latency_widget)

        # Add all widgets to dashboard
        dashboard.add_widgets(*lambda_widgets)
        dashboard.add_widgets(*ecs_widgets)
        dashboard.add_widgets(*alb_widgets)

        # Add alarm status widget
        alarm_status_widget = cloudwatch.AlarmStatusWidget(
            title="Alarm Status",
            alarms=list(self.alarms.values()),
            width=24,
            height=6,
        )
        dashboard.add_widgets(alarm_status_widget)

        return dashboard
