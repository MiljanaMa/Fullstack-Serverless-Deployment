#!/usr/bin/env python3
from dotenv import load_dotenv 
import aws_cdk as cdk
from stacks.main_stack.main_stack import MainStack
from stacks.pipeline.pipeline_stack import PipelineStack
from config.app_config import AppConfig 
from config.pipeline.pipeline_config import PipelineConfig

app = cdk.App()

# Get environment from context or use 'dev' as default
environment = app.node.try_get_context('environment') or 'dev'

# Load the correct .env file based on environment
dotenv_path = f"config/.env.{environment}"
config_paths = (f"config/.env.{environment}", "config/pipeline/.env")
for path in config_paths:
    load_dotenv(dotenv_path=path)


# Use your AppConfig helper class to access values safely
config = AppConfig()  # reads from os.environ inside

# Optionally pass env to CDK
cdk_env = cdk.Environment(account=config.account_id, region=config.region)

MainStack(app, f"MainStack-{environment}", config=config, env=cdk_env)

pipeline_config = PipelineConfig()
PipelineStack(app, "PipelineStack", config=pipeline_config, env=cdk_env)

app.synth()
