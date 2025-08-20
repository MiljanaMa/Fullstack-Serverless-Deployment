from aws_cdk import (
    aws_apigateway as apigateway,
    aws_cognito as cognito,
    aws_logs as logs,
    aws_cloudwatch as cw,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    Duration,
    CfnOutput,
    RemovalPolicy

)
import aws_cdk.aws_cloudwatch_actions as cw_actions
from constructs import Construct
from config.app_config import AppConfig

from .lambda_module import LambdaModule


class APIGateway(Construct):
    def __init__(self, scope: Construct, api_id: str, api_name: str, cognito_name: str, auth_name: str,
                 config: AppConfig, lambdaFn: LambdaModule):
        super().__init__(scope, api_id)
        #self.dashboard = dashboard
        self.api_name = api_name
        
        self.sns_topic = sns.Topic(
            self, f"APIGatewayAlarmNotificationTopic-{config.environment}",
            display_name="API Gateway Alarm Notification Topic"
        )
        self.sns_topic.add_subscription(
            subscriptions.EmailSubscription("miljana.marjanovic9@gmail.com")
        )

        self.user_pool = cognito.UserPool(self, f"{config.environment}-UserPool",
            user_pool_name=f"{cognito_name}-User-Pool-{config.environment}",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_uppercase=True,
                require_lowercase=True,
                require_digits=True,
                require_symbols=False
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY
        )
        self.user_pool.apply_removal_policy(RemovalPolicy.DESTROY)

        self.user_pool_client = self.user_pool.add_client(f"{config.environment}-UserPoolClient",
            user_pool_client_name=f"{cognito_name}-Client-{config.environment}",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True
            ),
            prevent_user_existence_errors=True,
            generate_secret=False
        )

        self.user_pool_client.apply_removal_policy(RemovalPolicy.DESTROY)
        
        #Log group
        self.log_group = logs.LogGroup(self, f"{api_id}_log_group-{config.environment}-{config.app_name}",
            log_group_name=f"{api_id}_log_group-{config.environment}-{config.app_name}",
            retention=logs.RetentionDays.ONE_WEEK
        )
        self.log_group.apply_removal_policy(RemovalPolicy.DESTROY)

        self.rest_api = apigateway.RestApi(self, f"{config.environment}-API",
            rest_api_name=f"{api_name}-{config.environment}",
            description="This service manages goals",
            cloud_watch_role=True,
            deploy_options=apigateway.StageOptions(
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                access_log_destination=apigateway.LogGroupLogDestination(self.log_group),
                access_log_format=apigateway.AccessLogFormat.json_with_standard_fields(
                    caller=True,
                    http_method=True,
                    ip=True,
                    protocol=True,
                    request_time=True,
                    resource_path=True,
                    response_length=True,
                    status=True,
                    user=True
                )
            )
        )
        
        authorizer = apigateway.CognitoUserPoolsAuthorizer(self, f"{config.environment}-Authorizer",
            cognito_user_pools=[self.user_pool],
            authorizer_name=f"{auth_name}-{config.environment}",
            identity_source="method.request.header.Authorization"
        )  

        goals_resource = self.rest_api.root.add_resource("goals", 
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=["OPTIONS", "GET", "POST"],
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "X-Amz-Security-Token"],
                allow_credentials=True
            )
        )       
        
        goal_id_resource = goals_resource.add_resource("{id}",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=["OPTIONS", "GET", "PUT", "DELETE"],
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "X-Amz-Security-Token"],
                allow_credentials=True
            ))


        goals_resource.add_method("POST",
            apigateway.LambdaIntegration(lambdaFn.lambdas["CreateGoal"]),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=authorizer,
            method_responses=[
                apigateway.MethodResponse(status_code="200"),
                apigateway.MethodResponse(status_code="500")
            ]
        )

        # GET /goals
        goals_resource.add_method("GET",
            apigateway.LambdaIntegration(lambdaFn.lambdas["GetAllGoals"]),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=authorizer
        )

        # GET /goals/{ID}
        goal_id_resource.add_method("GET",
            apigateway.LambdaIntegration(lambdaFn.lambdas["GetGoal"]),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=authorizer
        )

        # PUT /goals/{ID}
        goal_id_resource.add_method("PUT",
            apigateway.LambdaIntegration(lambdaFn.lambdas["UpdateGoal"]),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=authorizer
        )

         # DELETE /goals/{ID}
        goal_id_resource.add_method("DELETE",
            apigateway.LambdaIntegration(lambdaFn.lambdas["DeleteGoal"]),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=authorizer
        )

       # Outputs
        CfnOutput(self, "APIGatewayURL",
            value=self.rest_api.url_for_path(f"/goals").replace("//", "/").replace("https:/", "https://"),
            description="API Gateway Invoke URL"
        )
        CfnOutput(self, "CognitoUserPoolId",
            value=self.user_pool.user_pool_id,
            description="Cognito User Pool ID"
        )
        CfnOutput(self, "CognitoUserPoolClientId",
            value=self.user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID"
        )