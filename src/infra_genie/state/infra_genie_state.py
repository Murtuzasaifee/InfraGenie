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


class UserInput(BaseModel):
    """User input for the Terraform code generation"""
    
    services: List[str] = Field(..., 
        description="List of AWS services to deploy (e.g., ['ec2', 's3', 'rds', 'lambda']).")
    
    region: str = Field(..., 
        description="AWS region where services will be deployed (e.g., 'us-west-2').")
    
    vpc_cidr: str = Field(..., 
        description="CIDR block for the VPC (e.g., '10.0.0.0/16').")
    
    subnet_configuration: Dict[str, List[str]] = Field(
        default_factory=lambda: {"public": [], "private": [], "database": []},
        description="CIDR blocks for subnets by type (public, private, database).")
    
    availability_zones: List[str] = Field(...,
        description="List of availability zones to use (e.g., ['us-west-2a', 'us-west-2b']).")
    
    compute_type: str = Field(..., 
        description="Type of compute to use (e.g., 'ec2', 'ecs', 'lambda').")
    
    database_type: Optional[str] = Field(None, 
        description="Type of database to use if needed (e.g., 'mysql', 'postgres', 'dynamodb').")
    
    is_multi_az: bool = Field(..., 
        description="Whether to deploy across multiple availability zones for high availability.")
    
    is_serverless: bool = Field(..., 
        description="Whether to use serverless architecture where applicable.")
    
    enable_logging: bool = Field(True, 
        description="Whether to enable CloudWatch logging for services.")
    
    enable_monitoring: bool = Field(True, 
        description="Whether to enable CloudWatch monitoring for services.")
    
    load_balancer_type: Optional[Literal["ALB", "NLB", "CLB"]] = Field(None,
        description="Type of load balancer to deploy if needed.")
    
    enable_waf: bool = Field(False, 
        description="Whether to enable AWS WAF for web applications.")
    
    tags: Dict[str, str] = Field(
        default_factory=lambda: {
            "Environment": "dev",
            "ManagedBy": "Terraform",
            "Owner": "DevOps"
        },
        description="Resource tags.")
    
    # Free-form requirements
    requirements: str = Field(..., 
        description="Additional requirements in natural language.")
    
    # Advanced configuration
    custom_parameters: Dict[str, Union[str, int, bool, List, Dict]] = Field(
        default_factory=dict,
        description="Additional custom parameters for advanced configurations.")
    
    # Validators
    @field_validator('vpc_cidr')
    def validate_cidr(cls, v):
        import ipaddress
        try:
            ipaddress.IPv4Network(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid CIDR block format: {v}")
    
    @field_validator('region')
    def validate_region(cls, v):
        valid_regions = [
            "us-east-1", "us-east-2", "us-west-1", "us-west-2",
            "af-south-1",
            "ap-east-1", "ap-south-1", "ap-south-2",
            "ap-southeast-1", "ap-southeast-2", "ap-southeast-3", "ap-southeast-4",
            "ap-northeast-1", "ap-northeast-2", "ap-northeast-3",
            "ca-central-1", "ca-west-1",
            "eu-central-1", "eu-central-2",
            "eu-west-1", "eu-west-2", "eu-west-3",
            "eu-north-1", "eu-south-1", "eu-south-2",
            "me-south-1", "me-central-1",
            "sa-east-1"
        ]
        if v not in valid_regions:
            raise ValueError(f"Invalid AWS region: {v}. Must be one of {valid_regions}")
        return v


class InfraGenieState(BaseModel):
   
    """State for our InfraGenie agent."""
    
    project_name: str
    next_node: str = const.PROJECT_INITILIZATION
    modules: ModuleList = Field(default_factory=ModuleList)
    environments: EnvironmentList = Field(default_factory=EnvironmentList)
    user_input: Optional[UserInput] = None
    
    code_generated: bool = False
    is_code_valid: bool = False
    code_validation_json: Optional[str] = None
    code_validation_feedback: Optional[str] = None
    is_terraform_plan_valid: bool = False
    terraform_plan_validation_feedback: Optional[str] = None
    
    plan_data: Optional[str] = None
    plan_summary: Optional[str] = None
    plan_success: bool = False
    plan_error: Optional[str] = None
    
    
   
    
    
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        # Check if the object is any kind of Pydantic model
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        
        return super().default(obj)
    

    