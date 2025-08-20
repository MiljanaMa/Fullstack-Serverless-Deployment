from aws_cdk import (
    aws_wafv2 as wafv2,
    aws_elasticloadbalancingv2 as elbv2
)

from constructs import Construct
from config.app_config import AppConfig

class WAF(Construct):

    def __init__(self, scope: Construct, id: str,  alb_arn, config: AppConfig, **kwargs):
        super().__init__(scope, id, **kwargs)
        #Test
        # Levi9 GuestWifi Cidr Block
        ip_set = wafv2.CfnIPSet(self, f"Levi9IpSet-{config.environment}",         
                                addresses=[config.levi9_network],
                                ip_address_version='IPV4',
                                scope='REGIONAL',
                                name=f"Levi9GuestWifiAllowedIPs-{config.environment}")

        web_acl = wafv2.CfnWebACL(self, f"MyWebACL-{config.environment}",
                                 default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
                                 scope='REGIONAL',
                                 visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                                     cloud_watch_metrics_enabled=True,
                                     metric_name=f"MyWebACL-{config.environment}",
                                     sampled_requests_enabled=True 
                                 ),
                                 rules=[
                                     wafv2.CfnWebACL.RuleProperty(
                                        name=f"BlockNonLevi9Signup-{config.environment}",       
                                        priority=0,
                                        action=wafv2.CfnWebACL.RuleActionProperty(block={}),    # Block access if not from Levi9Guest Network
                                        visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                                            sampled_requests_enabled=True,
                                            cloud_watch_metrics_enabled=True,
                                            metric_name=f"BlockNonLevi9Signup-{config.environment}"
                                        ),
                                        statement=wafv2.CfnWebACL.StatementProperty(
                                            and_statement=wafv2.CfnWebACL.AndStatementProperty(
                                                statements=[
                                                    wafv2.CfnWebACL.StatementProperty(
                                                        byte_match_statement=wafv2.CfnWebACL.ByteMatchStatementProperty(
                                                            field_to_match=wafv2.CfnWebACL.FieldToMatchProperty(
                                                                uri_path={}
                                                            ),
                                                            positional_constraint='STARTS_WITH',
                                                            search_string='/signup',
                                                            text_transformations=[
                                                                wafv2.CfnWebACL.TextTransformationProperty(
                                                                    priority=0,
                                                                    type='NONE'
                                                                )
                                                            ]
                                                        )
                                                    ),
                                                    wafv2.CfnWebACL.StatementProperty(
                                                        not_statement=wafv2.CfnWebACL.NotStatementProperty(
                                                            statement=wafv2.CfnWebACL.StatementProperty(
                                                                ip_set_reference_statement=wafv2.CfnWebACL.IPSetReferenceStatementProperty(
                                                                    arn=ip_set.attr_arn
                                                                )
                                                            )
                                                        )
                                                    )
                                                ]
                                            )
                                        )
                                     )
                                 ])
        
        wafv2.CfnWebACLAssociation(self, f"WebACLAssociation-{config.environment}", 
                                   resource_arn=alb_arn,
                                   web_acl_arn=web_acl.attr_arn)