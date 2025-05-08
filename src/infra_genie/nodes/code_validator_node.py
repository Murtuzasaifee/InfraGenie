from src.infra_genie.state.infra_genie_state import InfraGenieState
from src.infra_genie.utils import constants as const
import os
import subprocess
from loguru import logger

class CodeValidatorNode:
    
    def __init__(self, llm, base_directory="output/src/environments/dev"):
        self.base_directory = base_directory
        self.llm = llm
        
    def validate_terraform_code(self, state: InfraGenieState):
        """
            Validates the generated Terraform code
        """
        
        try:
            # Change directory to where Terraform code is generated
            if not os.path.isdir(self.base_directory):
                raise Exception(f"Terraform code directory '{self.base_directory}' does not exist.")

            # Run 'terraform init'
            result = subprocess.run(
                ["terraform", "init"],
                cwd=self.base_directory,
                capture_output=True,
                text=True
            )

            logger.debug(f"Terraform Validation Response: {result}")
            
            if result.returncode != 0:
                raise Exception(f"Terraform init failed:\n{result.stderr}")
            
            state.next_node = const.SAVE_CODE       
            return state
        
        except Exception as e:
            raise Exception(f"Terraform Validation Error: {str(e)}")
        
    
    
    