from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_cloudwatch as cloudwatch
)

from constructs import Construct

from app_constructs.vpc import VPCStack
from app_constructs.api_gateway import APIGateway
from app_constructs.alb import ALB
from app_constructs.fargate import Fargate
from app_constructs.dynamo_db import DynamoDB
from app_constructs.lambda_module import LambdaModule
from app_constructs.WAF import WAF
from app_constructs.monitoring import Monitoring
from stacks.core import TaggedStack

from config.app_config import AppConfig



class MainStack(TaggedStack):

    def __init__(self, scope: Construct, construct_id: str, config: AppConfig, **kwargs) -> None:
        super().__init__(scope, construct_id, config=config, **kwargs)

        self.dynamo = DynamoDB(self, f"DYNAMO_DB-{config.environment}", config=config)
        
        self.lambda_module = LambdaModule(self, f"LAMBDA-{config.environment}", config=config)

        self.api_gateway = APIGateway(self, api_id=f"API_GATEWAY-{config.environment}", api_name="ApiGoal", cognito_name="CognitoGoal", auth_name="GoalAuthorizer",
                                      config=config, lambdaFn=self.lambda_module)

        vpcL1 = VPCStack(self, "MY_VPC", config=config)
        vpcL2 = ec2.Vpc.from_vpc_attributes(self, "MY_VPC_L2" + config.environment,
                                            vpc_id=vpcL1.my_vpc.ref,
                                            availability_zones=vpcL1.availability_zones,
                                            private_subnet_ids=[subnet.ref for subnet in vpcL1.private_subnet_list],
                                            public_subnet_ids=[subnet.ref for subnet in vpcL1.public_subnet_list]
                                          )
        
        subnet_selection = ec2.SubnetSelection(
        subnets=[
            ec2.Subnet.from_subnet_id(self, f"PrivateSubnet{i+1}Ref{config.environment}", subnet.ref)
            for i, subnet in enumerate(vpcL1.private_subnet_list)
        ])


        fargate_security_group = ec2.SecurityGroup(self, "FARGATE_SEC_GROUP" + config.environment,
                                   vpc=vpcL2,
                                   description="Allow traffic to Fargate service",
                                   allow_all_outbound=True)
        fargate_security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP")

        alb_security_group = ec2.SecurityGroup(self, "ALB_SEC_GROUP" + config.environment,
                                   vpc=vpcL2,
                                   description="Allow traffic to ALB service",
                                   allow_all_outbound=True)
        alb_security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP")
        alb_security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "Allow HTTPS")

        fargate = Fargate(f"FARGATE_FRONTEND-{config.environment}",
                                         self,
                                         vpcL2,
                                         subnet_selection,
                                         fargate_security_group,
                                         self.api_gateway.rest_api.url[:-1],
                                         self.api_gateway.user_pool.user_pool_id,
                                         self.api_gateway.user_pool_client.user_pool_client_id,
                                         config
                                        )
        alb = ALB("FARGATE_ALB", self, vpcL2, fargate.service, alb_security_group, config)
        
        alb_arn = alb.ALB_arn
        waf = WAF(self, f"WafLevi9-{config.environment}", alb_arn, config=config)
        self.monitoring = Monitoring(
                                            self, f"Monitoring{config.environment}",
                                            config=config,
                                            lambda_module=self.lambda_module,
                                            dynamodb=self.dynamo,
                                            api_gateway=self.api_gateway,
                                            fargate=fargate,
                                            alb=alb
                                        )

