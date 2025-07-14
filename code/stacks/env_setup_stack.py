from aws_cdk import (
    Fn,
    Stack,
    CfnParameter,
    aws_ec2 as ec2,
    CfnOutput
)

from constructs import Construct

class EnvSetupStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # === Parameters ===
        az = CfnParameter(self, "AvailabilityZone", type="String")
        cidr_disk_monitor = CfnParameter(self, "CIDRDiskMonitorVPC", type="String")
        cidr_rocketchat = CfnParameter(self, "CIDRRocketChatVPC", type="String")
        cidr_lambda = CfnParameter(self, "CIDRLambdaVPC", type="String")
        prefix_list_id = CfnParameter(self, "FacilityPrefixListId", type="String")

        # === VPCs ===
        disk_vpc = ec2.CfnVPC(self, "DiskMonitorVPC",
            cidr_block=cidr_disk_monitor.value_as_string,
            enable_dns_support=True,
            enable_dns_hostnames=True,
            tags=[{"key": "Name", "value": "DiskMonitorVPC"}]
        )

        rocketchat_vpc = ec2.CfnVPC(self, "RocketChatVPC",
            cidr_block=cidr_rocketchat.value_as_string,
            enable_dns_support=True,
            enable_dns_hostnames=True,
            tags=[{"key": "Name", "value": "RocketChatVPC"}]
        )

        lambda_vpc = ec2.CfnVPC(self, "LambdaVPC",
            cidr_block=cidr_lambda.value_as_string,
            enable_dns_support=True,
            enable_dns_hostnames=True,
            tags=[{"key": "Name", "value": "LambdaVPC"}]
        )

        # === Subnets ===
        disk_subnet = ec2.CfnSubnet(self, "DiskMonitorSubnet",
            vpc_id=disk_vpc.ref,
            cidr_block="10.10.0.0/28",
            availability_zone=az.value_as_string,
            map_public_ip_on_launch=True,
            tags=[{"key": "Name", "value": "DiskMonitorSubnet"}]
        )

        rocketchat_subnet = ec2.CfnSubnet(self, "RocketChatSubnet",
            vpc_id=rocketchat_vpc.ref,
            cidr_block="10.20.0.0/28",
            availability_zone=az.value_as_string,
            map_public_ip_on_launch=True,
            tags=[{"key": "Name", "value": "RocketChatSubnet"}]
        )

        lambda_pub_subnet = ec2.CfnSubnet(self, "LambdaPublicSubnet",
            vpc_id=lambda_vpc.ref,
            cidr_block="10.0.0.0/28",
            availability_zone=az.value_as_string,
            map_public_ip_on_launch=True,
            tags=[{"key": "Name", "value": "LambdaPublicSubnet"}]
        )

        lambda_priv_subnet = ec2.CfnSubnet(self, "LambdaPrivateSubnet",
            vpc_id=lambda_vpc.ref,
            cidr_block="10.0.0.16/28",
            availability_zone=az.value_as_string,
            map_public_ip_on_launch=False,
            tags=[{"key": "Name", "value": "LambdaPrivateSubnet"}]
        )

        # === IGWs and Attachments ===
        disk_igw = ec2.CfnInternetGateway(self, "DiskMonitorIGW")
        ec2.CfnVPCGatewayAttachment(self, "AttachDiskIGW",
            vpc_id=disk_vpc.ref,
            internet_gateway_id=disk_igw.ref
        )

        rocketchat_igw = ec2.CfnInternetGateway(self, "RocketChatIGW")
        ec2.CfnVPCGatewayAttachment(self, "AttachRCIGW",
            vpc_id=rocketchat_vpc.ref,
            internet_gateway_id=rocketchat_igw.ref
        )

        lambda_igw = ec2.CfnInternetGateway(self, "LambdaIGW")
        ec2.CfnVPCGatewayAttachment(self, "AttachLambdaIGW",
            vpc_id=lambda_vpc.ref,
            internet_gateway_id=lambda_igw.ref
        )

        # === Elastic IPs ===
        lambda_nat_eip = ec2.CfnEIP(self, "LambdaNatEIP", domain="vpc")
        rc_eip = ec2.CfnEIP(self, "RocketChatEIP", domain="vpc")

        # === NAT Gateway ===
        nat_gateway = ec2.CfnNatGateway(self, "LambdaNAT",
            allocation_id=lambda_nat_eip.attr_allocation_id,
            subnet_id=lambda_pub_subnet.ref
        )

        # === Route Tables ===
        lambda_pub_rt = ec2.CfnRouteTable(self, "LambdaPublicRT", vpc_id=lambda_vpc.ref)
        lambda_priv_rt = ec2.CfnRouteTable(self, "LambdaPrivateRT", vpc_id=lambda_vpc.ref)
        disk_rt = ec2.CfnRouteTable(self, "DiskMonitorRT", vpc_id=disk_vpc.ref)
        rc_rt = ec2.CfnRouteTable(self, "RocketChatRT", vpc_id=rocketchat_vpc.ref)

        # === Routes ===
        ec2.CfnRoute(self, "LambdaPubRoute",
            route_table_id=lambda_pub_rt.ref,
            destination_cidr_block="0.0.0.0/0",
            gateway_id=lambda_igw.ref
        )

        ec2.CfnRoute(self, "LambdaPrivRoute",
            route_table_id=lambda_priv_rt.ref,
            destination_cidr_block="0.0.0.0/0",
            nat_gateway_id=nat_gateway.ref
        )

        ec2.CfnRoute(self, "DiskRoute",
            route_table_id=disk_rt.ref,
            destination_cidr_block="0.0.0.0/0",
            gateway_id=disk_igw.ref
        )

        ec2.CfnRoute(self, "RocketRoute",
            route_table_id=rc_rt.ref,
            destination_cidr_block="0.0.0.0/0",
            gateway_id=rocketchat_igw.ref
        )

        # === Subnet Associations ===
        ec2.CfnSubnetRouteTableAssociation(self, "AssocLambdaPub", subnet_id=lambda_pub_subnet.ref, route_table_id=lambda_pub_rt.ref)
        ec2.CfnSubnetRouteTableAssociation(self, "AssocLambdaPriv", subnet_id=lambda_priv_subnet.ref, route_table_id=lambda_priv_rt.ref)
        ec2.CfnSubnetRouteTableAssociation(self, "AssocDisk", subnet_id=disk_subnet.ref, route_table_id=disk_rt.ref)
        ec2.CfnSubnetRouteTableAssociation(self, "AssocRC", subnet_id=rocketchat_subnet.ref, route_table_id=rc_rt.ref)

        # RocketChatSG
        lambda_nat_cidr = Fn.sub("${PublicIP}/32", {
            "PublicIP": lambda_nat_eip.attr_public_ip
        })

        rocketchat_sg = ec2.CfnSecurityGroup(self, "RocketChatSG",
            group_description="Allow SSH and Rocket.Chat access from facility prefix list and Lambda NAT EIP",
            vpc_id=rocketchat_vpc.ref,
            security_group_ingress=[
                ec2.CfnSecurityGroup.IngressProperty(
                    ip_protocol="tcp",
                    from_port=22,
                    to_port=22,
                    source_prefix_list_id=prefix_list_id.value_as_string
                ),
                ec2.CfnSecurityGroup.IngressProperty(
                    ip_protocol="tcp",
                    from_port=3000,
                    to_port=3000,
                    source_prefix_list_id=prefix_list_id.value_as_string
                ),
                ec2.CfnSecurityGroup.IngressProperty(
                    ip_protocol="tcp",
                    from_port=3000,
                    to_port=3000,
                    cidr_ip=lambda_nat_cidr
                ),
            ],
            tags=[{"key": "Name", "value": "demo-rocketchat-sg"}]
        )

        # DiskMonitorSG
        diskmonitor_sg = ec2.CfnSecurityGroup(self, "DiskMonitorSG",
            group_description="Allow SSH access for disk monitor from facility prefix list",
            vpc_id=disk_vpc.ref,
            security_group_ingress=[
                ec2.CfnSecurityGroup.IngressProperty(
                    ip_protocol="tcp",
                    from_port=22,
                    to_port=22,
                    source_prefix_list_id=prefix_list_id.value_as_string
                )
            ],
            tags=[{"key": "Name", "value": "demo-disk-monitor-sg"}]
        )

        # LambdaSG
        lambda_sg = ec2.CfnSecurityGroup(self, "LambdaSG",
            group_description="Lambda to Rocket.Chat webhook access",
            vpc_id=lambda_vpc.ref,
            security_group_egress=[
                ec2.CfnSecurityGroup.EgressProperty(
                    ip_protocol="-1",
                    cidr_ip="0.0.0.0/0"
                )
            ],
            tags=[{"key": "Name", "value": "demo-lambda-sg"}]
        )

        # Elastic IPs Outputs
        CfnOutput(self, "ROCKETCHAT_EIP", 
            value=rc_eip.ref, 
            description="Elastic IP allocation ID for Rocket.Chat EC2 instance"
        )

        # Subnet Outputs
        CfnOutput(self, "DISK_MONITOR_SUBNET", value=disk_subnet.ref, description="Subnet for Disk Monitor EC2")
        CfnOutput(self, "ROCKETCHAT_SUBNET", value=rocketchat_subnet.ref, description="Subnet for Rocket.Chat EC2")

        # SG Outputs
        CfnOutput(self, "DISK_MONITOR_SG", value=diskmonitor_sg.ref, description="Security Group ID for Disk Monitor")
        CfnOutput(self, "ROCKETCHAT_SG", value=rocketchat_sg.ref, description="Security Group ID for Rocket.Chat")
        CfnOutput(self, "LAMBDA_SG", value=lambda_sg.ref, description="Security Group ID for Lambda")
