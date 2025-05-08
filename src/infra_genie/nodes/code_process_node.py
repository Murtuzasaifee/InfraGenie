from pydantic import BaseModel, Field
from loguru import logger
from src.infra_genie.state.infra_genie_state import InfraGenieState, TerraformComponent
from langchain_core.prompts import PromptTemplate
from src.infra_genie.utils import constants as const
import os
import shutil
    

class ProcessCodeNode:
    
    def __init__(self, llm):
        self.llm = llm
       
    def save_terraform_files(self, state: InfraGenieState):
        """Save the generated Terraform files to disk."""
        
        base_dir = "output/src"
        
        # Delete existing directories before saving
        if os.path.exists(base_dir):
            shutil.rmtree(base_dir)
        
        os.makedirs(base_dir, exist_ok=True)
        
        for env in state.environments.environments:
            env_dir = os.path.join(base_dir, "environments", env.name)
            os.makedirs(env_dir, exist_ok=True)
            
            with open(os.path.join(env_dir, "main.tf"), "w") as f:
                f.write(env.main_tf)
            
            with open(os.path.join(env_dir, "output.tf"), "w") as f:
                f.write(env.output_tf)
            
            with open(os.path.join(env_dir, "variables.tf"), "w") as f:
                f.write(env.variables_tf)
        
        for module in state.modules.modules:
            module_dir = os.path.join(base_dir, "modules", module.name)
            os.makedirs(module_dir, exist_ok=True)
            
            with open(os.path.join(module_dir, "main.tf"), "w") as f:
                f.write(module.main_tf)
            
            with open(os.path.join(module_dir, "output.tf"), "w") as f:
                f.write(module.output_tf)
            
            with open(os.path.join(module_dir, "variables.tf"), "w") as f:
                f.write(module.variables_tf)
        
        print(f"Terraform files have been saved to {base_dir}")
        
        return state
        