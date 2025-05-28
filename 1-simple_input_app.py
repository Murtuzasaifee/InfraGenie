from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
import streamlit as st

# Stage 1: Minimal Essential Input
class BasicProjectInput(BaseModel):
    """Essential information to get started"""
    
    project_name: str = Field(
        ..., 
        description="Name for your infrastructure project",
        min_length=3,
        max_length=50
    )
    
    description: str = Field(
        ...,
        description="What are you building? (e.g., 'E-commerce website with user accounts')",
        min_length=10,
        max_length=500
    )
    
    application_type: Literal[
        "static_website",
        "web_application", 
        "api_service",
        "microservices",
        "data_pipeline",
        "machine_learning",
        "custom"
    ] = Field(..., description="Choose the type that best matches your application")
    
    expected_users: Literal["few", "moderate", "many", "very_high"] = Field(
        default="moderate",
        description="Expected number of users/traffic"
    )
    
    region: Optional[str] = Field(
        default="us-west-2",
        description="AWS region (we'll suggest the best one if not specified)"
    )

# Stage 2: Intelligent Service Detection  
class ServiceRequirements(BaseModel):
    """AI-inferred and user-confirmed services"""
    
    needs_database: Optional[bool] = Field(
        None,
        description="Do you need to store data persistently?"
    )
    
    needs_file_storage: Optional[bool] = Field(
        None, 
        description="Do you need to store files/media?"
    )
    
    needs_load_balancer: Optional[bool] = Field(
        None,
        description="Do you expect high traffic requiring load balancing?"
    )
    
    needs_caching: Optional[bool] = Field(
        None,
        description="Do you need caching for performance?"
    )
    
    custom_services: List[str] = Field(
        default_factory=list,
        description="Any specific AWS services you know you need"
    )

# Stage 3: Smart Configuration
class IntelligentConfiguration(BaseModel):
    """Context-aware configuration that adapts to previous choices"""
    
    # Only populated if needs_database = True
    database_preference: Optional[Literal["simple", "scalable", "analytics"]] = Field(
        None,
        description="Simple=RDS, Scalable=DynamoDB, Analytics=Redshift/Athena"
    )
    
    # Only populated if high traffic expected
    scaling_preference: Optional[Literal["manual", "automatic"]] = Field(
        None,
        description="How should your application handle traffic spikes?"
    )
    
    # Only populated if security is a concern
    security_level: Literal["basic", "enhanced", "strict"] = Field(
        default="basic",
        description="Basic=standard security, Enhanced=WAF+monitoring, Strict=compliance-ready"
    )
    
    # Advanced users only
    advanced_options: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Override any auto-generated configurations"
    )

# Final Combined Input
class ImprovedUserInput(BaseModel):
    """Simplified, progressive user input"""
    
    # Stage 1: Always required
    basic_info: BasicProjectInput
    
    # Stage 2: AI-assisted with user confirmation  
    services: ServiceRequirements
    
    # Stage 3: Context-aware configuration
    configuration: IntelligentConfiguration
    
    # Generated/Inferred (not user input)
    inferred_services: Optional[List[str]] = Field(
        default_factory=list,
        description="Services auto-detected from requirements"
    )
    
    generated_config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Auto-generated technical configuration"
    )

# Template-based shortcuts for common patterns
class InfrastructureTemplate(BaseModel):
    """Pre-built templates for common use cases"""
    
    template_name: Literal[
        "simple_website",           # S3 + CloudFront
        "web_app_basic",           # EC2 + RDS + ALB  
        "web_app_scalable",        # ECS + RDS + ALB + Auto Scaling
        "api_microservice",        # Lambda + API Gateway + DynamoDB
        "data_processing",         # Lambda + S3 + EventBridge
        "ml_pipeline"              # SageMaker + S3 + Lambda
    ]
    
    customizations: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Modify template defaults"
    )

# Service-specific configurations (only shown when relevant)
class DatabaseConfig(BaseModel):
    engine: Optional[Literal["mysql", "postgres", "mongodb"]] = None
    size: Optional[Literal["small", "medium", "large"]] = Field(default="small")

class ComputeConfig(BaseModel):
    type: Optional[Literal["serverless", "containers", "virtual_machines"]] = None
    auto_scaling: bool = Field(default=True)

# AI Service Detection Helper
class ServiceDetector:
    """Analyze user description and suggest services"""
    
    @staticmethod
    def detect_services_from_description(description: str, app_type: str) -> List[str]:
        """Use simple keyword matching or LLM to detect needed services"""
        
        keywords_to_services = {
            "database": ["rds", "dynamodb"],
            "file upload": ["s3"],
            "user auth": ["cognito"],
            "email": ["ses"],
            "api": ["apigateway"],
            "website": ["cloudfront", "s3"],
            "high traffic": ["alb", "autoscaling"],
            "real-time": ["lambda", "eventbridge"]
        }
        
        detected = []
        description_lower = description.lower()
        
        for keyword, services in keywords_to_services.items():
            if keyword in description_lower:
                detected.extend(services)
                
        return list(set(detected))  # Remove duplicates

# UI Flow Helper
class ProgressiveInputCollector:
    """Manages the step-by-step input collection"""
    
    def __init__(self):
        self.current_step = 1
        self.collected_data = {}
    
    def get_next_questions(self, previous_answers: Dict) -> Dict[str, Any]:
        """Return next set of questions based on previous answers"""
        
        if self.current_step == 1:
            return self._get_basic_questions()
        elif self.current_step == 2:
            return self._get_service_questions(previous_answers)
        elif self.current_step == 3:
            return self._get_configuration_questions(previous_answers)
        
    def _get_basic_questions(self):
        return {
            "questions": [
                "What's your project name?",
                "Describe what you're building",
                "What type of application is this?",
                "How many users do you expect?"
            ],
            "suggested_templates": [
                "Simple Website - Just host a website with global CDN",
                "Web App - Full web application with database", 
                "API Service - REST API with database",
                "Custom - I'll specify exactly what I need"
            ]
        }
    
    def _get_service_questions(self, basic_info):
        # Only ask relevant questions based on app type
        questions = []
        
        if basic_info.get("application_type") != "static_website":
            questions.extend([
                "Do you need to store user data? (database)",
                "Will users upload files?",
            ])
            
        if basic_info.get("expected_users") in ["many", "very_high"]:
            questions.append("Do you need automatic scaling for traffic spikes?")
            
        return {"questions": questions}
    
    def _get_configuration_questions(self, previous_answers):
        # Fine-tune based on all previous answers
        return {"questions": ["Any specific requirements or constraints?"]}

# Usage Example in Streamlit
def load_improved_user_input_ui():
    """Streamlined UI with progressive disclosure"""
    
    st.subheader("Tell us about your project")
    
    # Use tabs for progressive disclosure
    tab1, tab2, tab3 = st.tabs(["📋 Project Basics", "🔧 Services", "⚙️ Configuration"])
    
    with tab1:
        project_name = st.text_input("Project Name", placeholder="my-awesome-app")
        
        description = st.text_area(
            "What are you building?", 
            placeholder="A web application where users can create accounts and share photos",
            help="Describe your application in plain English. We'll suggest the right AWS services."
        )
        
        app_type = st.selectbox(
            "Application Type",
            ["web_application", "api_service", "static_website", "data_pipeline", "custom"]
        )
        
        # Show template shortcuts
        if st.checkbox("Use a template instead?"):
            template = st.selectbox(
                "Choose Template",
                ["simple_website", "web_app_basic", "web_app_scalable", "api_microservice"]
            )
            st.info(f"Template '{template}' will auto-configure everything for you!")
    
    with tab2:
        st.write("Based on your description, we suggest these services:")
        
        # AI-detected services (simulated)
        detected = ServiceDetector.detect_services_from_description(description, app_type)
        
        for service in detected:
            st.checkbox(f"✅ {service}", value=True, help="Auto-detected from your description")
        
        # Optional additions
        st.write("Need anything else?")
        additional = st.multiselect("Additional Services", ["lambda", "sns", "sqs", "elasticache"])
    
    with tab3:
        st.write("Fine-tune your configuration")
        
        # Only show relevant options
        if "rds" in detected or "dynamodb" in detected:
            db_type = st.selectbox("Database Type", ["Simple (RDS)", "Scalable (DynamoDB)"])
        
        security_level = st.selectbox("Security Level", ["Basic", "Enhanced", "Strict"])
        
        # Advanced section (collapsed by default)
        with st.expander("Advanced Options (Optional)"):
            st.warning("⚠️ Only modify if you know what you're doing")
            custom_vpc = st.text_input("Custom VPC CIDR", placeholder="Leave empty for auto-configuration")

    return {
        "project_name": project_name,
        "description": description,
        "application_type": app_type,
        "detected_services": detected,
        "security_level": security_level
    }
    

if __name__ == "__main__":
    collected_data = load_improved_user_input_ui()
    print(collected_data)