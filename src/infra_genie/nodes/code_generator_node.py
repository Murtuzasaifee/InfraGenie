from loguru import logger
from src.infra_genie.state.infra_genie_state import InfraGenieState, TerraformOutput, TerraformComponent
from langchain_core.prompts import PromptTemplate
from src.infra_genie.utils import constants as const
from src.infra_genie.utils.Utility import Utility
    

class CodeGeneratorNode:
    
    def __init__(self, llm):
        self.llm = llm
        self.utility = Utility()
       
    
    def generate_terraform_code(self, state: InfraGenieState):
        
        """
        Generate Terraform code with structured output.
        
        """

        if not state.user_input:
            raise ValueError("User input is required to generate Terraform code")
        
        try:
            print("Trying structured code approach...")
                    
            prompt_template = self.get_terraform_code_prompt(state)
            logger.debug(f"Prompt Template: {prompt_template}")
            
            structured_prompt = PromptTemplate.from_template(prompt_template)
            
            logger.debug(f"Structured Prompt: {structured_prompt.to_json()}")

            input_dict = state.user_input.model_dump()
            logger.debug(f"User Input: {input_dict}")

            structured_llm = self.llm.with_structured_output(TerraformOutput)
            structured_chain = structured_prompt | structured_llm
    
            result = structured_chain.invoke(input_dict)
            
            logger.debug(f"Result: {result}")
            
            # Transfer the structured result to the state
            for env in result.environments:
                state.environments.environments.append(TerraformComponent(
                    name=env.name,
                    main_tf=env.main_tf,
                    output_tf=env.output_tf,
                    variables_tf=env.variables_tf
                ))
            
            for module in result.modules:
                state.modules.modules.append(TerraformComponent(
                    name=module.name,
                    main_tf=module.main_tf,
                    output_tf=module.output_tf,
                    variables_tf=module.variables_tf
                ))
            
            print(f"Successfully generated {len(state.environments.environments)} environments and {len(state.modules.modules)} modules using structured output")
            state.code_generated = True
            state.next_node = const.CODE_VALIDATION
            
        except Exception as primary_error:
            print(f"Structured output approach failed: {primary_error}")
            state.code_generated = False
            state.next_node = const.FALLBACK_GENERATION
        
        return state
    
    
    
    def get_terraform_code_prompt(self, state: InfraGenieState) -> str:
        terraform_prompt = """
        **Objective:** Generate a production-grade Terraform configuration (in HCL, not JSON) for an AWS infrastructure spanning development, staging, and production environments.

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

        1. Module Organization:
        - Each module must have:
            - main.tf - Core resources
            - variables.tf - ALL inputs with validation blocks, descriptions, and constraints
            - outputs.tf - ALL necessary outputs for cross-module references

        2. Provider Configuration Example:
        terraform {{
            required_version = ">= 1.5.0"
            required_providers {{
            aws = {{
                source  = "hashicorp/aws"
                version = "~> 5.0"
            }}
            random = {{
                source  = "hashicorp/random"
                version = "~> 3.5"
            }}
            }}
        }}
        
        provider "aws" {{
            region = var.region
            
            default_tags {{
            tags = var.tags
            }}
        }}

        3. Variable Definitions Example:
        variable "example_variable" {{
            description = "Detailed description of the variable's purpose"
            type        = string
            default     = "default_value"  # Omit for required variables
            
            validation {{
            condition     = length(var.example_variable) > 3
            error_message = "The example_variable must be more than 3 characters."
            }}
        }}

        4. Resource Naming:
        - Use consistent naming convention: prefix-resource_type-purpose-environment
        - Example: mycompany-ec2-webserver-prod

        IMPLEMENTATION REQUIREMENTS:
        EACH parameter from the INFRASTRUCTURE SPECIFICATIONS must be explicitly used as follows:

        1. Networking Module:
        - VPC with CIDR from {vpc_cidr}
        - Subnets based on {subnet_configuration}:
            - Public subnets with Internet Gateway
            - Private application subnets with NAT Gateway
            - Private database subnets with no internet access
        - All subnets distributed across AZs from {availability_zones}
        - Network ACLs with appropriate rules
        - Flow logs if {enable_logging} is true
        - Transit Gateway or VPC Peering if multiple VPCs needed

        2. Compute Module based on {compute_type} and {is_serverless}:
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

        3. Load Balancing based on {load_balancer_type}:
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

        4. Database based on {database_type}:
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

        5. Security Implementation:
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

        6. Monitoring and Logging if {enable_monitoring} or {enable_logging} is true:
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

        7. Environment Differentiation:
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

        8. Tagging Strategy:
        - Apply {tags} to all resources
        - Additional required tags:
            - Environment
            - Owner
            - CostCenter
            - Application

        ADVANCED CONFIGURATION:
        1. State Management:
        - S3 backend with versioning
        - DynamoDB for state locking
        - State file isolation per environment

        2. Secret Management:
        - AWS Secrets Manager for sensitive data
        - No hardcoded secrets in Terraform files
        - IAM roles for service access

        3. Compliance Features:
        - Resource encryption in-transit and at-rest
        - VPC endpoints for private AWS service access
        - GuardDuty integration
        - AWS Config rules
        - Security Hub integration

        4. Operational Excellence:
        - Auto-remediation with EventBridge rules
        - Backup strategies for all data stores
        - Disaster recovery configurations
        - Cross-region resources if needed

        5. Cost Optimization:
        - Reserved Instances/Savings Plans declarations
        - Auto Scaling policies
        - Lifecycle policies for storage
        - Resource scheduling for non-production

        STRUCTURED OUTPUT FORMAT:
        Your response must be structured according to the following model:

        class TerraformComponent:
            name: str              # The name of the component
            main_tf: str           # The main.tf file content
            output_tf: str         # The output.tf file content
            variables_tf: str      # The variables.tf file content
            
        class TerraformOutput:
            environments: List[TerraformComponent]  # dev, stage, prod environments
            modules: List[TerraformComponent]       # Service modules

        DELIVERABLES:
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


        
        # Check if code_validation_error exists and insert it into the prompt if it does
        code_feedback = getattr(state, 'code_validation_feedback', None)
        if code_feedback:
            # Insert the feedback after the objective line but before the inputs section
            objective_line = "**Objective:** Generate a production-grade Terraform configuration (in HCL, not JSON) for an AWS infrastructure spanning development, staging, and production environments."
            feedback_section = f"\n**Incorporate the following code review feedback :** {code_feedback}\n"
            
            # Replace the objective line with objective + feedback
            terraform_prompt = terraform_prompt.replace(
                objective_line, 
                objective_line + feedback_section
            )
        
        return terraform_prompt
    
    def is_code_generated(self, state: InfraGenieState):
        """Decide whether to use the fallback method based on the code generation status."""
        return state.code_generated
    
    def fix_code(self, state: InfraGenieState):
        pass