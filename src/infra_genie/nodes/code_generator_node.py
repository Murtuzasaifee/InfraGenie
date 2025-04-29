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
            print("Trying fallback approach...")
                    
            prompt_template = self.get_terraform_code_prompt()
            logger.debug(f"Prompt Template: {prompt_template}")
            
            structured_prompt = PromptTemplate.from_template(prompt_template)
            
            input_dict = state.user_input.model_dump()
            logger.debug(f"User Input: {input_dict}")

            structured_llm = self.llm.with_structured_output(TerraformOutput)
            structured_chain = structured_prompt | structured_llm

            result = structured_chain.invoke(input_dict)
            
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
    
    
    def get_terraform_code_prompt(self) -> str:
        terraform_prompt = """
        You're a senior AWS Solutions Architect creating Terraform code based on these specifications:

        USER REQUIREMENTS:
        {requirements}

        INFRASTRUCTURE SPECIFICATIONS:
        - AWS Services: {services}
        - AWS Region: {region}
        - VPC CIDR: {vpc_cidr}
        - Subnet Configuration: {subnet_configuration}
        - Availability Zones: {availability_zones}
        - Compute Type: {compute_type}
        - Multi-AZ Deployment: {is_multi_az}
        - Serverless Architecture: {is_serverless}
        - Load Balancer Type: {load_balancer_type}
        - Logging Enabled: {enable_logging}
        - Monitoring Enabled: {enable_monitoring}
        - WAF Enabled: {enable_waf}
        - Resource Tags: {tags}
        - Database Type: {database_type}
        - Advanced Parameters: {custom_parameters}

        GENERATE:
        1. Three environment configurations (dev, stage, prod)
        2. Modules for each AWS service in the service list: {services}
        3. Also create any other necessary modules as needed based on the requirements: {requirements} if any which is not included in the service list: {services}.
        4. In each environment configurations (dev, stage, prod), in their main.tf file give the module path as ex: (source = "../../modules/lambda")
        
        TERRAFORM BEST PRACTICES TO IMPLEMENT:
        1. Create a modular design with proper service isolation
        2. Implement proper network segregation (public/private/database subnets)
        3. Follow least privilege IAM policies and proper encryption
        4. Use environment-specific configurations with proper variable typing
        5. Set up remote state management with appropriate locking
        6. Include comprehensive tagging strategy 
        7. Implement proper error handling with lifecycle management
        8. Use latest Terraform AWS provider
        9. Use data sources for dynamic lookups and proper resource repetition
        10. Put all the network related things under a 'netoworking' module e.g. vpc, subnets, security groups etc.
        
        Follow AWS best practices for security, high availability, and infrastructure as code.
        """
        
        return terraform_prompt
        
    def is_code_generated(self, state: InfraGenieState):
        """Decide whether to use the fallback method based on the code generation status."""
        return state.code_generated