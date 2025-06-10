from loguru import logger
from src.infra_genie.state.infra_genie_state import InfraGenieState, TerraformOutput, TerraformComponent, UserInput
from langchain_core.prompts import PromptTemplate
from src.infra_genie.utils import constants as const
from src.infra_genie.utils.Utility import Utility
from src.infra_genie.utils.components_type import ComponentType
import json
from typing import Dict, Any, List
from src.infra_genie.nodes.decomposed_prompts import DecomposedTerraformPrompts
    

class CodeGeneratorNode:
    
    def __init__(self, llm):
        self.llm = llm
        self.utility = Utility()
        self.generated_outputs = {}
        self.component_order = []
       
    def generate_terraform_code(self, state: InfraGenieState):
        """
        Generate Terraform code using decomposed component approach
        """
        if not state.user_input:
            raise ValueError("User input is required to generate Terraform code")
        
        try:
            print("Starting component-based Terraform generation...")
            
            # Convert user input to dict for easier handling
            user_input_dict = self.extract_user_input_dict(state.user_input)
            logger.debug(f"User Input Dict: {user_input_dict}")
            
            # Determine component generation order
            self.component_order = self.get_generation_order(user_input_dict)
            logger.info(f"Generation order: {[c.value for c in self.component_order]}")
            
            # Clear existing state
            state.environments.environments.clear()
            state.modules.modules.clear()
            
            # Generate each component
            all_components = {}
            for component_type in self.component_order:
                logger.info(f"Generating {component_type.value} component...")
                
                try:
                    component = self.generate_single_component(component_type, user_input_dict)
                    all_components[component_type.value] = component
                    
                    # Store outputs for dependency resolution
                    self.generated_outputs[component_type.value] = self.extract_component_outputs(component)
                    
                    logger.success(f"✅ {component_type.value} component generated")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to generate {component_type.value}: {e}")
                    # Re-raise the exception to handle at higher level
                    raise e
            
            # Convert components to modules (each component becomes a module)
            for component_name, component_data in all_components.items():
                terraform_component = TerraformComponent(
                    name=component_name,
                    main_tf=component_data.get('main_tf', ''),
                    output_tf=component_data.get('outputs_tf', ''),
                    variables_tf=component_data.get('variables_tf', '')
                )
                state.modules.modules.append(terraform_component)
            
            # Generate environment configuration that uses all modules
            env_component = self.generate_environment_configuration(user_input_dict, all_components)
            state.environments.environments.append(env_component)
            
            logger.success(f"Generated {len(state.modules.modules)} modules and {len(state.environments.environments)} environments")
            state.code_generated = True
            state.next_node = const.CODE_VALIDATION
            
        except Exception as e:
            logger.error(f"Component-based generation failed: {e}")
            state.code_generated = False
            
        return state
    
    def extract_component_outputs(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Extract outputs from a generated component for use by dependent components"""
        
        # Parse the outputs.tf to extract key output values
        outputs_tf = component.get('outputs_tf', '')
        component_type = component.get('component_type', '')
        
        # Simple parsing - in production, you might want more sophisticated parsing
        outputs = {'component_type': component_type}
        
        # Extract output names from the terraform code
        import re
        output_matches = re.findall(r'output\s+"([^"]+)"', outputs_tf)
        for output_name in output_matches:
            # Create a placeholder reference for this output
            outputs[output_name] = f"module.{component_type}.{output_name}"
        
        return outputs
    
    def extract_user_input_dict(self, user_input:UserInput) -> Dict[str, Any]:
        """Extract user input into dict format for easier processing"""
        
        # Handle the user input format
        if hasattr(user_input, 'basic_info'):
            return {
                'project_name': user_input.basic_info.project_name,
                'description': user_input.basic_info.description,
                'application_type': user_input.basic_info.application_type,
                'detected_services': getattr(user_input, 'inferred_services', []),
                'security_level': getattr(user_input.basic_info.security_level, 'security_level', 'basic'),
                'region': getattr(user_input.basic_info, 'region', 'us-west-2')
            }
        else:
            return None
    
    def get_generation_order(self, user_input_dict: Dict[str, Any]) -> List[ComponentType]:
        """Determine component generation order based on dependencies"""
        
        base_order = [
            ComponentType.NETWORKING,    # Always first
            ComponentType.SECURITY,      # Depends on networking
        ]
        
        # Add database if detected
        detected_services = user_input_dict.get('detected_services', [])
        if any(db in detected_services for db in ['rds', 'dynamodb', 'database']):
            base_order.append(ComponentType.DATABASE)
        
        # Add compute for web applications
        if user_input_dict.get('application_type') in ['web_application', 'api_service']:
            base_order.append(ComponentType.COMPUTE)
        
        # Add monitoring for enhanced security or production
        if user_input_dict.get('security_level', '').lower() in ['enhanced', 'strict']:
            base_order.append(ComponentType.MONITORING)
            base_order.append(ComponentType.SECURITY_ENHANCED)
        
        return base_order
    
    def generate_single_component(self, component_type: ComponentType, user_input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a single component using specialized prompts"""
        
        # Get component-specific prompt
        prompt = self.get_component_prompt(component_type, user_input_dict)
        
        # Use structured output for component generation
        structured_llm = self.llm.with_structured_output(TerraformComponent)
        structured_prompt = PromptTemplate.from_template(prompt)
        
        chain = structured_prompt | structured_llm
        result = chain.invoke(user_input_dict)
        
        print(f"Output of {component_type} : {result}")
        
        return {
            'main_tf': result.main_tf,
            'variables_tf': result.variables_tf,
            'outputs_tf': result.output_tf,
            'component_type': component_type.value
        }
    
    def get_component_prompt(self, component_type: ComponentType, user_input: Dict[str, Any]) -> str:
        """Get the specific prompt for each component type"""
        dependencies = self.generated_outputs
        
        prompts = DecomposedTerraformPrompts()
        
        prompt_map = {
            ComponentType.NETWORKING: prompts.get_networking_prompt(user_input),
            ComponentType.SECURITY: prompts.get_security_groups_prompt(user_input, dependencies),
            ComponentType.DATABASE: prompts.get_database_prompt(user_input, dependencies),
            ComponentType.COMPUTE: prompts.get_compute_prompt(user_input, dependencies),
            ComponentType.MONITORING: prompts.get_monitoring_prompt(user_input, dependencies),
        }
        
        # Add security enhancement for Enhanced level
        if (component_type == ComponentType.SECURITY and 
            user_input.get('security_level') == 'Enhanced'):
            return prompts.get_security_enhancement_prompt(user_input, self.generated_outputs)
        
        prompt_func = prompt_map.get(component_type)
        if prompt_func:
            print(f"{component_type}: {prompt_func}")
            return prompt_func
        else:
            raise ValueError(f"No prompt defined for component type: {component_type}")
    
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
    

    def generate_environment_configuration(self, user_input_dict: Dict[str, Any], all_components: Dict[str, Any]) -> TerraformComponent:
        """Generate the main environment configuration that uses all modules"""
        
        project_name = user_input_dict.get('project_name', 'infrastructure')
        
        # Generate main.tf that references all modules
        main_tf = f'''# Main configuration for {project_name}
            # Generated environment: dev
            
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
            
            # Networking Module
            module "networking" {{
            source = "../../modules/networking"
            
            project_name = var.project_name
            environment = var.environment
            vpc_cidr = var.vpc_cidr
            availability_zones = var.availability_zones
            common_tags = var.common_tags
            }}
            
            # Security Module  
            module "security" {{
            source = "../../modules/security"
            
            vpc_id = module.networking.vpc_id
            project_name = var.project_name
            environment = var.environment
            common_tags = var.common_tags
            }}
        '''
        
        # Add database module if present
        if 'database' in all_components:
            main_tf += '''
            # Database Module
            module "database" {{
            source = "../../modules/database"
            
            db_subnet_group_name = module.networking.db_subnet_group_name
            database_security_group_id = module.security.database_sg_id
            project_name = var.project_name
            environment = var.environment
            common_tags = var.common_tags
            }}
        '''
        
        # Add compute module if present
        if 'compute' in all_components:
            main_tf += '''
            # Compute Module
            module "compute" {{
            source = "../../modules/compute"
            
            vpc_id = module.networking.vpc_id
            private_subnet_ids = module.networking.private_subnet_ids
            public_subnet_ids = module.networking.public_subnet_ids
            application_security_group_id = module.security.application_sg_id
            alb_security_group_id = module.security.alb_sg_id
            project_name = var.project_name
            environment = var.environment
            common_tags = var.common_tags
            }}
        '''
        
        # Add monitoring module if present
        if 'monitoring' in all_components:
            main_tf += '''
            # Monitoring Module  
            module "monitoring" {{
            source = "../../modules/monitoring"
            
            alb_arn = module.compute.alb_arn
            asg_name = module.compute.asg_name
            project_name = var.project_name
            environment = var.environment
            common_tags = var.common_tags
            }}
        '''
        
        # Generate variables.tf
        variables_tf = f'''# Variables for {project_name} infrastructure

            variable "project_name" {{
            description = "Name of the project"
            type        = string
            default     = "{project_name}"
            }}
            
            variable "environment" {{
            description = "Environment name"
            type        = string
            default     = "dev"
            }}
            
            variable "region" {{
            description = "AWS region"
            type        = string
            default     = "us-west-2"
            }}
            
            variable "vpc_cidr" {{
            description = "CIDR block for VPC"
            type        = string
            default     = "10.0.0.0/16"
            }}
            
            variable "availability_zones" {{
            description = "List of availability zones"
            type        = list(string)
            default     = ["us-west-2a", "us-west-2b"]
            }}
            
            variable "common_tags" {{
            description = "Common tags to apply to all resources"
            type        = map(string)
            default = {{
                Project     = "{project_name}"
                Environment = "dev"
                ManagedBy   = "Terraform"
            }}
            }}
        '''
        
        # Generate outputs.tf
        outputs_tf = f'''# Outputs for {project_name} infrastructure

            output "vpc_id" {{
            description = "ID of the VPC"
            value       = module.networking.vpc_id
            }}
        '''
        
        if 'compute' in all_components:
            outputs_tf += '''
            output "alb_dns_name" {{
            description = "DNS name of the Application Load Balancer"
            value       = module.compute.alb_dns_name
            }}
            
            output "application_url" {{
            description = "URL of the application"
            value       = "https://${{module.compute.alb_dns_name}}"
            }}
        '''
        
        return TerraformComponent(
            name="dev",
            main_tf=main_tf,
            variables_tf=variables_tf,
            output_tf=outputs_tf
        )