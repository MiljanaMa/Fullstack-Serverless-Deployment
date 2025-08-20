from aws_cdk import (
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as cpactions,
    aws_codebuild as codebuild,
    aws_iam as iam,
)
from constructs import Construct
from config.pipeline.pipeline_config import PipelineConfig

class Pipeline(Construct):
    def __init__(self, scope: Construct, service_name, branch, is_feature_branch: bool, config: PipelineConfig):
        super().__init__(scope, f"{service_name}_id-{config.region}")

        source_artifact = codepipeline.Artifact("SourceArtifact")
        react_app_build_artifact = codepipeline.Artifact("ReactAppBuild")

        # One CodeBuild project reused with different buildspec overrides
        test_react_project = codebuild.PipelineProject(self, f"{service_name}-TestReactProject-{config.region}",build_spec=codebuild.BuildSpec.from_source_filename("pipeline/react-test-buildspec.yml"))
        tetst_cdk_project = codebuild.PipelineProject(self, f"{service_name}-TestCDKProject-{config.region}",build_spec=codebuild.BuildSpec.from_source_filename("pipeline/cdk-test-buildspec.yml"))
        test_synth_project = codebuild.PipelineProject(self, f"{service_name}-TestSynthProject-{config.region}",build_spec=codebuild.BuildSpec.from_source_filename("pipeline/synth-buildspec.yml"))
        build_project = codebuild.PipelineProject(self, f"{service_name}-BuildProject-{config.region}",build_spec=codebuild.BuildSpec.from_source_filename("pipeline/build-image-buildspec.yml"))
        build_project.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:CompleteLayerUpload",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:InitiateLayerUpload",
                    "ecr:PutImage",
                    "ecr:UploadLayerPart",
                    "ecr:StartImageScan",
                    "ecr:DescribeImageScanFindings"
                ],
                resources=["*"]
            )
        )
        cdk_deploy_project = codebuild.PipelineProject(self, f"{service_name}-DeployProject-{config.region}",build_spec=codebuild.BuildSpec.from_source_filename("pipeline/cdk-buildspec.yml"))
        cdk_deploy_project.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["*"],
                resources=["*"]
            )
        )

        pipeline = codepipeline.Pipeline(self, service_name,pipeline_type=codepipeline.PipelineType.V2, execution_mode=codepipeline.ExecutionMode.QUEUED)

        pipeline.add_stage(
            stage_name="Source",
            actions=[cpactions.CodeStarConnectionsSourceAction(
                action_name=f"GitHubSource",
                variables_namespace="SourceVariables",
                owner=config.git_owner,
                repo=config.git_repo,
                branch=branch,
                connection_arn=config.git_connection_arn,
                output=source_artifact,
                trigger_on_push=True,
            )],
        )

        git_branch_env = {
            "GIT_BRANCH": codebuild.BuildEnvironmentVariable(value="#{SourceVariables.BranchName}", type=codebuild.BuildEnvironmentVariableType.PLAINTEXT)
        }

        # Test Stage
        pipeline.add_stage(
            stage_name="Test",
            actions=[
                cpactions.CodeBuildAction(
                    action_name="TestAndBuildReactApp",
                    project=test_react_project,
                    input=source_artifact,
                    outputs=[react_app_build_artifact],
                ),
                cpactions.CodeBuildAction(
                    action_name="TestCDK",
                    project=tetst_cdk_project,
                    input=source_artifact,
                    environment_variables=git_branch_env
                ),
                cpactions.CodeBuildAction(
                    action_name="TestSynth",
                    project=test_synth_project,
                    input=source_artifact,
                    environment_variables=git_branch_env
                )
            ],
        )

        # Manual Approval
        if is_feature_branch:
            pipeline.add_stage(
                stage_name="BuildApproval",
                actions=[cpactions.ManualApprovalAction(action_name="ManualApproval")]
            )                           

        # Build and Publish Stage
        pipeline.add_stage(
            stage_name="BuildAndPublishImage",
            actions=[
                cpactions.CodeBuildAction(
                    action_name="BuildAndPublish",
                    project=build_project,
                    input=source_artifact,
                    extra_inputs=[react_app_build_artifact],
                )
            ],
        )

        pipeline.add_stage(
            stage_name="DeployApproval",
            actions=[
                cpactions.ManualApprovalAction(action_name="ManualApproval"),
            ],
        )

        # Deploy Stage   
        pipeline.add_stage(
            stage_name="Deploy",
            actions=[
                cpactions.CodeBuildAction(
                    action_name="CDKDeploy",
                    project=cdk_deploy_project,
                    input=source_artifact,
                    environment_variables=git_branch_env
                )
            ],
        )
