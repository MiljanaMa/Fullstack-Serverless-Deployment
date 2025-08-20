from dotenv import load_dotenv
import aws_cdk as cdk
from aws_cdk.assertions import Template
from config.app_config import AppConfig
from stacks.main_stack.main_stack import MainStack
import os

# Load the .env file
# Determine which .env file to load (default: .env.test)
env_type = os.getenv("ENV", "fail")  # Defaults to 'test' if not set
env_file = f"config/.env.{env_type}"

# Load the .env file
load_dotenv(dotenv_path=env_file)

# Initialize config from env
config = AppConfig()  # reads from os.environ inside

def test_main_stack_synthesizes():

    app = cdk.App()
        
    env = cdk.Environment(account=config.account_id, region=config.region)
    stack = MainStack(app, "TestMainStack", config=config, env=env)

    template = Template.from_stack(stack)

    # Example assertion: is the DynamoDB table created?
    template.has_resource_properties("AWS::DynamoDB::Table", {
        "TableName": config.full_table_name
    })