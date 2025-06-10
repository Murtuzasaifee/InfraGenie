from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from src.infra_genie.utils.components_type import ComponentType

@dataclass
class ComponentContext:
    """Context for each component generation"""
    component_type: ComponentType
    dependencies: List[str]
    outputs_needed: List[str]
    security_level: str
    region: str

class DecomposedTerraformPrompts:
    """Specialized prompts for each infrastructure component with proper dependency handling"""
    
    def __init__(self):
        self.base_context = """
        You are a Terraform expert specializing in AWS infrastructure.
        Generate production-ready, secure Terraform code following AWS best practices.
        
        CRITICAL REQUIREMENTS:
        - Use only valid Terraform 1.5+ syntax
        - All variables must be declared in variables.tf
        - All resources must have proper dependencies
        - Follow AWS Well-Architected Framework principles
        - Include comprehensive error handling
        """

    def format_dependencies(self, dependencies: Dict[str, Any]) -> str:
        """Format available dependencies for inclusion in prompts"""
        if not dependencies:
            return "No dependencies available yet."
        
        formatted = []
        for component, outputs in dependencies.items():
            if outputs:
                formatted.append(f"\n  From {component} module:")
                for key, value in outputs.items():
                    formatted.append(f"    - {key}: module.{component}.{key}")
        
        return "".join(formatted) if formatted else "No dependencies available yet."

    def get_dependency_variables(self, dependencies: Dict[str, Any]) -> str:
        """Generate variable declarations for dependencies"""
        if not dependencies:
            return ""
        
        variables = []
        for component, outputs in dependencies.items():
            if outputs:
                for key, value in outputs.items():
                    variables.append(f"""
                        variable "{component}_{key}" {{
                        description = "{key} from {component} module"
                        type        = string
                        }}""")
        
        return "\n".join(variables)

    def get_networking_prompt(self, user_input: Dict[str, Any], dependencies: Dict[str, Any] = None) -> str:
        """Generate VPC, subnets, routing, and basic networking"""
        
        return f"""
        {self.base_context}
        
        TASK: Generate a networking module for a {user_input['application_type']}
        
        PROJECT CONTEXT:
        - Project: {user_input['project_name']}
        - Description: {user_input['description']}
        - Security Level: {user_input['security_level']}
        
        DEPENDENCIES:
        {self.format_dependencies(dependencies)}
        
        NETWORKING REQUIREMENTS:
        1. Create a VPC with appropriate CIDR (10.0.0.0/16 recommended)
        2. Create subnets across 2 availability zones:
           - Public subnets for load balancers (10.0.1.0/24, 10.0.2.0/24)
           - Private subnets for applications (10.0.10.0/24, 10.0.11.0/24)
           - Database subnets for data tier (10.0.20.0/24, 10.0.21.0/24)
        3. Internet Gateway for public access
        4. NAT Gateways for private subnet internet access
        5. Route tables with proper routing
        6. DB subnet group for RDS
        
        SECURITY CONSIDERATIONS (Enhanced Level):
        - Enable VPC Flow Logs to CloudWatch
        - Create NACLs with restrictive rules
        - Implement proper subnet isolation
        
        REQUIRED OUTPUTS (These will be used by other modules):
        - vpc_id: For security groups and other resources
        - public_subnet_ids: For load balancers
        - private_subnet_ids: For application instances
        - database_subnet_ids: For RDS subnet group
        - db_subnet_group_name: For RDS instances
        - route_table_ids: For additional routing if needed
        
        GENERATE THREE FILES:
        1. main.tf - VPC, subnets, gateways, routing
        2. variables.tf - All input variables with validation
        3. outputs.tf - ALL required outputs listed above
        
        Focus ONLY on networking. Do not include compute, database, or other resources.
        """

    def get_security_groups_prompt(self, user_input: Dict[str, Any], dependencies: Dict[str, Any] = None) -> str:
        """Generate security groups based on application needs"""
        
        networking_deps = dependencies.get('networking', {}) if dependencies else {}
        
        return f"""
        {self.base_context}
        
        TASK: Generate security groups module for {user_input['application_type']}
        
        PROJECT CONTEXT:
        - Project: {user_input['project_name']}
        - Application: {user_input['description']}
        - Security Level: {user_input['security_level']}
        
        
        DEPENDENCY USAGE IN CODE:
        Use these exact references in your Terraform code:
        - VPC ID: var.networking_vpc_id (passed from module.networking.vpc_id)
        
        SECURITY GROUPS NEEDED:
        1. ALB Security Group:
           - Inbound: HTTP (80), HTTPS (443) from 0.0.0.0/0
           - Outbound: All traffic to VPC CIDR
        
        2. Application Security Group:
           - Inbound: HTTP (80), HTTPS (443) from ALB security group
           - Inbound: SSH (22) from bastion/admin CIDR (if needed)
           - Outbound: HTTPS (443) to 0.0.0.0/0 (for API calls)
           - Outbound: Database port to database security group
        
        3. Database Security Group:
           - Inbound: Database port (3306/5432) from application security group only
           - No outbound internet access
        
        ENHANCED SECURITY FEATURES:
        - Implement principle of least privilege
        - Use specific port ranges, no wildcards
        - Add detailed descriptions for each rule
        - Enable security group rule descriptions
        
        REQUIRED OUTPUTS (These will be used by other modules):
        - alb_sg_id: For load balancer attachment
        - application_sg_id: For EC2 instances
        - database_sg_id: For RDS instances
        
        GENERATE THREE FILES:
        1. main.tf - Security group resources with specific rules
        2. variables.tf - VPC ID, CIDR blocks, ports, and dependency variables
        3. outputs.tf - ALL required security group IDs listed above
        
        Use separate aws_security_group_rule resources for better management.
        """

    def get_database_prompt(self, user_input: Dict[str, Any], dependencies: Dict[str, Any] = None) -> str:
        """Generate database resources based on detected services"""
        
        detected_db_services = [svc for svc in user_input['detected_services'] if svc in ['rds', 'dynamodb']]
        networking_deps = dependencies.get('networking', {}) if dependencies else {}
        security_deps = dependencies.get('security', {}) if dependencies else {}
        
        return f"""
        {self.base_context}
        
        TASK: Generate database module for {user_input['application_type']}
        
        PROJECT CONTEXT:
        - Project: {user_input['project_name']}
        - Description: {user_input['description']}
        - Detected Services: {detected_db_services}
        - Security Level: {user_input['security_level']}
        
        DEPENDENCY USAGE IN CODE:
        Use these exact references in your Terraform code:
        - Database Subnet Group: var.networking_db_subnet_group_name
        - Database Security Group: var.security_database_sg_id
        - Database Subnet IDs: var.networking_database_subnet_ids (if needed for manual subnet group)
        
        DATABASE STRATEGY:
        Since both RDS and DynamoDB were detected, implement hybrid approach:
        
        1. RDS (PostgreSQL) for structured data:
           - User accounts, application data
           - ACID compliance for transactions
           - Multi-AZ for high availability
           - Automated backups (7-day retention)
           - Encryption at rest enabled
           - Use existing db_subnet_group from networking module
        
        2. DynamoDB for scalable NoSQL data:
           - Session data, temporary data
           - High-throughput operations
           - Auto-scaling enabled
           - Point-in-time recovery
        
        RDS CONFIGURATION:
        - Engine: PostgreSQL 15.x
        - Instance: db.t3.micro (dev) / db.t3.medium (prod)
        - Storage: 20GB GP2, auto-scaling enabled
        - Backup window: 03:00-04:00 UTC
        - Maintenance window: Sun:04:00-Sun:05:00 UTC
        - Security Groups: [var.security_database_sg_id]
        - DB Subnet Group: var.networking_db_subnet_group_name
        
        DYNAMODB CONFIGURATION:
        - Billing mode: PAY_PER_REQUEST (for variable workloads)
        - Encryption: AWS managed keys
        - Stream: enabled for event processing
        
        ENHANCED SECURITY:
        - RDS: Enable Performance Insights
        - Both: Enable detailed monitoring
        - Use AWS Secrets Manager for credentials
        - Implement proper IAM policies
        
        
        REQUIRED OUTPUTS (These will be used by other modules):
        - rds_endpoint: For application connection
        - rds_instance_id: For monitoring
        - dynamodb_table_name: For application access
        - dynamodb_table_arn: For IAM policies
        - database_secret_arn: For application credential access
        
        GENERATE THREE FILES:
        1. main.tf - RDS instance, DynamoDB table, secrets
        2. variables.tf - Database configurations, credentials, and dependency variables
        3. outputs.tf - ALL required database outputs listed above
        """

    def get_compute_prompt(self, user_input: Dict[str, Any], dependencies: Dict[str, Any] = None) -> str:
        """Generate compute resources (EC2, Auto Scaling, etc.)"""
        
        networking_deps = dependencies.get('networking', {}) if dependencies else {}
        security_deps = dependencies.get('security', {}) if dependencies else {}
        database_deps = dependencies.get('database', {}) if dependencies else {}
        
        return f"""
        {self.base_context}
        
        TASK: Generate compute module for scalable {user_input['application_type']}
        
        PROJECT CONTEXT:
        - Project: {user_input['project_name']}
        - Description: {user_input['description']}
        - Security Level: {user_input['security_level']}
        
        
        DEPENDENCY USAGE IN CODE:
        Use these exact references in your Terraform code:
        - Private Subnets: var.networking_private_subnet_ids
        - Public Subnets: var.networking_public_subnet_ids  
        - Application Security Group: var.security_application_sg_id
        - ALB Security Group: var.security_alb_sg_id
        - Database Endpoint: var.database_rds_endpoint
        - DynamoDB Table: var.database_dynamodb_table_name
        - VPC ID: var.networking_vpc_id
        
        COMPUTE ARCHITECTURE:
        Design for "scalable database" requirement with these components:
        
        1. Launch Template:
           - AMI: Latest Amazon Linux 2023 (use data source)
           - Instance Type: t3.medium (scalable sizing)
           - Security Groups: [var.security_application_sg_id]
           - User Data: Install application dependencies
           - IAM Instance Profile: EC2 service role
        
        2. Auto Scaling Group:
           - Min: 2, Max: 10, Desired: 2
           - VPC Zone Identifier: var.networking_private_subnet_ids
           - Target Group attachment for ALB
           - Health checks: ELB + EC2
           - Scaling policies: CPU-based (scale out >70%, scale in <30%)
        
        3. Application Load Balancer:
           - Internet-facing in public subnets: var.networking_public_subnet_ids
           - Security Groups: [var.security_alb_sg_id]
           - Target Group: HTTP/HTTPS health checks
           - Listener: Redirect HTTP to HTTPS
           - SSL Certificate: ACM (if domain provided)
        
        IAM ROLE PERMISSIONS:
        - CloudWatch Logs: Write application logs
        - Secrets Manager: Read database credentials (var.database_database_secret_arn)
        - DynamoDB: Read/Write to application table
        - S3: Access to deployment artifacts (if needed)
        
        USER DATA SCRIPT:
        #!/bin/bash
        yum update -y
        yum install -y docker
        systemctl start docker
        systemctl enable docker
        # Install CloudWatch agent
        # Configure application environment variables from dependencies:
        echo "DB_ENDPOINT=var.database_rds_endpoint" >> /etc/environment
        echo "DYNAMODB_TABLE=var.database_dynamodb_table_name" >> /etc/environment
        
        ENHANCED FEATURES:
        - CloudWatch detailed monitoring
        - Application logs to CloudWatch Logs
        - Systems Manager Session Manager (no SSH keys needed)
        - Instance refresh for zero-downtime deployments
        
        
        REQUIRED OUTPUTS (These will be used by other modules):
        - alb_dns_name: For DNS configuration
        - alb_arn: For monitoring and WAF attachment
        - alb_zone_id: For Route53 alias records
        - target_group_arn: For additional services
        - asg_name: For monitoring and scaling policies
        - launch_template_id: For updates and monitoring
        
        GENERATE THREE FILES:
        1. main.tf - Launch template, ASG, ALB, target groups with proper dependency references
        2. variables.tf - Instance types, scaling parameters, AMI IDs, and dependency variables
        3. outputs.tf - ALL required compute outputs listed above
        """

    def get_monitoring_prompt(self, user_input: Dict[str, Any], dependencies: Dict[str, Any] = None) -> str:
        """Generate monitoring and logging resources"""
        
        compute_deps = dependencies.get('compute', {}) if dependencies else {}
        database_deps = dependencies.get('database', {}) if dependencies else {}
        networking_deps = dependencies.get('networking', {}) if dependencies else {}
        
        return f"""
        {self.base_context}
        
        TASK: Generate comprehensive monitoring module for {user_input['application_type']}
        
        PROJECT CONTEXT:
        - Project: {user_input['project_name']}
        - Security Level: {user_input['security_level']} (Enhanced monitoring required)
        
        
        DEPENDENCY USAGE IN CODE:
        Use these exact references in your Terraform code:
        - ALB ARN: var.compute_alb_arn
        - ALB Full Name: var.compute_alb_dns_name
        - Auto Scaling Group: var.compute_asg_name
        - RDS Instance ID: var.database_rds_instance_id
        - DynamoDB Table: var.database_dynamodb_table_name
        - Target Group ARN: var.compute_target_group_arn
        
        MONITORING STRATEGY:
        Implement comprehensive observability for enhanced security level:
        
        1. CloudWatch Log Groups:
           - Application Logs: /aws/ec2/{user_input['project_name']}/application
           - ALB Access Logs: /aws/alb/{user_input['project_name']}
           - VPC Flow Logs: /aws/vpc/{user_input['project_name']}/flowlogs
           - RDS Performance: /aws/rds/instance/{user_input['project_name']}/postgresql
        
        2. CloudWatch Alarms (using dependency references):
           - ALB: High response time (>2s), error rate (>5%)
             * Use ALB ARN: var.compute_alb_arn for metric dimensions
           - EC2: High CPU (>80%), low disk space (<10%)
             * Use ASG name: var.compute_asg_name for AutoScaling metrics
           - RDS: High connections, CPU, read latency
             * Use RDS instance ID: var.database_rds_instance_id
           - DynamoDB: Throttled requests, consumed capacity
             * Use table name: var.database_dynamodb_table_name
        
        3. SNS Topic for Alerts:
           - Email notifications for critical alarms
           - Integration with Slack/Teams (if webhook provided)
        
        4. CloudWatch Dashboard:
           - Application performance metrics (using ALB metrics)
           - Infrastructure health overview (using ASG metrics)
           - Database performance metrics (using RDS metrics)
           - Security metrics (failed logins, etc.)
        
        ENHANCED SECURITY MONITORING:
        - GuardDuty: Enable threat detection
        - Config Rules: Monitor compliance
        - CloudTrail: API call logging
        - VPC Flow Logs: Network traffic analysis
        
        COST OPTIMIZATION:
        - Set log retention policies (30 days for debug, 1 year for audit)
        - Use metric filters to reduce noise
        - Implement log aggregation
        
        
        REQUIRED OUTPUTS (These will be used by security module):
        - dashboard_url: For operations team
        - sns_topic_arn: For additional integrations
        - log_group_names: For log analysis
        - cloudtrail_s3_bucket: For audit compliance
        
        GENERATE THREE FILES:
        1. main.tf - Log groups, alarms, dashboard, SNS topics with proper dependency references
        2. variables.tf - Retention periods, alarm thresholds, notification emails, and dependency variables
        3. outputs.tf - ALL required monitoring outputs listed above
        """

    def get_security_enhancement_prompt(self, user_input: Dict[str, Any], dependencies: Dict[str, Any] = None) -> str:
        """Generate additional security resources for Enhanced security level"""
        
        compute_deps = dependencies.get('compute', {}) if dependencies else {}
        networking_deps = dependencies.get('networking', {}) if dependencies else {}
        monitoring_deps = dependencies.get('monitoring', {}) if dependencies else {}
        
        return f"""
        {self.base_context}
        
        TASK: Generate security enhancement module for Enhanced security level
        
        PROJECT CONTEXT:
        - Project: {user_input['project_name']}
        - Security Level: {user_input['security_level']} (Enhanced)
        - Application: ATS Resume Checker (PII handling required)
        
        
        DEPENDENCY USAGE IN CODE:
        Use these exact references in your Terraform code:
        - ALB ARN: var.compute_alb_arn (for WAF attachment)
        - VPC ID: var.networking_vpc_id (for Config rules)
        - SNS Topic: var.monitoring_sns_topic_arn (for security alerts)
        
        ENHANCED SECURITY COMPONENTS:
        
        1. WAF (Web Application Firewall):
           - Attach to ALB using: var.compute_alb_arn
           - AWS Managed Rules: Core Rule Set, Known Bad Inputs
           - Custom Rules: Rate limiting (100 req/5min per IP)
           - SQL injection and XSS protection
           - Geo-blocking if needed
        
        2. AWS Config:
           - Monitor resource compliance
           - Rules: Encrypted storage, secure security groups
           - Configuration recorder for all resources in VPC: var.networking_vpc_id
        
        3. GuardDuty:
           - Enable threat detection
           - Monitor for malicious activity
           - Integration with existing SNS: var.monitoring_sns_topic_arn
        
        4. Secrets Manager:
           - Database credentials rotation
           - Application API keys
           - JWT signing keys
        
        5. KMS Keys:
           - Custom CMK for application data encryption
           - Separate keys for different data types
           - Automatic key rotation enabled
        
        6. IAM Roles and Policies:
           - Least privilege principle
           - Service-specific roles
           - Policy conditions for IP/time restrictions
        
        7. S3 Bucket (if file uploads needed):
           - Encryption with CMK
           - Versioning enabled
           - Block public access
           - Access logging
           - Lifecycle policies
        
        COMPLIANCE FEATURES:
        - CloudTrail: All API calls logged
        - VPC Flow Logs: All network traffic
        - Access Analyzer: Review resource policies
        - Security Hub: Centralized security findings
        
        PII PROTECTION (Resume data):
        - Encryption at rest and in transit
        - Access logging and monitoring
        - Data retention policies
        - Backup encryption
        
        REQUIRED OUTPUTS:
        - waf_web_acl_arn: For additional protection rules
        - kms_key_arn: For application encryption
        - secrets_manager_arn: For credential rotation
        - security_hub_arn: For compliance reporting
        
        GENERATE THREE FILES:
        1. main.tf - WAF, Config, GuardDuty, KMS, Secrets Manager with proper dependency references
        2. variables.tf - Security configurations, compliance settings, and dependency variables
        3. outputs.tf - ALL required security resource outputs listed above
        """

    def get_component_generation_order(self, user_input: Dict[str, Any]) -> List[ComponentType]:
        """Determine the order of component generation based on dependencies"""
        
        # Base order for web applications
        base_order = [
            ComponentType.NETWORKING,    # Must be first - provides VPC, subnets
            ComponentType.SECURITY,      # Security groups depend on VPC
            ComponentType.DATABASE,      # Can be parallel with compute, but needed for app config
            ComponentType.COMPUTE,       # Depends on networking, security, database
            ComponentType.MONITORING,    # Depends on all other resources for monitoring
        ]
        
        # Add security enhancements if Enhanced level
        if user_input.get('security_level') == 'Enhanced':
            base_order.append(ComponentType.SECURITY)  # Additional security module
        
        return base_order

    def generate_component_context(self, 
                                 component_type: ComponentType, 
                                 user_input: Dict[str, Any],
                                 previous_outputs: Dict[str, Dict[str, Any]]) -> ComponentContext:
        """Generate context for each component based on dependencies"""
        
        context_map = {
            ComponentType.NETWORKING: ComponentContext(
                component_type=ComponentType.NETWORKING,
                dependencies=[],
                outputs_needed=["vpc_id", "public_subnet_ids", "private_subnet_ids", "database_subnet_ids", "db_subnet_group_name"],
                security_level=user_input.get('security_level', 'Basic'),
                region="us-west-2"
            ),
            ComponentType.SECURITY: ComponentContext(
                component_type=ComponentType.SECURITY,
                dependencies=["networking"],
                outputs_needed=["alb_sg_id", "application_sg_id", "database_sg_id"],
                security_level=user_input.get('security_level', 'Basic'),
                region="us-west-2"
            ),
            ComponentType.DATABASE: ComponentContext(
                component_type=ComponentType.DATABASE,
                dependencies=["networking", "security"],
                outputs_needed=["rds_endpoint", "dynamodb_table_name", "database_secret_arn", "rds_instance_id"],
                security_level=user_input.get('security_level', 'Basic'),
                region="us-west-2"
            ),
            ComponentType.COMPUTE: ComponentContext(
                component_type=ComponentType.COMPUTE,
                dependencies=["networking", "security", "database"],
                outputs_needed=["alb_dns_name", "alb_arn", "asg_name", "target_group_arn", "launch_template_id"],
                security_level=user_input.get('security_level', 'Basic'),
                region="us-west-2"
            ),
            ComponentType.MONITORING: ComponentContext(
                component_type=ComponentType.MONITORING,
                dependencies=["compute", "database", "networking"],
                outputs_needed=["dashboard_url", "sns_topic_arn", "log_group_names", "cloudtrail_s3_bucket"],
                security_level=user_input.get('security_level', 'Basic'),
                region="us-west-2"
            )
        }
        
        return context_map.get(component_type)
