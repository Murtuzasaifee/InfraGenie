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

# Define the template with a simple prompt approach
terraform_template = """
You are a Terraform Expert. Based on the user's requirements, generate Terraform code for AWS Cloud infrastructure.

Requirements: {requirements}

Generate Terraform code for the following:

1. Create three environments: dev, stage, and prod
2. Create necessary infrastructure modules

Format your answer as valid JSON with the following structure:

{{
  "environments": [
    {{
      "name": "dev",
      "main_tf": "provider \\"aws\\" {{ ... }}",
      "output_tf": "output \\"vpc_id\\" {{ ... }}",
      "variables_tf": "variable \\"region\\" {{ ... }}"
    }}
  ],
  "modules": [
    {{
      "name": "vpc-module",
      "main_tf": "resource \\"aws_vpc\\" {{ ... }}",
      "output_tf": "output \\"vpc_id\\" {{ ... }}",
      "variables_tf": "variable \\"cidr_block\\" {{ ... }}"
    }}
  ]
}}

IMPORTANT: Only provide a valid JSON response, with no additional text or explanations. Ensure that your response can be parsed directly by json.loads().
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
    
    # Use regular invoke instead of structured output
    chain = prompt | llm
    response = chain.invoke({"requirements": state.user_requirements})
    
    try:
        # Extract JSON from the response using our helper function
        json_str = extract_json_from_text(response.content)
        print(f"Extracted JSON string: {json_str}")  # Print first 100 chars for debugging
        
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
    # Create base directory
    os.makedirs(base_dir, exist_ok=True)
    
    for env in state["environments"].environments:
        print(f"Environment: {env}")
        
        env_dir = os.path.join(base_dir, "environments", env.name)
        os.makedirs(env_dir, exist_ok=True)
        
        with open(os.path.join(env_dir, "main.tf"), "w") as f:
            f.write(env.main_tf)
        
        with open(os.path.join(env_dir, "output.tf"), "w") as f:
            f.write(env.output_tf)
        
        with open(os.path.join(env_dir, "variables.tf"), "w") as f:
            f.write(env.variables_tf)
    
    for module in state["modules"].modules:
        print(f"Module: {module}")
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