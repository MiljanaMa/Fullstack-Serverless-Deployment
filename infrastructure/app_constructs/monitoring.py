from aws_cdk import (
    aws_logs as logs,
    aws_cloudwatch as cw,
    Duration,
    RemovalPolicy
)
from constructs import Construct
import aws_cdk.aws_cloudwatch_actions as cw_actions
from .lambda_module import LambdaModule
from .dynamo_db import DynamoDB
from .api_gateway import APIGateway
from .fargate import Fargate
from .alb import ALB
from config.app_config import AppConfig

class Monitoring(Construct):
    def __init__(self, scope: Construct, id: str, config: AppConfig, lambda_module: LambdaModule, 
                 api_gateway: APIGateway,dynamodb: DynamoDB, fargate: Fargate,
                 alb: ALB,**kwargs):
        super().__init__(scope, id, **kwargs)

        self.lambda_module = lambda_module
        self.config = config
        self.dynamodb = dynamodb
        self.api_gateway = api_gateway
        self.fargate = fargate
        self.alb = alb
        
        self.dashboard = cw.Dashboard(self, f"MainDashboard-{config.environment}-{config.app_name}",
            dashboard_name=f"MainDashboard-{config.environment}-{config.app_name}"
        )

        self._create_lambda_duration_alarms()
        self._create_lambda_error_alarms()
        self.create_dynamodb_alarms()
        self.create_api_gateway_alarms()
        self.create_fargate_alarms()
        self.create_alb_alarms()

    def _create_lambda_duration_alarms(self):
        for name, fn in self.lambda_module.lambdas.items():
            duration_metric = fn.metric_duration(
                period=Duration.minutes(2),
                statistic="Average"
            )

            alarm = cw.Alarm(
                self, f"{name}DurationAlarm-{self.config.environment}-{self.config.app_name}",
                metric=duration_metric,
                threshold=2000,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            ).apply_removal_policy(RemovalPolicy.DESTROY)
            #alarm.add_alarm_action(cw_actions.SnsAction(self.api_gateway.sns_topic))
            
            self.dashboard.add_widgets(
                cw.GraphWidget(
                    title=f"{name} Lambda Duration (ms)",
                    left=[duration_metric],
                    width=12
                )
            )

    def _create_lambda_error_alarms(self):
        for name, log_group in self.lambda_module.log_groups.items():
            error_metric_filter = logs.MetricFilter(
                self, f"{name}-500ErrorMetric-{self.config.environment}",
                log_group=log_group,
                metric_namespace=f"MyApiNamespace-{self.config.environment}",
                metric_name=f"{name}-500-Errors-{self.config.environment}",
                filter_pattern=logs.FilterPattern.literal('"error"'),
                metric_value="1"
            )
            error_metric = error_metric_filter.metric(
                statistic="Sum",
                period=Duration.minutes(1)
            )

            cw.Alarm(
                self, f"{name}ErrorAlarm-{self.config.environment}-{self.config.app_name}",
                metric=error_metric,
                threshold=1,
                evaluation_periods=1,
                datapoints_to_alarm=1,
                comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
                treat_missing_data=cw.TreatMissingData.NOT_BREACHING
            ).apply_removal_policy(RemovalPolicy.DESTROY)

            self.dashboard.add_widgets(
                cw.GraphWidget(
                    title=f"{name} Lambda Errors",
                    left=[error_metric],
                    width=12
                )
            )
    def create_dynamodb_alarms(self):
        self.read_capacity_alarm = cw.Alarm(
            self, f"ReadCapacityAlarm-{self.config.environment}",
            metric=self.dynamodb.table.metric_consumed_read_capacity_units(
                period=Duration.minutes(5)
            ),
            threshold=100,
            evaluation_periods=1,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
            alarm_description="Read capacity units exceed threshold",
            alarm_name=f"{self.dynamodb.construct_id}_read_capacity_alarm-{self.config.environment}-{self.config.app_name}"
        ).apply_removal_policy(RemovalPolicy.DESTROY)

        self.write_capacity_alarm = cw.Alarm(
            self, f"WriteCapacityAlarm-{self.config.environment}",
            metric=self.dynamodb.table.metric_consumed_write_capacity_units(
                period=Duration.minutes(5)
            ),
            threshold=100,
            evaluation_periods=1,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
            alarm_description="Write capacity units exceed threshold",
            alarm_name=f"{self.dynamodb.construct_id}_write_capacity_alarm-{self.config.environment}-{self.config.app_name}"
        ).apply_removal_policy(RemovalPolicy.DESTROY)

        self.throttled_requests_alarm = cw.Alarm(
            self, f"ThrottledRequestsAlarm-{self.config.environment}",
            metric=self.dynamodb.table.metric_throttled_requests(
                period=Duration.minutes(5)
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            alarm_description="DynamoDB table is throttling requests",
            alarm_name=f"{self.dynamodb.construct_id}_throttled_requests_alarm-{self.config.environment}-{self.config.app_name}"
        ).apply_removal_policy(RemovalPolicy.DESTROY)

        self.dashboard.add_widgets(
            cw.GraphWidget(
                title="DynamoDB Read Capacity",
                left=[self.dynamodb.table.metric_consumed_read_capacity_units()]
            ),
            cw.GraphWidget(
                title="DynamoDB Write Capacity",
                left=[self.dynamodb.table.metric_consumed_write_capacity_units()]
            ),
            cw.GraphWidget(
                title="DynamoDB Throttled Requests",
                left=[self.dynamodb.table.metric_throttled_requests()]
            )
        )
        
    def create_api_gateway_alarms(self):
        metric_filter = logs.MetricFilter(self, f"MetricFilter-{self.config.environment}",
            log_group=self.api_gateway.log_group,
            metric_namespace=f"MyApiNamespace-{self.config.environment}",
            metric_name=f"ServerErrorMetric-{self.config.environment}",
            filter_pattern=logs.FilterPattern.string_value('$.status', '=', '500'),
            metric_value="1",
        )
        error_metric = metric_filter.metric(
            statistic="Sum",
            period=Duration.minutes(1),
        )
        alarm = cw.Alarm(self, "ServerErrorAlarm",
            alarm_name=f"{self.api_gateway.api_name}-{self.config.environment}-API-Server-Error-Alarm",
            metric=error_metric,
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            alarm_description="Trigger when server error appears in logs",
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING
        )
        alarm.apply_removal_policy(RemovalPolicy.DESTROY)
        alarm.add_alarm_action(cw_actions.SnsAction(self.api_gateway.sns_topic))

        latency_metric = self.api_gateway.rest_api.metric_latency(
            statistic="Average",
            period=Duration.minutes(1)
        )

        cw.Alarm(self, f"APIGatewayLatencyAlarm-{self.config.environment}",
            alarm_name=f"{self.api_gateway.api_name}-{self.config.environment}-API-Latency-Alarm",
            metric=latency_metric,
            threshold=2000,
            evaluation_periods=1,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            alarm_description="Trigger when the latency is higher than 2 seconds",
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
            actions_enabled=True
        ).apply_removal_policy(RemovalPolicy.DESTROY)
        self.dashboard.add_widgets(
            cw.GraphWidget(
                title="API Gateway 5XX Errors",
                left=[error_metric],
                view=cw.GraphWidgetView.TIME_SERIES,
                width=12,
            ),
            cw.GraphWidget(
                title="API Gateway Latency",
                left=[latency_metric],
                view=cw.GraphWidgetView.TIME_SERIES,
                width=12,
            )
        )
    def create_fargate_alarms(self):
        cpu_util_widget = cw.GraphWidget(
            title="CPU Utilization",
            left=[
                cw.Metric(
                    namespace="AWS/ECS",
                    metric_name="CPUUtilization",
                    dimensions_map={
                        "ClusterName": self.fargate.ecs_cluster.cluster_name,
                        "ServiceName": self.fargate.service.service_name
                    },
                    statistic="Average",
                    period=Duration.minutes(5)
                )
            ]
        )
        memory_util_widget = cw.GraphWidget(
            title="Memory Utilization",
            left=[
                cw.Metric(
                    namespace="AWS/ECS",
                    metric_name="MemoryUtilization",
                    dimensions_map={
                        "ClusterName": self.fargate.ecs_cluster.cluster_name,
                        "ServiceName": self.fargate.service.service_name
                    },
                    statistic="Average",
                    period=Duration.minutes(5)
                )
            ]
        )
        self.dashboard.add_widgets(cpu_util_widget)
        self.dashboard.add_widgets(memory_util_widget)
        
        cpu_alarm = cw.Alarm(self.fargate.stack, f"{self.fargate.service_name}_high_cpu_alarm-{self.config.environment}-{self.config.app_name}",
            metric=cw.Metric(
                namespace="AWS/ECS",
                metric_name="CPUUtilization",
                dimensions_map={
                    "ClusterName": self.fargate.ecs_cluster.cluster_name,
                    "ServiceName": self.fargate.service.service_name
                },
                statistic="Average",
                period=Duration.minutes(5)
            ),
            threshold=80,
            evaluation_periods=2,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
            alarm_description="Alarm if ECS service CPU > 80% for 10 minutes"
        )
        memory_alarm = cw.Alarm(self.fargate.stack, f"{self.fargate.service_name}_high_memory_alarm-{self.config.environment}-{self.config.app_name}",
            metric=cw.Metric(
                namespace="AWS/ECS",
                metric_name="MemoryUtilization",
                dimensions_map={
                    "ClusterName": self.fargate.ecs_cluster.cluster_name,
                    "ServiceName": self.fargate.service.service_name
                },
                statistic="Average",
                period=Duration.minutes(5)
            ),
            threshold=80,
            evaluation_periods=2,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
            alarm_description="Alarm if ECS service Memory > 80% for 10 minutes"
        )
        self.dashboard.add_widgets(
            cw.AlarmWidget(
                title="ECS High CPU Alarm",
                alarm=cpu_alarm
            )
        )
        self.dashboard.add_widgets(
            cw.AlarmWidget(
                title="ECS High memory Alarm",
                alarm=memory_alarm
            )
        )
    def create_alb_alarms(self):
        request_metric = cw.Metric(
            namespace="AWS/ApplicationELB",
            metric_name="RequestCount",
            dimensions_map={
                "LoadBalancer": self.alb.load_balancer.load_balancer_name
            },
            statistic="Sum",
            period=Duration.minutes(1)
        )
        self.dashboard.add_widgets(
            cw.GraphWidget(
                title="ALB Request Count",
                left=[request_metric]
            )
        )
