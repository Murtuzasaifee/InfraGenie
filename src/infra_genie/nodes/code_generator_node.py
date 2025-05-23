from loguru import logger
from src.infra_genie.state.infra_genie_state import InfraGenieState, TerraformOutput, TerraformComponent
from langchain_core.prompts import PromptTemplate
from src.infra_genie.utils import constants as const
from src.infra_genie.utils.Utility import Utility
import json
    

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
            
            # Clear existing environments and modules before adding new ones
            state.environments.environments.clear()
            state.modules.modules.clear()
            
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
        """
        Get the Terraform code generation prompt with validation feedback incorporated.
        """
        
        base_prompt = """
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
        """

        # Check for validation feedback and incorporate it
        validation_feedback = getattr(state, 'code_validation_feedback', None)
        user_feedback = getattr(state, 'code_validation_user_feedback', None)
        
        feedback_section = ""
        if validation_feedback or user_feedback:
            feedback_section = "\n**CRITICAL: INCORPORATE THE FOLLOWING FEEDBACK TO FIX VALIDATION ERRORS:**\n"
            
            if validation_feedback:
                feedback_section += f"""
                **Terraform Validation Errors to Fix:**
                {validation_feedback}

                **ACTION REQUIRED:** 
                - Analyze each validation error above
                - Fix ALL syntax errors, unsupported arguments, and missing variable declarations
                - Ensure ALL variable references are properly declared in variables.tf files
                - Use only supported resource arguments as per AWS provider documentation
                - Fix any CIDR block issues or overlapping subnets
                - Ensure proper module references and dependencies

                """
                
                if user_feedback:
                    feedback_section += f"""
                    **User Feedback to Address:**
                    {user_feedback}

                    **ACTION REQUIRED:**
                    - Address all user concerns and requirements
                    - Implement suggested improvements
                    - Ensure the solution meets user expectations

                    """
            
            # Add context about existing code if available
            if hasattr(state, 'environments') and state.environments.environments:
                feedback_section += """
                **EXISTING CODE CONTEXT:**
                You are fixing/improving existing Terraform code. Make sure to:
                - Maintain the same module structure and naming conventions
                - Fix errors without breaking working parts
                - Preserve user requirements and infrastructure specifications
                - Only modify what needs to be fixed based on the feedback above

                """

        # Combine base prompt with feedback section
        prompt_with_feedback = base_prompt + feedback_section

        # Add the rest of the prompt
        rest_of_prompt = """
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

        VALIDATION CHECKLIST:
        - [ ] All variables are declared in variables.tf
        - [ ] All data sources have required arguments
        - [ ] All resource arguments are supported
        - [ ] All module references use correct paths
        - [ ] All CIDR blocks are valid and non-overlapping
        - [ ] All cross-references use proper syntax
        - [ ] Provider configuration is included in each module
        - [ ] No deprecated or unsupported arguments used

        DELIVERABLES:
        1. Generate ONLY dev environment as TerraformComponent with:
        - Complete provider configuration in main.tf
        - Proper module references with correct source paths
        - ALL required variables declared in variables.tf
        - Comprehensive outputs in output.tf

        2. Generate modules ONLY for services in {{services}} list:
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
        - Correct any invalid CIDR notations in {{subnet_configuration}}
        - Ensure all subnets are within VPC CIDR range
        - Use proper /24, /16 notation

        Your task is to generate VALIDATION-COMPLIANT, production-ready Terraform code that PASSES terraform validate without errors. The code must be syntactically correct, use only supported arguments, and have all dependencies properly declared.
        """

        return prompt_with_feedback + rest_of_prompt
    
    def is_code_generated(self, state: InfraGenieState):
        """Decide whether to use the fallback method based on the code generation status."""
        return state.code_generated
    
    def fix_code(self, state: InfraGenieState):
        """
        This method is called when code validation fails and we need to fix the code.
        It's essentially a wrapper around generate_terraform_code but with feedback context.
        """
        logger.info("Fixing Terraform code based on validation feedback...")
        
        # Reset code generation status to trigger regeneration
        state.code_generated = False
        
        # Call the main generation method which will now include validation feedback
        return self.generate_terraform_code(state)