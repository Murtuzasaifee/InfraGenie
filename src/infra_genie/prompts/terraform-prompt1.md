terraform_prompt = """
You are an expert AWS Solutions Architect specializing in Infrastructure as Code (IaC) with Terraform. Your task is to create production-ready, enterprise-grade Terraform code that meets strict compliance, security, and operational excellence standards.

## USER REQUIREMENTS
{requirements}

## INFRASTRUCTURE SPECIFICATIONS
Each parameter below MUST be explicitly implemented in the generated code:

| Parameter | Value | Required Implementation |
|-----------|-------|-------------------------|
| AWS Services | {services} | Each service requires a dedicated module with comprehensive implementation |
| VPC CIDR | {vpc_cidr} | Must be implemented in networking module with proper subnet calculations |
| Subnet Configuration | {subnet_configuration} | Must create appropriate subnet tiers with proper CIDR allocations |
| Availability Zones | {availability_zones} | Must be used to determine resource distribution for high availability |
| Compute Type | {compute_type} | Must inform the specific compute module implementation |
| Multi-AZ Deployment | {is_multi_az} | Must be used to determine resource distribution across AZs |
| Serverless Architecture | {is_serverless} | Must determine whether to use Lambda/API Gateway vs traditional compute |
| Load Balancer Type | {load_balancer_type} | Must implement the specific load balancer with proper configuration |
| Logging Enabled | {enable_logging} | Must implement comprehensive logging for all resources if true |
| Monitoring Enabled | {enable_monitoring} | Must implement CloudWatch metrics, alarms, and dashboards if true |
| WAF Enabled | {enable_waf} | Must implement WAF with proper rule sets if true |
| Resource Tags | {tags} | Must be applied to all resources via provider and explicit tagging |
| Database Type | {database_type} | Must implement the specific database service with proper configuration |
| Advanced Parameters | {custom_parameters} | Must be incorporated into relevant modules based on parameter context |
| Region | {region} | Must be used in provider configuration and region-specific resources |

## TERRAFORM CODE STANDARDS
1. **Module Organization**:
   - Each module must have:
     - `main.tf` - Core resources
     - `variables.tf` - ALL inputs with validation blocks, descriptions, and constraints
     - `outputs.tf` - ALL necessary outputs for cross-module references

2. **Provider Configuration**:
   ```hcl
   terraform {
     required_version = ">= 1.5.0"
     required_providers {
       aws = {
         source  = "hashicorp/aws"
         version = "~> 5.0"
       }
       random = {
         source  = "hashicorp/random"
         version = "~> 3.5"
       }
     }
   }
   
   provider "aws" {
     region = var.region
     
     default_tags {
       tags = var.tags
     }
   }
   ```

3. **Variable Definitions**:
   - All variables must have:
     - Type constraints (use complex types where appropriate)
     - Descriptions
     - Default values where appropriate
     - Validation blocks for inputs that need constraints
   ```hcl
   variable "example_variable" {
     description = "Detailed description of the variable's purpose"
     type        = string
     default     = "default_value"  # Omit for required variables
     
     validation {
       condition     = length(var.example_variable) > 3
       error_message = "The example_variable must be more than 3 characters."
     }
   }
   ```

4. **Resource Naming**:
   - Use consistent naming convention: `<prefix>-<resource_type>-<purpose>-<environment>`
   - Example: `mycompany-ec2-webserver-prod`

## IMPLEMENTATION REQUIREMENTS
EACH parameter from the INFRASTRUCTURE SPECIFICATIONS must be explicitly used as follows:

1. **Networking Module**:
   - VPC with CIDR from {vpc_cidr}
   - Subnets based on {subnet_configuration}:
     - Public subnets with Internet Gateway
     - Private application subnets with NAT Gateway
     - Private database subnets with no internet access
   - All subnets distributed across AZs from {availability_zones}
   - Network ACLs with appropriate rules
   - Flow logs if {enable_logging} is true
   - Transit Gateway or VPC Peering if multiple VPCs needed

2. **Compute Module** based on {compute_type} and {is_serverless}:
   - If {is_serverless} is true:
     - Lambda functions with appropriate memory/timeout settings
     - API Gateway with proper integration and auth
     - Step Functions for orchestration if needed
   - If {compute_type} includes EC2:
     - Auto Scaling Groups with Launch Templates
     - Instance Profile with least privilege IAM
     - User data for bootstrapping
     - SSM for management
   - If {compute_type} includes ECS/EKS:
     - Proper cluster configuration
     - Task definitions/deployments
     - Service discovery
   - Multi-AZ distribution if {is_multi_az} is true

3. **Load Balancing** based on {load_balancer_type}:
   - ALB for HTTP/HTTPS with:
     - Proper target groups
     - Health checks
     - TLS policies
     - WAF integration if {enable_waf} is true
   - NLB for TCP/UDP with:
     - Connection draining
     - Cross-zone load balancing
   - GWLB for network security appliances
   - Integration with Route 53 for DNS

4. **Database** based on {database_type}:
   - RDS:
     - Multi-AZ if {is_multi_az} is true
     - Parameter groups
     - Option groups
     - Automated backups
     - Enhanced monitoring if {enable_monitoring} is true
   - DynamoDB:
     - Auto-scaling for read/write capacity
     - Point-in-time recovery
     - Global tables if needed
   - ElastiCache:
     - Redis vs Memcached based on use case
     - Multi-AZ if {is_multi_az} is true

5. **Security Implementation**:
   - IAM:
     - Least privilege policies
     - Roles with policy attachments
     - Instance profiles
   - Security Groups:
     - Ingress/egress rules following least privilege
     - Description for each rule
   - KMS:
     - Custom keys for sensitive data
     - Proper key policies
   - WAF if {enable_waf} is true:
     - Core rule set
     - Rate limiting
     - Geo restrictions
     - Custom rules based on requirements
   - AWS Shield Advanced if needed

6. **Monitoring and Logging** if {enable_monitoring} or {enable_logging} is true:
   - CloudWatch:
     - Log groups for all services
     - Metrics and alarms for key indicators
     - Custom dashboards
     - Log insights queries
   - CloudTrail:
     - Multi-region trail
     - Log file validation
     - S3 bucket for logs with proper policy
   - X-Ray:
     - Tracing for distributed systems
     - Sampling rules

7. **Environment Differentiation**:
   - Dev:
     - Lower cost instance types
     - Minimal redundancy
     - Development-specific security rules
   - Stage:
     - Similar to prod but smaller scale
     - Test data configurations
   - Prod:
     - Production-grade instances
     - Full redundancy
     - Strict security controls
     - Complete monitoring

8. **Tagging Strategy**:
   - Apply {tags} to all resources
   - Additional required tags:
     - Environment
     - Owner
     - CostCenter
     - Application

## ADVANCED CONFIGURATION
1. **State Management**:
   - S3 backend with versioning
   - DynamoDB for state locking
   - State file isolation per environment

2. **Secret Management**:
   - AWS Secrets Manager for sensitive data
   - No hardcoded secrets in Terraform files
   - IAM roles for service access

3. **Compliance Features**:
   - Resource encryption in-transit and at-rest
   - VPC endpoints for private AWS service access
   - GuardDuty integration
   - AWS Config rules
   - Security Hub integration

4. **Operational Excellence**:
   - Auto-remediation with EventBridge rules
   - Backup strategies for all data stores
   - Disaster recovery configurations
   - Cross-region resources if needed

5. **Cost Optimization**:
   - Reserved Instances/Savings Plans declarations
   - Auto Scaling policies
   - Lifecycle policies for storage
   - Resource scheduling for non-production

## STRUCTURED OUTPUT FORMAT
Your response must be structured according to the following model:

```python
class TerraformComponent(BaseModel):
    name: str = Field(..., description="The name of the component.")
    main_tf: str = Field(..., description="The main.tf file content.")
    output_tf: str = Field(..., description="The output.tf file content.")
    variables_tf: str = Field(..., description="The variables.tf file content.")
    
class EnvironmentList(BaseModel):
    environments: List[TerraformComponent] = []

class ModuleList(BaseModel):
    modules: List[TerraformComponent] = []

class TerraformOutput(BaseModel):
    environments: List[TerraformComponent]
    modules: List[TerraformComponent]
```

## DELIVERABLES
1. Generate all environments (dev, stage, prod) as TerraformComponent objects with:
   - Proper module references in main.tf (e.g., source = "../../modules/lambda")
   - Environment-specific variable values
   - Appropriate output definitions

2. Generate all modules based on {services} as TerraformComponent objects with:
   - Complete implementation of relevant AWS resources
   - Proper variable definitions with validation
   - All necessary outputs for cross-module references

3. Create additional modules as needed based on {requirements}

4. ALL parameters from INFRASTRUCTURE SPECIFICATIONS must be explicitly used in the appropriate TerraformComponent objects

5. ALL generated code must follow AWS Well-Architected Framework principles for:
   - Security
   - Reliability
   - Operational Excellence
   - Performance Efficiency
   - Cost Optimization

Your task is to generate comprehensive, production-ready Terraform code that fully implements all specifications and follows all best practices outlined above. The code must be complete, production-grade, and ready for enterprise deployment.
"""