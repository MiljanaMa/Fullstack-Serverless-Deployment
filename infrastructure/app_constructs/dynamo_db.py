from aws_cdk import (
    aws_dynamodb as dynamodb,
    RemovalPolicy
)
from constructs import Construct
from config.app_config import AppConfig

class DynamoDB(Construct):
    def __init__(self, scope: Construct, construct_id: str,  config: AppConfig, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.construct_id = construct_id
        self.table = dynamodb.Table(
            self, config.table_name,
            table_name=config.full_table_name,
            partition_key=dynamodb.Attribute(
                name="userId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="goalId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            removal_policy=RemovalPolicy.DESTROY
        )