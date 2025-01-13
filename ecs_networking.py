import boto3
from datetime import datetime

def log_networking_with_timestamp(region="sa-east-1", log_file="network_log.txt"):
    ecs_client = boto3.client('ecs', region_name=region)
    ec2_client = boto3.client('ec2', region_name=region)
    clusters = ecs_client.list_clusters()['clusterArns']

    with open(log_file, "w") as log:
        for cluster in clusters:
            services = ecs_client.list_services(cluster=cluster)['serviceArns']
            for service in services:
                service_details = ecs_client.describe_services(cluster=cluster, services=[service])['services'][0]
                vpc_config = service_details.get('networkConfiguration', {}).get('awsvpcConfiguration', {})
                subnets = vpc_config.get('subnets', [])
                security_groups = vpc_config.get('securityGroups', [])

                # Fetch VPC ID from subnet
                vpc_id = None
                if subnets:
                    subnet_details = ec2_client.describe_subnets(SubnetIds=subnets)
                    vpc_id = subnet_details['Subnets'][0]['VpcId'] if subnet_details['Subnets'] else None

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log.write(f"Timestamp: {timestamp}\n")
                log.write(f"Cluster: {cluster}\n")
                log.write(f"Service: {service}\n")
                log.write(f"VPC: {vpc_id}\n")
                log.write(f"Subnets: {subnets}\n")
                log.write(f"Security Groups: {security_groups}\n")
                log.write("-" * 40 + "\n")


def update_networking(region="sa-east-1", main_config=None, shared_config=None, public_config=None):
    ecs_client = boto3.client('ecs', region_name=region)
    ec2_client = boto3.client('ec2', region_name=region)
    clusters = ecs_client.list_clusters()['clusterArns']

    for cluster in clusters:
        services = ecs_client.list_services(cluster=cluster)['serviceArns']
        for service in services:
            service_details = ecs_client.describe_services(cluster=cluster, services=[service])['services'][0]
            vpc_config = service_details.get('networkConfiguration', {}).get('awsvpcConfiguration', {})
            subnets = vpc_config.get('subnets', [])

            # Fetch VPC ID from subnet
            vpc_id = None
            if subnets:
                subnet_details = ec2_client.describe_subnets(SubnetIds=subnets)
                vpc_id = subnet_details['Subnets'][0]['VpcId'] if subnet_details['Subnets'] else None

            if vpc_id:
                if "main" in vpc_id and main_config:
                    new_subnets = main_config.get('subnets', [])
                    new_security_groups = main_config.get('securityGroups', [])
                elif "shared" in vpc_id and shared_config:
                    new_subnets = shared_config.get('subnets', [])
                    new_security_groups = shared_config.get('securityGroups', [])
                elif "public" in vpc_id and public_config:
                    new_subnets = public_config.get('subnets', [])
                    new_security_groups = public_config.get('securityGroups', [])
                else:
                    continue

                ecs_client.update_service(
                    cluster=cluster,
                    service=service,
                    networkConfiguration={
                        'awsvpcConfiguration': {
                            'subnets': list(set(new_subnets)),  # Avoid duplicates
                            'securityGroups': list(set(new_security_groups)),
                            'assignPublicIp': vpc_config.get('assignPublicIp', 'DISABLED'),
                        }
                    }
                )

if __name__ == "__main__":
    # Log networking details with timestamp to a file
    log_networking_with_timestamp()

    # Update networking configuration
    update_networking(
        main_config={"subnets": ["subnet-main"], "securityGroups": ["sg-main"]},
        shared_config={"subnets": ["subnet-shared"], "securityGroups": ["sg-shared"]},
        public_config={"subnets": ["subnet-public"], "securityGroups": ["sg-public"]}
    )
