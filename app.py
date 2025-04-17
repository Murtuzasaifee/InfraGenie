from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
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

api_key = os.environ["GEMINI_API_KEY"]
model = "gemini-2.0-flash"

sanitized_api_key = sanitize_ascii(api_key)
llm = ChatGoogleGenerativeAI(api_key=sanitized_api_key, model=model)

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

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        # Check if the object is any kind of Pydantic model
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        # Or check for specific classes if needed
        # if isinstance(obj, UserStories) or isinstance(obj, DesignDocument):
        #     return obj.model_dump()
        return super().default(obj)

# Prompt template
terraform_template = """
You are a senior AWS Solutions Architect and Terraform Expert responsible for creating enterprise-grade, 
production-ready infrastructure as code. Your task is to generate complete, 
executable Terraform code that follows HashiCorp's recommended practices and AWS Well-Architected Framework principles.

Requirements: {requirements}

SPECIFICATIONS:
1. ARCHITECTURE:
   - Follow a modular design pattern with reusable components
   - Implement proper networking segregation with public/private subnets
   - Include appropriate security controls (NACLs, Security Groups)
   - Design for high availability across multiple AZs
   - Implement proper tagging strategy (environment, owner, cost center)

2. CODE QUALITY REQUIREMENTS:
   - Use proper Terraform state management with remote state configuration
   - Implement conditional logic for environment-specific configurations
   - Add descriptive comments explaining key design decisions
   - Use proper variable typing and constraints
   - Implement input validation for critical variables
   - Use locals for repeated or computed values
   - Follow proper naming conventions (snake_case)
   - Include proper error handling and lifecycle management

3. SECURITY REQUIREMENTS:
   - Implement least privilege IAM policies
   - Enable proper encryption for data at rest and in transit
   - Configure security groups with specific CIDR blocks (no 0.0.0.0/0 except for public-facing LBs)
   - Set up proper logging and auditing
   - Include security headers and best practices

Generate Terraform code for three environments:
- dev: lower capacity, minimal redundancy
- stage: medium capacity, good redundancy
- prod: high capacity, maximum redundancy and proper auto-scaling

IMPORTANT IMPLEMENTATION DETAILS:
- Use Terraform AWS provider version 5.0.0 or later
- Include proper provider configuration with version constraints
- Define data sources for dynamic lookup of AMIs, AZs, etc.
- Use count or for_each for resource repetition
- Include proper error handling with preconditions/postconditions
- Set up proper dependency management

Return your answer as a valid JSON object with the following structure and no additional text:

{{
  "environments": [
    {{
      "name": "dev",
      "main_tf": "[Complete Terraform code for dev main.tf]",
      "output_tf": "[Complete Terraform code for dev output.tf]",
      "variables_tf": "[Complete Terraform code for dev variables.tf]"
    }},
    {{
      "name": "stage",
      "main_tf": "[Complete Terraform code for stage main.tf]",
      "output_tf": "[Complete Terraform code for stage output.tf]",
      "variables_tf": "[Complete Terraform code for stage variables.tf]"
    }},
    {{
      "name": "prod",
      "main_tf": "[Complete Terraform code for prod main.tf]",
      "output_tf": "[Complete Terraform code for prod output.tf]",
      "variables_tf": "[Complete Terraform code for prod variables.tf]"
    }}
  ],
  "modules": [
    {{
      "name": "vpc-module",
      "main_tf": "[Complete Terraform code for vpc module main.tf]",
      "output_tf": "[Complete Terraform code for vpc module output.tf]",
      "variables_tf": "[Complete Terraform code for vpc module variables.tf]"
    }},
    {{
      "name": "security-module",
      "main_tf": "[Complete Terraform code for security module main.tf]",
      "output_tf": "[Complete Terraform code for security module output.tf]",
      "variables_tf": "[Complete Terraform code for security module variables.tf]"
    }}
  ],
  "user_requirements": "{requirements}"
}}

Your code must be directly deployable to AWS without modifications. Avoid using placeholders or TODOs - provide working values for all required fields. Include proper module references and dependency management.
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
    
    state_str = json.dumps(state, cls=CustomEncoder)
    print(f"State: {state_str}")
    
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