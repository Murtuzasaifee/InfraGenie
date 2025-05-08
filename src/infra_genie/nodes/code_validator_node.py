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
            
            # Process the result to extract just the important message
            if result.returncode == 0:
                # Success case - extract just the success message
                success_message = "Terraform has been successfully initialized!"
                state.code_validation_error = success_message
                state.is_code_valid = True
            else:
                # Error case - extract just the error message
                error_lines = result.stderr.strip().split("\n")
                if error_lines:
                    # Often the last line contains the most relevant error
                    error_message = error_lines[-1]
                else:
                    error_message = "Unknown terraform init error"
                    
                state.is_code_valid = False
                state.code_validation_error = error_message
                logger.info(f"Terraform init failed: {error_message}")
            
            return state
        
        except Exception as e:
            state.is_code_valid = False
            state.code_validation_error = str(e)
            logger.info(f"Terraform Validation Error: {str(e)}")
        
        
    def code_validation_router(self, state: InfraGenieState):
        """
            Evaluates Code validation status.
        """
        if state.is_code_valid:
            return "approved"
        else:
            return "feedback"
    
    
    def creat_terraform_plan(self, state: InfraGenieState):
        """
            Create Terraform Plan for the generated code
        """
        pass
        # try:
        #     # Change directory to where Terraform code is generated
        #     if not os.path.isdir(self.base_directory):
        #         raise Exception(f"Terraform code directory '{self.base_directory}' does not exist.")

        #     # Run 'terraform plan'
        #     result = subprocess.run(
        #         ["terraform", "plan"],
        #         cwd=self.base_directory,
        #         capture_output=True,
        #         text=True
        #     )

        #     logger.debug(f"Terraform Plan Response: {result}")
            
        #     if result.returncode != 0:
        #         state.is_terraform_plan_valid = False
        #         state.terraform_plan_validation_error = result.stderr
        #         raise Exception(f"Terraform plan failed:\n{result.stderr}")
            
        #     state.is_terraform_plan_valid = True   
        #     return state
        
        # except Exception as e:
        #     state.is_terraform_plan_valid = False
        #     raise Exception(f"Terraform Plan Error: {str(e)}")
    
    
    def terraform_plan_router(self, state: InfraGenieState):
        """
            Evaluates terraform plan
        """
        # return state.get("is_terraform_plan_valid", False)  # default to False
        pass
    