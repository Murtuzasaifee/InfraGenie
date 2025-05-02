from pydantic import BaseModel, Field
from loguru import logger
from src.infra_genie.state.infra_genie_state import InfraGenieState, TerraformComponent
from langchain_core.prompts import PromptTemplate
from src.infra_genie.utils import constants as const
import re
    

class FallbackNode:
    
    def __init__(self, llm):
        self.llm = llm
       
    
    def fallback_generate_terraform_code(self, state: InfraGenieState):
        
        """
        Generate Terraform code with fallback approach.
        
        """

        if not state.user_input:
            raise ValueError("User input is required to generate Terraform code")
        
        try:
            print("Trying fallback approach...")
                    
            prompt_template = self.get_fallback_code_prompt()
            logger.debug(f"Prompt Template: {prompt_template}")
            
            structured_prompt = PromptTemplate.from_template(prompt_template)
            logger.debug(f"""Structured Prompt: {structured_prompt.to_json()}""")
            
            input_dict = state.user_input.model_dump()
            logger.debug(f"User Input: {input_dict}")

            structured_chain = structured_prompt | self.llm

            result = structured_chain.invoke(input_dict)
            
            content = result.content
            logger.debug(f"Content: {content}")
            
            # Extract environment blocks
            env_pattern = r"# ENV: (\w+) - (\w+\.tf)\n([\s\S]*?)(?=# ENV:|# MODULE:|$)"
            env_matches = re.findall(env_pattern, content)
            
            # Extract module blocks
            module_pattern = r"# MODULE: (\w+) - (\w+\.tf)\n([\s\S]*?)(?=# ENV:|# MODULE:|$)"
            module_matches = re.findall(module_pattern, content)
        
            # Dictionary to organize the extracted content
            environments = {}
            modules = {}
            
            # Process environment matches
            for env_name, file_type, content in env_matches:
                if env_name not in environments:
                    environments[env_name] = {"name": env_name, "main_tf": "", "variables_tf": "", "output_tf": ""}
                
                if file_type == "main.tf":
                    environments[env_name]["main_tf"] = content.strip()
                elif file_type == "variables.tf":
                    environments[env_name]["variables_tf"] = content.strip()
                elif file_type == "output.tf":
                    environments[env_name]["output_tf"] = content.strip()
            
            # Process module matches
            for module_name, file_type, content in module_matches:
                if module_name not in modules:
                    modules[module_name] = {"name": module_name, "main_tf": "", "variables_tf": "", "output_tf": ""}
                
                if file_type == "main.tf":
                    modules[module_name]["main_tf"] = content.strip()
                elif file_type == "variables.tf":
                    modules[module_name]["variables_tf"] = content.strip()
                elif file_type == "output.tf":
                    modules[module_name]["output_tf"] = content.strip()
            
            # Update state with extracted environments
            for env_name, env_data in environments.items():
                component = TerraformComponent(
                    name=env_data["name"],
                    main_tf=env_data["main_tf"],
                    output_tf=env_data["output_tf"],
                    variables_tf=env_data["variables_tf"]
                )
                state.environments.environments.append(component)
            
            # Update state with extracted modules
            for module_name, module_data in modules.items():
                component = TerraformComponent(
                    name=module_data["name"],
                    main_tf=module_data["main_tf"],
                    output_tf=module_data["output_tf"],
                    variables_tf=module_data["variables_tf"]
                )
                state.modules.modules.append(component)
            
            print(f"Successfully generated {len(state.environments.environments)} environments and {len(state.modules.modules)} modules using fallback approach")
            state.code_generated = True
            state.next_node = const.CODE_VALIDATION
        
        except Exception as fallback_error:
            print(f"Improved fallback attempt failed: {fallback_error}")
            state.code_generated = False
            state.next_node = const.ERROR
        
        return state
    

    def get_fallback_code_prompt(self) -> str:
        terraform_prompt = """
        You're a senior AWS Solutions Architect creating production-grade Terraform code. Generate infrastructure as code based on the following specifications:

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
        - Custom Parameters: {custom_parameters}

        TERRAFORM BEST PRACTICES TO IMPLEMENT:
        1. Use provider as aws for all the environments
        2. Add region {region} for all the environments under the provider
        3. Create a modular design with proper service isolation
        4. Implement proper network segregation (public/private/database subnets)
        5. Follow least privilege IAM policies and proper encryption
        6. Use environment-specific configurations with proper variable typing
        7. Use data sources for dynamic lookups and proper resource repetition
        8. Put all the network related things under a 'netoworking' module e.g. vpc, subnets, security groups etc.

        ENVIRONMENT CONFIGURATIONS:
        - dev: minimal capacity and redundancy
        - stage: medium capacity with good redundancy
        - prod: high capacity with full redundancy and auto-scaling

        I need you to generate Terraform (HCL) code for the following environments and modules.
        For each environment (dev, stage, prod), create three files:
        1. main.tf - with the module configurations
        2. variables.tf - with input variables
        3. output.tf - with output values
        In each environment configurations (dev, stage, prod), in their main.tf file give the module path as ex: (source = "../../modules/lambda")

        For each required module based on the services list ({services}) and {requirements}, create:
        1. main.tf - with the resource definitions
        2. variables.tf - with input variables for the module
        3. output.tf - with output values from the module

        Format your response with clear headers between each file, like this:
        # ENV: dev - main.tf
        <code here>

        # ENV: dev - variables.tf
        <code here>

        # ENV: dev - output.tf
        <code here>

        # MODULE: vpc - main.tf
        <code here>

        And so on for all environments and modules.
        DO NOT provide explanations or additional text - ONLY the Terraform code with headers.
        Do not include markdown code block syntax like ```terraform or ``` around the generated Terraform code. Only provide raw .tf content without wrapping it in code fences.
        """
        
        return terraform_prompt
        