from pydantic import BaseModel, Field
from typing import Any, Dict, Literal, Optional
import json
import src.infra_genie.utils.constants as const
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator

    
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

# Added for structured output parser
class TerraformOutput(BaseModel):
    environments: List[TerraformComponent]
    modules: List[TerraformComponent]
    
class BasicInfo(BaseModel):
    project_name: str
    description: str
    application_type: str
    detected_services: List[str]
    security_level: str
    
class UserInput(BaseModel):
    
    # Stage 1: Always required
    basic_info: BasicInfo
    
class InfraGenieState(BaseModel):
   
    """State for our InfraGenie agent."""
    
    ## User Input
    user_input: Optional[UserInput] = None
    
    next_node: str = const.PROJECT_INITILIZATION
    modules: ModuleList = Field(default_factory=ModuleList)
    environments: EnvironmentList = Field(default_factory=EnvironmentList)
    
    code_generated: bool = False
    is_code_valid: bool = False
    code_validation_json: Optional[str] = None
    code_validation_feedback: Optional[str] = None
    code_validation_user_feedback: Optional[str] = None
    code_review_status: Optional[str] = None

    
    
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        # Check if the object is any kind of Pydantic model
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        
        return super().default(obj)
    

    