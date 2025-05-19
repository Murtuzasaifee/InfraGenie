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
            state.code_validation_json = validate_result.stdout
            
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
                # Run validation first if not already done
                state = self.validate_terraform_code(state)
                
            # Run terraform plan with JSON output
            plan_result = subprocess.run(
                ["terraform", "plan", "-out=tfplan", "-no-color"],
                cwd=self.base_directory,
                capture_output=True,
                text=True
            )
            
            logger.debug(f"Terraform Plan: {plan_result}")
            
            # Check if plan was created successfully
            if plan_result.returncode != 0:
                state.plan_success = False
                state.plan_error = "Failed to create Terraform plan"
                
                # Simple error extraction without complex parsing
                if "Error:" in plan_result.stderr:
                    import re
                    error_match = re.search(r'Error: ([^\n]+)', plan_result.stderr)
                    if error_match:
                        error_message = f"Terraform plan failed: {error_match.group(1).strip()}"
                        state.plan_error = error_message
                
                raise Exception(state.plan_error)
                
            # Convert the plan to JSON format for easy parsing
            json_plan_result = subprocess.run(
                ["terraform", "show", "-json", "tfplan"],
                cwd=self.base_directory,
                capture_output=True,
                text=True
            )
            
            logger.debug(f"Terraform Plan Json: {json_plan_result}")
            
            if json_plan_result.returncode != 0:
                state.plan_success = False
                state.plan_error = "Failed to convert Terraform plan to JSON format"
                raise Exception(state.plan_error)
                
            try:
                plan_json = json.loads(json_plan_result.stdout)
                
                # Process the plan data into a more concise format for the LLM
                simplified_plan = {
                    "success": True,
                    "resource_changes": [],
                    "output_changes": []
                }
                
                # Extract resource changes
                if "resource_changes" in plan_json:
                    for resource in plan_json["resource_changes"]:
                        change = {
                            "address": resource.get("address"),
                            "action": resource.get("change", {}).get("actions", []),
                            "type": resource.get("type", "")
                        }
                        simplified_plan["resource_changes"].append(change)
                
                # Extract output changes if present
                if "output_changes" in plan_json:
                    for output_name, output_change in plan_json["output_changes"].items():
                        change = {
                            "name": output_name,
                            "action": output_change.get("actions", [])
                        }
                        simplified_plan["output_changes"].append(change)
                
                # Summary statistics
                simplified_plan["summary"] = {
                    "add": len([r for r in simplified_plan["resource_changes"] if "create" in r["action"]]),
                    "change": len([r for r in simplified_plan["resource_changes"] if "update" in r["action"]]),
                    "destroy": len([r for r in simplified_plan["resource_changes"] if "delete" in r["action"]])
                }
                
                # Store both full and simplified plans
                # state.plan_data = plan_json
                # state.plan_summary = simplified_plan
                # state.plan_success = True
                logger.debug(f"plan_json : {plan_json}")
                logger.debug(f"simplified_plan : {simplified_plan}")
                
                return state
                
            except json.JSONDecodeError:
                state.plan_success = False
                state.plan_error = "Failed to parse Terraform plan JSON output"
                raise Exception(state.plan_error)
        
        except Exception as e:
            state.plan_success = False
            state.plan_error = str(e)
            raise Exception(f"Terraform Plan Error: {str(e)}")
    
    
    def terraform_plan_router(self, state: InfraGenieState):
        """
            Evaluates terraform plan
        """
        # return state.get("is_terraform_plan_valid", False)  # default to False
        pass
    