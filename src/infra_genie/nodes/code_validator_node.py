from src.infra_genie.state.infra_genie_state import InfraGenieState
from src.infra_genie.utils import constants as const
import os
import subprocess
from loguru import logger
import json

class CodeValidatorNode:
    
    def __init__(self, llm, base_directory="output/src/environments/dev"):
        self.base_directory = base_directory
        self.llm = llm
        
            
    def validate_terraform_code(self, state: InfraGenieState):
        """
        Validates the generated Terraform code using Terraform's JSON output format
        """
        
        try:
            # Change directory to where Terraform code is generated
            if not os.path.isdir(self.base_directory):
                raise Exception(f"Terraform code directory '{self.base_directory}' does not exist.")
          
            
            # First, we need to run init (but we don't need to parse its complex output)
            init_result = subprocess.run(
                ["terraform", "init", "-no-color"],
                cwd=self.base_directory,
                capture_output=True,
                text=True
            )
            
              # Run 'terraform validate' with JSON output 
            validate_result = subprocess.run(
                ["terraform", "validate", "-json"],
                cwd=self.base_directory,
                capture_output=True,
                text=True
            )
            
            logger.debug(f"Terraform Init Response: {init_result}")
            logger.debug("-----------------------------------------")
            logger.debug(f"Terraform Validate Response: {validate_result}")
            
            # If init succeeded, proceed to validation results
            if init_result.returncode == 0:
                # Parse the JSON output from validate
                
                try:
                    validation_data = json.loads(validate_result.stdout)
                    logger.debug(f"Terraform Validation Json: {validation_data}")
                    
                    if validation_data.get("valid", False):
                        state.is_code_valid = True
                        state.code_validation_feedback = "Terraform code is valid"
                    else:
                        # Extract clean error messages from the structured data
                        diagnostics = validation_data.get("diagnostics", [])
                        if diagnostics:
                            # Get the first error with its location
                            error = diagnostics[0]
                            message = error.get("summary", "Unknown error")
                            message += f": {error.get("detail", "Unknown error")}"
                            
                            # Add location info if available
                            if "range" in error and "filename" in error["range"]:
                                filename = error["range"]["filename"]
                                start_line = error["range"].get("start", {}).get("line", 0)
                                message += f" in {filename} (line {start_line})"
                                
                            state.is_code_valid = False
                            state.code_validation_feedback = message
                            logger.error(f"Terraform validation failed: {message}")
                            
                        else:
                            state.is_code_valid = False
                            state.code_validation_feedback = "Terraform validation failed with unspecified errors"
                            logger.error("Terraform validation failed with unspecified errors")
                            
                except json.JSONDecodeError:
                    # If JSON parsing fails, we have a different kind of error
                    state.is_code_valid = False
                    state.code_validation_feedback = "Failed to parse Terraform validation output"
                    logger.error("Failed to parse Terraform validation output")
            else:
                # Init failed, provide a clean error message
                state.is_code_valid = False
                
                # Get a clean, LLM-friendly error message
                error_message = "Terraform initialization failed"
                
                # Add the most relevant part of the error output
                if "Error:" in init_result.stderr:
                    import re
                    # Find the main error message after "Error:"
                    error_match = re.search(r'Error: ([^\n]+)', init_result.stderr)
                    if error_match:
                        error_message += f": {error_match.group(1).strip()}"
                
                state.code_validation_feedback = error_message
                logger.error(error_message)
            
            return state
        
        except Exception as e:
            state.is_code_valid = False
            state.code_validation_feedback = str(e)
            logger.error(f"Terraform Validation Error: {str(e)}")
        
        
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
    