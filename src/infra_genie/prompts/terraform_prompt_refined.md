terraform_prompt = """
**Objective:** Generate a production-grade, VALIDATION-COMPLIANT Terraform configuration (in HCL, not JSON) for an AWS infrastructure spanning development environment.

**CRITICAL VALIDATION REQUIREMENTS:**
- ALL resources must use ONLY valid arguments supported by their resource types
- ALL variable references must be properly declared in variables.tf
- ALL data sources must be properly configured with required arguments
- ALL resource dependencies must be explicitly defined
- NO deprecated or unsupported arguments

USER REQUIREMENTS:
{requirements}

INFRASTRUCTURE SPECIFICATIONS:
Each parameter below MUST be explicitly implemented in the generated code:

Parameter: AWS Services
Value: {services}
Required Implementation: Each service requires a dedicated module with comprehensive implementation

Parameter: VPC CIDR
Value: {vpc_cidr}
Required Implementation: Must be implemented in networking module with proper subnet calculations

Parameter: Subnet Configuration
Value: {subnet_configuration}
Required Implementation: Must create appropriate subnet tiers with proper CIDR allocations

Parameter: Availability Zones
Value: {availability_zones}
Required Implementation: Must be used to determine resource distribution for high availability

Parameter: Compute Type
Value: {compute_type}
Required Implementation: Must inform the specific compute module implementation

Parameter: Multi-AZ Deployment
Value: {is_multi_az}
Required Implementation: Must be used to determine resource distribution across AZs

Parameter: Serverless Architecture
Value: {is_serverless}
Required Implementation: Must determine whether to use Lambda/API Gateway vs traditional compute

Parameter: Load Balancer Type
Value: {load_balancer_type}
Required Implementation: Must implement the specific load balancer with proper configuration

Parameter: Logging Enabled
Value: {enable_logging}
Required Implementation: Must implement comprehensive logging for all resources if true

Parameter: Monitoring Enabled
Value: {enable_monitoring}
Required Implementation: Must implement CloudWatch metrics, alarms, and dashboards if true

Parameter: WAF Enabled
Value: {enable_waf}
Required Implementation: Must implement WAF with proper rule sets if true

Parameter: Resource Tags
Value: {tags}
Required Implementation: Must be applied to all resources via provider and explicit tagging

Parameter: Database Type
Value: {database_type}
Required Implementation: Must implement the specific database service with proper configuration

Parameter: Advanced Parameters
Value: {custom_parameters}
Required Implementation: Must be incorporated into relevant modules based on parameter context

Parameter: Region
Value: {region}
Required Implementation: Must be used in provider configuration and region-specific resources

TERRAFORM CODE STANDARDS:

1. Provider Configuration (MANDATORY for each module):
```hcl
terraform {{
  required_version = ">= 1.5.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = var.region
  
  default_tags {{
    tags = var.common_tags
  }}
}}
```

2. Module Organization:
- Each module must have:
  - main.tf - Core resources with provider configuration
  - variables.tf - ALL inputs with proper types and validation
  - outputs.tf - ALL necessary outputs for cross-module references

3. Variable Definitions (ALL variables must be declared):
```hcl
variable "region" {{
  description = "AWS region for resources"
  type        = string
  validation {{
    condition     = can(regex("^[a-z]{{2}}-[a-z]+-[0-9]{{1}}[a-z]?$", var.region))
    error_message = "Region must be a valid AWS region format."
  }}
}}

variable "common_tags" {{
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {{}}
}}
```

4. Data Sources (use only when necessary):
```hcl
data "aws_availability_zones" "available" {{
  state = "available"
}}

data "aws_ami" "amazon_linux" {{
  most_recent = true
  owners      = ["amazon"]
  
  filter {{
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }}
}}
```

CRITICAL VALIDATION RULES:

1. **Networking Module Requirements:**
   - VPC: Use only `cidr_block`, `enable_dns_hostname`, `enable_dns_support`, `tags`
   - Subnets: Use only `vpc_id`, `cidr_block`, `availability_zone`, `map_public_ip_on_launch`, `tags`
   - Internet Gateway: Use only `vpc_id`, `tags`
   - Route Tables: Use only `vpc_id`, `tags`, and separate `aws_route` resources
   - NAT Gateway: Use only `allocation_id`, `subnet_id`, `tags`
   - Security Groups: Use only `name`, `description`, `vpc_id`, `tags`, and separate `aws_security_group_rule` resources

2. **EC2 Module Requirements:**
   - Launch Template: Use only supported arguments like `name_prefix`, `image_id`, `instance_type`, `vpc_security_group_ids`, `user_data`, `tag_specifications`
   - Auto Scaling Group: Use only `name`, `launch_template`, `vpc_zone_identifier`, `target_group_arns`, `health_check_type`, `min_size`, `max_size`, `desired_capacity`, `tag`
   - Target Group: Use only `name`, `port`, `protocol`, `vpc_id`, `health_check`, `tags`

3. **Lambda Module Requirements:**
   - Function: Use only `function_name`, `runtime`, `handler`, `filename` OR `s3_bucket`/`s3_key`, `role`, `environment`, `tags`
   - IAM Role: Use only `name`, `assume_role_policy`, `tags`
   - IAM Policy Attachment: Use only `role`, `policy_arn`

4. **ALB Module Requirements:**
   - Load Balancer: Use only `name`, `internal`, `load_balancer_type`, `subnets`, `security_groups`, `tags`
   - Listener: Use only `load_balancer_arn`, `port`, `protocol`, `default_action`
   - Target Group: Use only `name`, `port`, `protocol`, `vpc_id`, `health_check`, `tags`

5. **RDS Module Requirements:**
   - DB Instance: Use only `identifier`, `engine`, `engine_version`, `instance_class`, `allocated_storage`, `db_name`, `username`, `password`, `vpc_security_group_ids`, `db_subnet_group_name`, `multi_az`, `skip_final_snapshot`, `tags`
   - DB Subnet Group: Use only `name`, `subnet_ids`, `tags`

MANDATORY IMPLEMENTATION PATTERNS:

1. **Variable Dependencies:**
   - EVERY variable used in a module MUST be declared in that module's variables.tf
   - EVERY variable passed to a module MUST exist in the calling configuration
   - Use `var.variable_name` syntax consistently

2. **Resource Naming:**
   - Use descriptive, unique names for all resources
   - Follow pattern: `resource_type-purpose-environment`
   - Example: `aws_vpc.main`, `aws_subnet.public`, `aws_security_group.web`

3. **Cross-Module References:**
   - Use outputs to expose resource attributes
   - Reference outputs using `module.module_name.output_name`
   - Ensure all referenced outputs are properly declared

4. **Subnet CIDR Validation:**
   - Ensure all subnet CIDRs are within the VPC CIDR range
   - Use proper CIDR notation (e.g., "10.0.1.0/24", not "10.0.1.24/16")
   - Validate CIDR blocks don't overlap


ENVIRONMENT CONFIGURATION:

Dev Environment main.tf:
```hcl
terraform {{
  required_version = ">= 1.5.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = var.region
  
  default_tags {{
    tags = var.common_tags
  }}
}}

# Networking module
module "networking" {{
  source = "../../modules/networking"
  
  environment           = var.environment
  region               = var.region
  vpc_cidr            = var.vpc_cidr
  public_subnet_cidrs = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  database_subnet_cidrs = var.database_subnet_cidrs
  availability_zones   = var.availability_zones
  common_tags         = var.common_tags
}}

# Only include modules for requested services
# EC2 module (only if "ec2" in services)
module "ec2" {{
  source = "../../modules/ec2"
  
  environment       = var.environment
  vpc_id           = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  security_group_id = module.networking.ec2_security_group_id
  common_tags      = var.common_tags
}}
```

VALIDATION CHECKLIST:
- [ ] All variables are declared in variables.tf
- [ ] All data sources have required arguments
- [ ] All resource arguments are supported
- [ ] All module references use correct paths
- [ ] All CIDR blocks are valid and non-overlapping
- [ ] All cross-references use proper syntax
- [ ] Provider configuration is included in each module
- [ ] No deprecated or unsupported arguments used

STRUCTURED OUTPUT FORMAT:
Your response must be structured according to the following model:

class TerraformComponent:
    name: str              # The name of the component
    main_tf: str           # The main.tf file content
    output_tf: str         # The output.tf file content
    variables_tf: str      # The variables.tf file content
    
class TerraformOutput:
    environments: List[TerraformComponent]  # dev environment
    modules: List[TerraformComponent]       # Service modules

DELIVERABLES:
1. Generate ONLY dev environment as TerraformComponent with:
   - Complete provider configuration in main.tf
   - Proper module references with correct source paths
   - ALL required variables declared in variables.tf
   - Comprehensive outputs in output.tf

2. Generate modules ONLY for services in {services} list:
   - networking (always required)
   - ec2 (if "ec2" in services)
   - lambda (if "lambda" in services)
   - rds (if database_type is specified)
   - alb (if load_balancer_type is "ALB")

3. Each module must include:
   - Complete provider configuration in main.tf
   - ALL variables properly declared with types and validation
   - ALL necessary outputs for inter-module dependencies
   - ONLY supported resource arguments

4. Fix CIDR block issues:
   - Correct any invalid CIDR notations in {subnet_configuration}
   - Ensure all subnets are within VPC CIDR range
   - Use proper /24, /16 notation

Your task is to generate VALIDATION-COMPLIANT, production-ready Terraform code that PASSES terraform validate without errors. The code must be syntactically correct, use only supported arguments, and have all dependencies properly declared.
"""