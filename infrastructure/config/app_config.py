import os

class AppConfig:
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT")
        self.region = os.getenv("REGION")
        self.table_name = os.getenv("TABLE_NAME")
        self.account_id = os.getenv("ACCOUNT_ID")
        self.hosted_zone_id = os.getenv("HOSTED_ZONE_ID")
        self.domain_name = os.getenv("DOMAIN_NAME")
        self.frontend_docker_image = os.getenv("FRONTEND_DOCKER_IMAGE")
        self.app_name = os.getenv("APP_NAME")
        self.full_table_name = f"{self.table_name}-{self.environment}"
        self.ecs_memory_limit = int(os.getenv("ECS_MEMORY_LIMIT"))
        self.ecs_cpu_limit = int(os.getenv("ECS_CPU_LIMIT"))
        self.api_url_env = os.getenv("API_URL_ENV")
        self.user_pool_id_env = os.getenv("USER_POOL_ID_ENV")
        self.app_client_id_env = os.getenv("APP_CLIENT_ID_ENV")
        self.ecr_repository_arn = f"arn:aws:ecr:{self.region}:{self.account_id}:repository/{self.frontend_docker_image}"
        self.ssl_certificate_id = os.getenv("SSL_CERTIFICATE_ID")
        self.website_subdomain = os.getenv("WEBSITE_SUBDOMAIN")
        self.docker_image_tag = os.getenv("DOCKER_IMAGE_TAG")
        self.certificate_arn = f"arn:aws:acm:{self.region}:{self.account_id}:certificate/{self.ssl_certificate_id}"
        self.table_arn = f"arn:aws:dynamodb:{self.region}:{self.account_id}:table/{self.full_table_name}"
        self.vpc_cidr_block = os.getenv("VPC_CIDR_BLOCK")
        self.vpc_az1 = os.getenv("AVAILABILITY_ZONE_1")
        self.vpc_az2 = os.getenv("AVAILABILITY_ZONE_2")
        self.team_name = os.getenv("TEAM_NAME")
        self.managed_by = os.getenv("MANAGED_BY")
        self.stack_name = os.getenv("STACK_NAME")
        self.levi9_network = os.getenv('LEVI9_GUEST_NETWORK')
