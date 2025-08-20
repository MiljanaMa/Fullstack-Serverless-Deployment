import os

class PipelineConfig:
    def __init__(self):
        self.region = os.getenv("REGION")
        self.account_id = os.getenv("ACCOUNT_ID")
        self.git_connection_id = os.getenv("GIT_CONNECTION_ID")
        self.git_owner = os.getenv("GIT_OWNER")
        self.git_repo = os.getenv("GIT_REPO")
        self.git_connection_arn = f"arn:aws:codeconnections:{self.region}:{self.account_id}:connection/{self.git_connection_id}"