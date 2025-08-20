from aws_cdk import (
    aws_elasticloadbalancingv2 as elbv2,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as targets
)
from constructs import Construct
from config.app_config import AppConfig

class ALB(Construct):
    def __init__(self, service_name, stack, vpc, ecs, security_group,
                 config:AppConfig):
        super().__init__(stack, f"{service_name}_id-{config.environment}-{config.app_name}")
        self._config = config
        load_balancer_name = f"{service_name}-{config.environment}-{config.app_name}"
        self.load_balancer = elbv2.ApplicationLoadBalancer(stack, load_balancer_name,
                                                     vpc=vpc,
                                                     security_group=security_group,
                                                     internet_facing=True)
        
        listener_name = f"{service_name}_listener-{config.environment}-{config.app_name}"
        listener = self.load_balancer.add_listener(listener_name, protocol=elbv2.ApplicationProtocol.HTTPS, port=443)

        certificate_arn = self._config.certificate_arn
        certificate = acm.Certificate.from_certificate_arn(stack, "ImportedCertificate", certificate_arn)
        listener.add_certificates(f"{service_name}_certificate-{config.environment}-{config.app_name}", [certificate])
        ecs_target_name = f"{service_name}_ecs_target-{config.environment}-{config.app_name}"
        listener.add_targets(ecs_target_name, port=80, protocol=elbv2.ApplicationProtocol.HTTP, targets=[ecs])

        self.load_balancer.add_listener(f"{service_name}_redirect-listener-{config.environment}-{config.app_name}",
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            default_action=elbv2.ListenerAction.redirect(
                protocol="HTTPS",
                port="443",
                permanent=True
            )
        )
        
        hosted_zone = route53.HostedZone.from_lookup(
            stack, f"{service_name}_hosted-zone-{config.environment}-{config.app_name}",
            domain_name=self._config.domain_name
        )

        route53.ARecord(
            stack, f"{service_name}_dns-record-{config.environment}-{config.app_name}",
            zone=hosted_zone,
            record_name= f"{self._config.website_subdomain}.{self._config.domain_name}",
            target=route53.RecordTarget.from_alias(targets.LoadBalancerTarget(self.load_balancer)),
        )
        self.ALB_arn = self.load_balancer.load_balancer_arn
