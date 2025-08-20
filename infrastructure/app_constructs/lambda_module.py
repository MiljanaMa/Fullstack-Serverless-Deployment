from aws_cdk import (
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_logs as logs,
    RemovalPolicy,
    Duration
)
from constructs import Construct
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
lambda_code_path = project_root / 'lambda'
lambda_layer_code_path = project_root / 'lambda/lambda_layer'

from config.app_config import AppConfig

class LambdaModule(Construct):
    def __init__(self, scope: Construct, construct_id: str, config: AppConfig, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.scope = scope
        #self.dashboard = dashboard
        self.table_arn = config.table_arn
        self.config = config
        self.lambdas = {}
        self.log_groups = {}

        self.lambda_definitions = {
            "GetAllGoals": {
                "handler": "get_all_goals.lambda_handler",
                "path":    "get_all_goals",
                "actions": ["dynamodb:Query", "dynamodb:Scan"]
            },
            "CreateGoal": {
                "handler": "create_goal.lambda_handler",
                "path":    "create_goal",
                "actions": ["dynamodb:PutItem", "dynamodb:GetItem"]
            },
            "GetGoal": {
                "handler": "get_goal.lambda_handler",
                "path":    "get_goal",
                "actions": ["dynamodb:GetItem"]
            },
            "UpdateGoal": {
                "handler": "update_goal.lambda_handler",
                "path":    "update_goal",
                "actions": ["dynamodb:UpdateItem", "dynamodb:GetItem"]
            },
            "DeleteGoal": {
                "handler": "delete_goal.lambda_handler",
                "path":    "delete_goal",
                "actions": ["dynamodb:DeleteItem", "dynamodb:GetItem"]
            }
        }
        utils_layer = _lambda.LayerVersion(
            self, f"UtilsLayer-{config.environment}",
            code=_lambda.Code.from_asset(str(lambda_layer_code_path)),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_10],
            description="Shared utils layer"
        )

        log_group_prefix = f"{construct_id}_log_group-{config.environment}-{config.app_name}_"

        for name, details in self.lambda_definitions.items():
            role = self._create_lambda_role(f"{name}LambdaRole-{config.environment}", details["actions"])
            log_group = self._create_log_group(log_group_prefix, name)
            lambda_fn = self._create_lambda(name, details["handler"], details["path"], role, log_group, utils_layer)

            self.lambdas[name] = lambda_fn
            self.log_groups[name] = log_group


    def _create_lambda_role(self, role_name: str, actions: list[str]) ->iam.Role:
        role = iam.Role(
            self, role_name,
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            role_name=role_name,
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
                # , iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")  Lambda communication with VPC through VPC Endpoint?
            ]
        )

        role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=actions,
            resources=[self.table_arn]
        ))

        return role
    
    def _create_lambda(self, name: str, handler: str, path: str, role: iam.Role, log_group: logs.LogGroup, utils_layer: _lambda.LayerVersion) -> _lambda.Function:
        lambda_fn = _lambda.Function(
            self, f"{name}Function",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler=handler,
            timeout =Duration.seconds(5),
            code=_lambda.Code.from_asset(str(lambda_code_path/path)),
            log_group=log_group,
            layers=[utils_layer],
            environment={
                'GOALS_TABLE_NAME': self.config.full_table_name
            },
            role=role
        )
        lambda_fn.node.add_dependency(log_group)
        lambda_fn.node.add_dependency(role)
        return lambda_fn
    
    def _create_log_group(self, log_group_prefix: str, log_group_name: str, retention: logs.RetentionDays = logs.RetentionDays.ONE_WEEK) -> logs.LogGroup:
        log_group = logs.LogGroup(
            self.scope, log_group_prefix + log_group_name,
            log_group_name=log_group_prefix + log_group_name,
            retention=retention,
            removal_policy=RemovalPolicy.DESTROY,
            data_protection_policy=logs.DataProtectionPolicy(
                name="EmailRedactionPolicy",
                description="Mask email addresses in logs",
                identifiers=[logs.DataIdentifier.EMAILADDRESS]
            )
        )
        return log_group