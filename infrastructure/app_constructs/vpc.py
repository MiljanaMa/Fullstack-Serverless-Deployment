from aws_cdk import aws_ec2 as ec2
from constructs import Construct
from config.app_config import AppConfig

# CIDR

class VPCStack(Construct):

    def __init__(self, scope: Construct, id: str, config: AppConfig, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.my_vpc = ec2.CfnVPC(self, f"MY_VPC-{config.environment}",
                            cidr_block=config.vpc_cidr_block,
                            enable_dns_hostnames=True,
                            enable_dns_support=True)
        
        internet_gateway = ec2.CfnInternetGateway(self, f"INTERNET_GATEWAY-{config.environment}")

        ec2.CfnVPCGatewayAttachment(self, f"IGW_ATTACHMENT-{config.environment}",
                                    vpc_id=self.my_vpc.attr_vpc_id,
                                    internet_gateway_id=internet_gateway.attr_internet_gateway_id)

        self.availability_zones = [config.vpc_az1, config.vpc_az2]
        nat_elastic_ip = ec2.CfnEIP(self, f"NAT_EIP-{config.environment}")
        self.private_subnet_list = []
        self.public_subnet_list = []

        public_network_ACL = ec2.CfnNetworkAcl(self, f"PUBLIC_SUBNET_NETWORK_ACL-{config.environment}",
                                               vpc_id=self.my_vpc.attr_vpc_id)
        
        # Inbound rule for public NACL - Allowing traffic from HTTPS
        ec2.CfnNetworkAclEntry(self, f"PUBLIC_NACL_INBOUND_HTTPS-{config.environment}",
                               network_acl_id=public_network_ACL.attr_id,
                               protocol=6,
                               rule_action='allow',
                               rule_number=100,
                               egress=False,
                               cidr_block='0.0.0.0/0',
                               port_range={'from': 443, 'to':443})
        
        # Inbound rule for public NACL - Allowing traffic from HTTP
        ec2.CfnNetworkAclEntry(self, f"PUBLIC_NACL_INBOUND_HTTP-{config.environment}",
                               network_acl_id=public_network_ACL.attr_id,
                               protocol=6,
                               rule_action='allow',
                               rule_number=99,
                               egress=False,
                               cidr_block='0.0.0.0/0',
                               port_range={'from': 80, 'to':80})
        
        # Inbound rule for public NACL - Allowing ephemeral port return traffic (for NAT responses)
        ec2.CfnNetworkAclEntry(self, f"PUBLIC_NACL_INBOUND_EPHERAL_PORTS-{config.environment}",
                               network_acl_id=public_network_ACL.attr_id,
                               protocol=6,
                               rule_action='allow',
                               rule_number=110,
                               egress=False,
                               cidr_block='0.0.0.0/0',
                               port_range={'from': 1024, 'to': 65535})
        
        # Outbound rule for public NACL - Allowing all outbound traffic
        ec2.CfnNetworkAclEntry(self, f"PUBLIC_NACL_OUTBOUND-{config.environment}",
                               network_acl_id=public_network_ACL.attr_id,
                               rule_number=101,
                               protocol=-1,
                               rule_action='allow',
                               egress=True,
                               port_range={'from': 0, 'to': 65535},
                               cidr_block='0.0.0.0/0')
        
        private_network_ACL = ec2.CfnNetworkAcl(self, f"PRIVATE_SUBNET_NETWORK_ACL-{config.environment}",
                                                vpc_id=self.my_vpc.attr_vpc_id)
        
        # Inbound rule for private NACL - Allowing traffic from HTTPS
        ec2.CfnNetworkAclEntry(self, f"PRIVATE_NACL_INBOUND_HTTPS-{config.environment}",
                               network_acl_id=private_network_ACL.attr_id,
                               rule_number=102,
                               rule_action='allow',
                               protocol=6,
                               egress=False,
                               cidr_block='0.0.0.0/0',
                               port_range={'from':443, 'to':443})
    
        # Inbound rule for private NACL - Allowing traffic from HTTP
        ec2.CfnNetworkAclEntry(self, f"PRIVATE_NACL_INBOUND_HTTP-{config.environment}",
                                network_acl_id=private_network_ACL.attr_id,
                                rule_number=106,
                                rule_action='allow',
                                protocol=6,
                                egress=False,
                                cidr_block='0.0.0.0/0',
                                port_range={'from':80, 'to':80})
        
        # Inbound rule for private NACL - Allowing traffic from EPHEMERAL ports
        ec2.CfnNetworkAclEntry(self, f"PRIVATE_NACL_INBONUD_EPHERAL_PORTS-{config.environment}", 
                               network_acl_id=private_network_ACL.attr_id,
                               rule_number=103,
                               rule_action='allow',
                               protocol=6,
                               egress=False,
                               cidr_block='0.0.0.0/0',
                               port_range={'from':1024, 'to':65535})
        
        # Outbound rule for private NACL - Allowing ALL outbound traffic
        ec2.CfnNetworkAclEntry(self, f"PRIVATE_NACL_OUTBOUND_VPC-{config.environment}",
                               network_acl_id=private_network_ACL.attr_id,
                               rule_number=110,
                               protocol=-1,
                               rule_action='allow',
                               egress=True,
                               port_range={'from':0, 'to':65535},
                               cidr_block='0.0.0.0/0'
                               )
    
        for i in range(2):
            # PUBLIC SUBNETS
            public_subnet = ec2.CfnSubnet(self, f"PUBLIC_SUBNET{i+1}-{config.environment}",
                                          vpc_id=self.my_vpc.ref,
                                          cidr_block=f"10.0.{i}.0/24",
                                          availability_zone=self.availability_zones[i],
                                          map_public_ip_on_launch=True)
            
            self.public_subnet_list.append(public_subnet)

            public_rt = ec2.CfnRouteTable(self, f"PUBLIC_RT{i+1}-{config.environment}",
                                          vpc_id=self.my_vpc.ref)

            ec2.CfnSubnetRouteTableAssociation(self, f"PUBLIC_ASN{i+1}-{config.environment}",
                                              subnet_id=public_subnet.ref,
                                              route_table_id=public_rt.ref)

            ec2.CfnRoute(self, f"PUBLIC_ROUTE{i+1}-{config.environment}",
                         route_table_id=public_rt.ref,
                         destination_cidr_block="0.0.0.0/0",
                         gateway_id=internet_gateway.ref)
            
            ec2.CfnSubnetNetworkAclAssociation(self, f'PUBLIC_SUBNET_NACL_ASCN{i+1}-{config.environment}',
                                               subnet_id=public_subnet.attr_subnet_id,
                                               network_acl_id=public_network_ACL.attr_id)

        # 5. NAT Gateway (in first public subnet)
        nat_gateway = ec2.CfnNatGateway(self, f"NAT_GATEWAY-{config.environment}",
                                        allocation_id=nat_elastic_ip.attr_allocation_id,
                                        subnet_id=self.public_subnet_list[0].ref)

        for i in range(2):
            # PRIVATE SUBNETS
            private_subnet = ec2.CfnSubnet(self, f"PRIVATE_SUBNET{i+1}-{config.environment}",
                                           vpc_id=self.my_vpc.ref,
                                           cidr_block=f"10.0.{i+2}.0/24",
                                           availability_zone=self.availability_zones[i],
                                           map_public_ip_on_launch=False)
            
            self.private_subnet_list.append(private_subnet)

            private_rt = ec2.CfnRouteTable(self, f"PRIVATE_RT{i+1}-{config.environment}",
                                           vpc_id=self.my_vpc.ref)

            ec2.CfnSubnetRouteTableAssociation(self, f"PRIVATE_ASN{i+1}-{config.environment}",
                                               subnet_id=private_subnet.ref,
                                               route_table_id=private_rt.ref)

            ec2.CfnRoute(self, f"PRIVATE_ROUTE{i+1}-{config.environment}",
                         route_table_id=private_rt.ref,
                         destination_cidr_block="0.0.0.0/0",
                         nat_gateway_id=nat_gateway.ref)
            
            ec2.CfnSubnetNetworkAclAssociation(self, f'PRIVATE_SUBNET_NACL_ACSN{i+1}-{config.environment}',
                                               subnet_id=private_subnet.attr_subnet_id,
                                               network_acl_id=private_network_ACL.attr_id)        