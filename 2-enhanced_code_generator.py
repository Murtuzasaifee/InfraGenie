from loguru import logger
from src.infra_genie.state.infra_genie_state import InfraGenieState, TerraformOutput, TerraformComponent
from langchain_core.prompts import PromptTemplate
from src.infra_genie.utils import constants as const
from typing import Dict, Any, List, Optional
from enum import Enum
import json

class ComponentType(Enum):
    NETWORKING = "networking"
    SECURITY = "security"
    DATABASE = "database"  
    COMPUTE = "compute"
    MONITORING = "monitoring"
    SECURITY_ENHANCED = "security_enhanced"

class EnhancedCodeGeneratorNode:
    """Enhanced code generator with decomposed, component-based prompts"""
    
    def __init__(self, llm):
        self.llm = llm
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
            user_input_dict = self._extract_user_input_dict(state.user_input)
            
            # Determine component generation order
            self.component_order = self._get_generation_order(user_input_dict)
            logger.info(f"Generation order: {[c.value for c in self.component_order]}")
            
            # Clear existing state
            state.environments.environments.clear()
            state.modules.modules.clear()
            
            # Generate each component
            all_components = {}
            for component_type in self.component_order:
                logger.info(f"Generating {component_type.value} component...")
                
                try:
                    component = self._generate_single_component(component_type, user_input_dict)
                    all_components[component_type.value] = component
                    
                    # Store outputs for dependency resolution
                    self.generated_outputs[component_type.value] = self._extract_component_outputs(component)
                    
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
            env_component = self._generate_environment_configuration(user_input_dict, all_components)
            state.environments.environments.append(env_component)
            
            logger.success(f"Generated {len(state.modules.modules)} modules and {len(state.environments.environments)} environments")
            state.code_generated = True
            state.next_node = const.CODE_VALIDATION
            
        except Exception as e:
            logger.error(f"Component-based generation failed: {e}")
            state.code_generated = False
            state.next_node = const.FALLBACK_GENERATION
            
        return state
    
    def _extract_user_input_dict(self, user_input) -> Dict[str, Any]:
        """Extract user input into dict format for easier processing"""
        
        # Handle the new simplified input format
        if hasattr(user_input, 'basic_info'):
            # New format with progressive disclosure
            return {
                'project_name': user_input.basic_info.project_name,
                'description': user_input.basic_info.description,
                'application_type': user_input.basic_info.application_type,
                'detected_services': getattr(user_input, 'inferred_services', []),
                'security_level': getattr(user_input.configuration, 'security_level', 'basic'),
                'region': getattr(user_input.basic_info, 'region', 'us-west-2')
            }
        else:
            # Handle direct dict input from your example
            if isinstance(user_input, dict):
                return user_input
            
            # Handle existing UserInput model
            return {
                'project_name': getattr(user_input, 'project_name', 'unknown'),
                'description': getattr(user_input, 'requirements', ''),
                'application_type': 'web_application',
                'detected_services': getattr(user_input, 'services', []),
                'security_level': 'basic',
                'region': getattr(user_input, 'region', 'us-west-2')
            }
    
    def _get_generation_order(self, user_input_dict: Dict[str, Any]) -> List[ComponentType]:
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
    
    def _generate_single_component(self, component_type: ComponentType, user_input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a single component using specialized prompts"""
        
        # Get component-specific prompt
        prompt = self._get_component_prompt(component_type, user_input_dict)
        
        # Use structured output for component generation
        structured_llm = self.llm.with_structured_output(TerraformComponent)
        structured_prompt = PromptTemplate.from_template(prompt)
        
        chain = structured_prompt | structured_llm
        result = chain.invoke(user_input_dict)
        
        return {
            'main_tf': result.main_tf,
            'variables_tf': result.variables_tf,
            'outputs_tf': result.output_tf,
            'component_type': component_type.value
        }
    
    def _get_component_prompt(self, component_type: ComponentType, user_input_dict: Dict[str, Any]) -> str:
        """Get specialized prompt for each component type using decomposed prompts"""
        
        # Import and initialize the decomposed prompts
        from src.infra_genie.nodes.decomposed_terraform_prompts import DecomposedTerraformPrompts
        
        prompts = DecomposedTerraformPrompts()
        
        # Map component types to prompt methods
        prompt_map = {
            ComponentType.NETWORKING: prompts.get_networking_prompt,
            ComponentType.SECURITY: prompts.get_security_groups_prompt,
            ComponentType.DATABASE: prompts.get_database_prompt,
            ComponentType.COMPUTE: prompts.get_compute_prompt,
            ComponentType.MONITORING: prompts.get_monitoring_prompt,
            ComponentType.SECURITY_ENHANCED: prompts.get_security_enhancement_prompt,
        }
        
        prompt_func = prompt_map.get(component_type)
        if prompt_func:
            return prompt_func(user_input_dict, self.generated_outputs)
        else:
            raise ValueError(f"No prompt defined for component type: {component_type}")