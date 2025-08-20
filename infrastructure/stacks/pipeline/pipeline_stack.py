from aws_cdk import (
    Stack,
)

from constructs import Construct

from app_constructs.pipeline import Pipeline
from config.pipeline.pipeline_config import PipelineConfig



class PipelineStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, config: PipelineConfig, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
    
        Pipeline(self, "DevelopPipeline", "develop", False, config)
        Pipeline(self, "MainPipeline", "main", False, config)
        Pipeline(self, "FeaturePipeline", "feature/**", True, config)