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
            
            # First, run terraform init
            init_result = subprocess.run(
                ["terraform", "init", "-no-color"],
                cwd=self.base_directory,
                capture_output=True,
                text=True
            )
            
            # Run terraform validate with JSON output 
            validate_result = subprocess.run(
                ["terraform", "validate", "-json"],
                cwd=self.base_directory,
                capture_output=True,
                text=True
            )
            
            logger.debug(f"Terraform Init Response: {init_result}")
            logger.info("-----------------------------------------")
            logger.debug(f"Terraform Validate Response: {validate_result}")
            state.code_validation_json = validate_result.stdout
            
            # If init succeeded, proceed to validation results
            if init_result.returncode == 0:
                try:
                    validation_data = json.loads(validate_result.stdout)
                    logger.info(f"Terraform Validation Json: {validation_data}")
                    
                    if validation_data.get("valid", False):
                        state.is_code_valid = True
                        state.code_validation_feedback = "Terraform code is valid"
                    else:
                        # Extract ALL errors from diagnostics
                        diagnostics = validation_data.get("diagnostics", [])
                        if diagnostics:
                            error_messages = []
                            
                            for error in diagnostics:
                                # Build error message
                                message = error.get("summary", "Unknown error")
                                detail = error.get("detail", "")
                                if detail:
                                    message += f": {detail}"
                                
                                # Add location info if available
                                if "range" in error and "filename" in error["range"]:
                                    filename = error["range"]["filename"]
                                    start_line = error["range"].get("start", {}).get("line", "unknown")
                                    message += f" (File: {filename}, Line: {start_line})"
                                
                                error_messages.append(message)
                            
                            # Join all errors with newlines
                            all_errors = "\n".join(error_messages)
                            error_count = len(error_messages)
                            
                            state.is_code_valid = False
                            state.code_validation_feedback = f"Found {error_count} validation errors:\n\n{all_errors}"
                            logger.error(f"Terraform validation failed with {error_count} errors")
                            logger.error(f"Terraform validation feedback:\n{ state.code_validation_feedback}")
                            
                        else:
                            state.is_code_valid = False
                            state.code_validation_feedback = "Terraform validation failed with unspecified errors"
                            logger.error("Terraform validation failed with unspecified errors")
                            
                except json.JSONDecodeError:
                    # If JSON parsing fails
                    state.is_code_valid = False
                    state.code_validation_feedback = "Failed to parse Terraform validation output"
                    logger.error("Failed to parse Terraform validation output")
            else:
                # Init failed
                state.is_code_valid = False
                
                # Get clean error message from init failure
                error_message = "Terraform initialization failed"
                
                if "Error:" in init_result.stderr:
                    import re
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
    
    
    def create_terraform_plan(self, state: InfraGenieState):
        """
        Runs terraform plan and returns structured results in JSON format
        """
        
        try:
            # Change directory to where Terraform code is generated
            if not os.path.isdir(self.base_directory):
                raise Exception(f"Terraform code directory '{self.base_directory}' does not exist.")
                
            # First ensure terraform is initialized
            if not state.is_code_valid:
                raise Exception("Terraform code is not valid")
                
            # Run terraform plan with JSON output
            plan_result = subprocess.run(
                ["terraform", "plan", "-out=tfplan", "-no-color"],
                cwd=self.base_directory,
                capture_output=True,
                text=True
            )
            
            logger.debug(f"Terraform Plan: {plan_result}")
            logger.success(f"Terraform Plan Stdout: {plan_result.stdout}")
            logger.error(f"Terraform Plan stderr: {plan_result.stderr}")
            
            if plan_result.returncode == 0:
                state.is_plan_success = True
                
                # Convert the plan to JSON format for easy parsing
                json_plan_result = subprocess.run(
                    ["terraform", "show", "-json", "tfplan"],
                    cwd=self.base_directory,
                    capture_output=True,
                    text=True
                )
                logger.success(f"Terraform Plan Json: {json_plan_result}")
                state.plan_summary = "" ## TODO
                
            else:
                state.is_plan_success = False
                state.plan_error = plan_result.stderr
            
            return state
        
        except Exception as e:
            state.is_plan_success = False
            state.plan_error = str(e)
            raise Exception(f"Terraform Plan Error: {str(e)}")
    
    
    def terraform_plan_router(self, state: InfraGenieState):
        """
            Evaluates terraform plan
        """
        if state.is_plan_success:
            return "approved"
        else:
            return "feedback"
    