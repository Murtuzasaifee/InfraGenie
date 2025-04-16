from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv
import json
import re
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

load_dotenv()

def sanitize_ascii(s: str) -> str:
    # Remove any non-ASCII characters from the string
    return ''.join(c for c in s if ord(c) < 128)

api_key = os.environ["GROQ_API_KEY"]
model = "llama3-70b-8192"

sanitized_api_key = sanitize_ascii(api_key)
llm = ChatGroq(api_key=sanitized_api_key, model=model)

class TerraformFile(BaseModel):
    path: str
    content: str
    
class TerraformComponent(BaseModel):
    name: str = Field(..., description="The name of the component.")
    main_tf: str = Field(..., description="The main.tf file content.")
    output_tf: str = Field(..., description="The output.tf file content.")
    variables_tf: str = Field(..., description="The variables.tf file content.")
    
class EnvironmentList(BaseModel):
    environments: List[TerraformComponent] = []

class ModuleList(BaseModel):
    modules: List[TerraformComponent] = []

class TerraformState(BaseModel):
    """State for our Terraform code generation agent."""
    modules: ModuleList = Field(default_factory=ModuleList)
    environments: EnvironmentList = Field(default_factory=EnvironmentList)
    user_requirements: str = ""

# Define the template
terraform_template = """
You are a Terraform Expert who writes production-grade, syntactically valid, and best-practice Terraform code for AWS. Based on the user's requirements provided below, generate complete Terraform code for AWS infrastructure. Make sure to include all necessary provider blocks, resource definitions, variable declarations, and outputs. The generated code should be executable with Terraform and follow HCL syntax.

Requirements: {requirements}

Instructions:
1. Generate code for three environments: dev, stage, and prod. For each environment, create:
   - A main.tf that includes the AWS provider configuration and resource definitions (e.g., VPC, subnets, security groups).
   - An output.tf that defines outputs for resource identifiers.
   - A variables.tf that declares any required variables.
2. Generate code for infrastructure modules. For example, create a "vpc-module" that includes:
   - A main.tf with resource definitions for a VPC.
   - An output.tf to output the VPC ID.
   - A variables.tf with variable declarations (e.g., for CIDR blocks).
3. Use proper resource naming conventions, include realistic values and valid HCL code. Do not use generic placeholders like "..."—include sample configurations that satisfy the requirement.
4. Ensure the AWS provider is configured correctly with at least a region setting.
5. Echo the user requirements in the final JSON output.

Return your answer as a valid JSON object with the exact following structure and no additional text:

{{
  "environments": [
    {{
      "name": "dev",
      "main_tf": "[Terraform code for dev main.tf]",
      "output_tf": "[Terraform code for dev output.tf]",
      "variables_tf": "[Terraform code for dev variables.tf]"
    }},
    {{
      "name": "stage",
      "main_tf": "[Terraform code for stage main.tf]",
      "output_tf": "[Terraform code for stage output.tf]",
      "variables_tf": "[Terraform code for stage variables.tf]"
    }},
    {{
      "name": "prod",
      "main_tf": "[Terraform code for prod main.tf]",
      "output_tf": "[Terraform code for prod output.tf]",
      "variables_tf": "[Terraform code for prod variables.tf]"
    }}
  ],
  "modules": [
    {{
      "name": "vpc-module",
      "main_tf": "[Terraform code for vpc module main.tf]",
      "output_tf": "[Terraform code for vpc module output.tf]",
      "variables_tf": "[Terraform code for vpc module variables.tf]"
    }}
  ],
  "user_requirements": "{requirements}"
}}

IMPORTANT:
- Only output valid JSON that exactly follows the schema above. Do not include any additional text, markdown formatting, or code block markers.
- Ensure that all Terraform code is syntactically valid and could be used in a Terraform project with minimal modifications.
"""

def process_request(state: TerraformState):
    """Process the user's request and update the state."""
    return state

def extract_json_from_text(text):
    """Extract JSON from text using multiple methods."""
    # Try to find JSON in code blocks
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if json_match:
        return json_match.group(1).strip()
    
    # Try to find JSON between curly braces
    json_match = re.search(r'(\{[\s\S]*\})', text)
    if json_match:
        return json_match.group(1).strip()
    
    # Return the whole text as a last resort
    return text.strip()

def generate_terraform_code(state: TerraformState):
    """Generate Terraform code based on requirements in state."""
    
    prompt = PromptTemplate.from_template(terraform_template)
    
    chain = prompt | llm
    response = chain.invoke({"requirements": state.user_requirements})
    
    try:
        # Extract JSON from the response using our helper function
        json_str = extract_json_from_text(response.content)
        print(f"Extracted JSON string: {json_str}")
        
        # Parse the JSON response
        data = json.loads(json_str)
        
        # Update environments
        for env_data in data.get("environments", []):
            component = TerraformComponent(
                name=env_data.get("name", ""),
                main_tf=env_data.get("main_tf", ""),
                output_tf=env_data.get("output_tf", ""),
                variables_tf=env_data.get("variables_tf", "")
            )
            state.environments.environments.append(component)
        
        # Update modules
        for module_data in data.get("modules", []):
            component = TerraformComponent(
                name=module_data.get("name", ""),
                main_tf=module_data.get("main_tf", ""),
                output_tf=module_data.get("output_tf", ""),
                variables_tf=module_data.get("variables_tf", "")
            )
            state.modules.modules.append(component)
            
    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        print(f"Response content: {response.content}")
    
    return state

# Define the graph
graph = StateGraph(TerraformState)

# Add nodes
graph.add_node("process_request", process_request)
graph.add_node("generate_terraform_code", generate_terraform_code)

# Add edges
graph.add_edge(START, "process_request")
graph.add_edge("process_request", "generate_terraform_code")
graph.add_edge("generate_terraform_code", END)

# Compile the graph
terraform_app = graph.compile()

# Function to save generated Terraform files
def save_terraform_files(state: TerraformState, base_dir: str = "output/src"):
    """Save the generated Terraform files to disk."""
    
    os.makedirs(base_dir, exist_ok=True)
    
    for env in state["environments"].environments:
        
        env_dir = os.path.join(base_dir, "environments", env.name)
        os.makedirs(env_dir, exist_ok=True)
        
        with open(os.path.join(env_dir, "main.tf"), "w") as f:
            f.write(env.main_tf)
        
        with open(os.path.join(env_dir, "output.tf"), "w") as f:
            f.write(env.output_tf)
        
        with open(os.path.join(env_dir, "variables.tf"), "w") as f:
            f.write(env.variables_tf)
    
    for module in state["modules"].modules:
       
        module_dir = os.path.join(base_dir, "modules", module.name)
        os.makedirs(module_dir, exist_ok=True)
        
        with open(os.path.join(module_dir, "main.tf"), "w") as f:
            f.write(module.main_tf)
        
        with open(os.path.join(module_dir, "output.tf"), "w") as f:
            f.write(module.output_tf)
        
        with open(os.path.join(module_dir, "variables.tf"), "w") as f:
            f.write(module.variables_tf)
    
    print(f"Terraform files have been saved to {base_dir}")

# Example usage
result = terraform_app.invoke({
    "user_requirements": "Create a VPC with public and private subnets in AWS with appropriate security groups"
})


# Save files to disk
save_terraform_files(result)