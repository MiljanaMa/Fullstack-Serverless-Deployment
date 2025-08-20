from aws_cdk import (
    aws_ecs as ecs,
    aws_iam as iam,
    aws_ecr as ecr,
    aws_logs as logs,
    RemovalPolicy,
    Duration
)
from constructs import Construct
from config.app_config import AppConfig
from aws_cdk.aws_ecs import DeploymentCircuitBreaker

class Fargate(Construct):
    def __init__(self, service_name, stack, vpc, subnets,
                 security_group, api_url, user_pool_id, app_client_id,
                 config: AppConfig):
        super().__init__(stack, f"{service_name}_id-{config.environment}-{config.app_name}")
        self._config = config
        self.stack = stack
        self.service_name = service_name
        self.ecs_cluster = self._generate_ecs_cluster(stack, service_name, vpc)
        execution_role = self._generate_execution_role(stack, service_name)
        task_definition = self._generate_task_definition(stack, service_name, execution_role)
        
        container_name = f"{service_name}_container-{self._config.environment}-{self._config.app_name}"
        ecr_repository = ecr.Repository.from_repository_name(
            stack, 
            f"{service_name}_frontend_repository-{self._config.environment}-{self._config.app_name}",
            repository_name=self._config.frontend_docker_image,
        )
        log_group = logs.LogGroup(self, f"{service_name}_log_group-{self._config.environment}-{self._config.app_name}",
            log_group_name=f"{service_name}_log_group-{self._config.environment}-{self._config.app_name}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )
        log_driver = ecs.LogDriver.aws_logs(
            stream_prefix=f"{self._config.app_name}",
            log_group=log_group
        )
        container = task_definition.add_container(container_name,
                                                logging=log_driver,
                                                image=ecs.ContainerImage.from_ecr_repository(ecr_repository, tag=self._config.docker_image_tag),
                                                environment={
                                                    self._config.api_url_env:api_url,
                                                    self._config.user_pool_id_env:user_pool_id,
                                                    self._config.app_client_id_env:app_client_id
                                                })

        # Define the port mapping
        container.add_port_mappings(
            ecs.PortMapping(container_port=80, host_port=80, protocol=ecs.Protocol.TCP)
        )

        self.service = ecs.FargateService(stack, service_name,
                                cluster=self.ecs_cluster,
                                task_definition=task_definition,
                                security_groups=[security_group],
                                desired_count=2,
                                vpc_subnets=subnets,
                                circuit_breaker=DeploymentCircuitBreaker(
                                    rollback=True,
                                    enable=True
                                ))
        
        scaling = self.service.auto_scale_task_count(
            min_capacity=1,
            max_capacity=3
        )

        scaling.scale_on_cpu_utilization("CpuScaling",
            target_utilization_percent=70,
            scale_in_cooldown=Duration.seconds(60),
            scale_out_cooldown=Duration.seconds(60)
        )

    def _generate_ecs_cluster(self, stack, service_name, vpc):
        ecs_cluster_name = f"{service_name}_ecs_cluster-{self._config.environment}-{self._config.app_name}"
        ecs_cluster = ecs.Cluster(stack, ecs_cluster_name, vpc=vpc)
        return ecs_cluster

    def _generate_task_definition(self, stack, service_name, execution_role):
        task_definition_name = f"{service_name}_task_definition-{self._config.environment}-{self._config.app_name}"
        task_definition = ecs.FargateTaskDefinition(stack,
                                                    task_definition_name,
                                                    execution_role=execution_role,
                                                    memory_limit_mib=self._config.ecs_memory_limit, cpu=self._config.ecs_cpu_limit)  
        return task_definition     

    def _generate_execution_role(self, stack, service_name):
        ecs_execution_role_name = f"{service_name}_execution_role-{self._config.environment}-{self._config.app_name}"
        execution_role = iam.Role(stack, ecs_execution_role_name, assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"), role_name=ecs_execution_role_name)
        execution_role.add_to_policy(iam.PolicyStatement( effect=iam.Effect.ALLOW, resources=[self._config.ecr_repository_arn], actions=["ecr:GetAuthorizationToken", "ecr:BatchCheckLayerAvailability", "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage", "logs:CreateLogStream", "logs:PutLogEvents"] ))
        return execution_role