from aws_cdk import Stack, Tags
from constructs import Construct
from config.app_config import AppConfig

class TaggedStack(Stack):
    def __init__(self, scope: Construct, id: str, *, config: AppConfig, **kwargs):
        super().__init__(scope, id, **kwargs)

        tags = {
            "Service": config.app_name,
            "Team": config.team_name,
            "BudgetId": f"{config.environment.upper()}-{config.account_id}",
            "Environment": config.environment,
            "Stack": f"{config.stack_name}-{config.environment}",
            "ManagedBy": config.managed_by
        }

        for key, value in tags.items():
            Tags.of(self).add(key, value)