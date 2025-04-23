import streamlit as st
from src.infra_genie.LLMS.groqllm import GroqLLM
from src.infra_genie.LLMS.geminillm import GeminiLLM
from src.infra_genie.LLMS.openai_llm import OpenAILLM
from src.infra_genie.LLMS.mistral_llm import MistralLLM
from src.infra_genie.graph.graph_builder import GraphBuilder
from src.infra_genie.ui.uiconfigfile import Config
import src.infra_genie.utils.constants as const
from src.infra_genie.graph.graph_executor import GraphExecutor
import os
from loguru import logger
import json
from pathlib import Path
from src.infra_genie.state.infra_genie_state import UserInput

def initialize_session():
    st.session_state.stage = const.PROJECT_INITILIZATION
    st.session_state.project_name = ""
    st.session_state.requirements = ""
    st.session_state.task_id = ""
    st.session_state.state = {}
    st.session_state.form_data = {}


def load_sidebar_ui(config: Config):
    user_controls = {}
    
    with st.sidebar:
        # Get options from config
        llm_options = config.get_llm_options()

        # LLM selection
        user_controls["selected_llm"] = st.selectbox("Select LLM", llm_options)

        if user_controls["selected_llm"] == 'Groq':
            # Model selection
            model_options = config.get_groq_model_options()
            user_controls["selected_groq_model"] = st.selectbox("Select Model", model_options)
            # API key input
            os.environ["GROQ_API_KEY"] = user_controls["GROQ_API_KEY"] = st.session_state["GROQ_API_KEY"] = st.text_input("API Key",
                                                                                                    type="password",
                                                                                                    value=os.getenv("GROQ_API_KEY", ""))
            # Validate API key
            if not user_controls["GROQ_API_KEY"]:
                st.warning("⚠️ Please enter your GROQ API key to proceed. Don't have? refer : https://console.groq.com/keys ")
                
        
        if user_controls["selected_llm"] == 'Mistral':
            # Model selection
            model_options = config.get_mistral_model_options()
            user_controls["selected_mistral_model"] = st.selectbox("Select Model", model_options)
            # API key input
            os.environ["MISTRAL_API_KEY"] = user_controls["MISTRAL_API_KEY"] = st.session_state["MISTRAL_API_KEY"] = st.text_input("API Key",
                                                                                                    type="password",
                                                                                                    value=os.getenv("MISTRAL_API_KEY", ""))
            # Validate API key
            if not user_controls["MISTRAL_API_KEY"]:
                st.warning("⚠️ Please enter your MISTRAL API key to proceed. Don't have? refer : https://console.mistral.ai/api-keys ")
                
        if user_controls["selected_llm"] == 'Gemini':
            # Model selection
            model_options = config.get_gemini_model_options()
            user_controls["selected_gemini_model"] = st.selectbox("Select Model", model_options)
            # API key input
            os.environ["GEMINI_API_KEY"] = user_controls["GEMINI_API_KEY"] = st.session_state["GEMINI_API_KEY"] = st.text_input("API Key",
                                                                                                    type="password",
                                                                                                    value=os.getenv("GEMINI_API_KEY", "")) 
            # Validate API key
            if not user_controls["GEMINI_API_KEY"]:
                st.warning("⚠️ Please enter your GEMINI API key to proceed. Don't have? refer : https://ai.google.dev/gemini-api/docs/api-key ")
                
                
        if user_controls["selected_llm"] == 'OpenAI':
            # Model selection
            model_options = config.get_openai_model_options()
            user_controls["selected_openai_model"] = st.selectbox("Select Model", model_options)
            # API key input
            os.environ["OPENAI_API_KEY"] = user_controls["OPENAI_API_KEY"] = st.session_state["OPENAI_API_KEY"] = st.text_input("API Key",
                                                                                                    type="password",
                                                                                                    value=os.getenv("OPENAI_API_KEY", "")) 
            # Validate API key
            if not user_controls["OPENAI_API_KEY"]:
                st.warning("⚠️ Please enter your OPENAI API key to proceed. Don't have? refer : https://platform.openai.com/api-keys ")
    
        if st.button("Reset Session"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            initialize_session()
            st.rerun()
            
        st.subheader("Workflow Overview")
        st.image("workflow_graph.png")
            
    return user_controls


def load_streamlit_ui(config: Config):
    st.set_page_config(page_title=config.get_page_title(), layout="wide")
    st.header(config.get_page_title())
    st.subheader("Let AI agents design your Terraform Code", divider="rainbow", anchor=False)
    user_controls = load_sidebar_ui(config)
    return user_controls

def load_user_input_ui():
    
    st.subheader("Basic Configuration")
    
    # Resolve the JSON path relative to the current file
    json_path = Path(__file__).resolve().parents[2] / "data" / "aws_services.json"

    # Load the JSON file
    with open(json_path, "r") as f:
        aws_services = json.load(f)
    
    aws_services_list = aws_services.get("services", [])
    database_services = aws_services.get("database", [])

    selected_services = st.multiselect("Select AWS Services", aws_services_list)
    
    region = st.text_input("AWS Region", 
                           placeholder="e.g., us-west-1")
    vpc_cidr = st.text_input("VPC CIDR Block", 
                             placeholder="e.g., 10.0.0.0/16")

    st.subheader("Subnet Configuration")
    public_subnets = st.text_area("Public Subnet CIDRs (comma-separated)", 
                                   placeholder="e.g., 10.0.1.0/24, 10.0.2.0/24")
    private_subnets = st.text_area("Private Subnet CIDRs (comma-separated)", 
                                   placeholder="e.g., 10.0.3.0/24, 10.0.4.0/24")
    database_subnets = st.text_area("Database Subnet CIDRs (comma-separated)", 
                                    placeholder="e.g., 10.0.5.0/24, 10.0.6.0/24")

    subnet_configuration = {
        "public": [s.strip() for s in public_subnets.split(",") if s.strip()],
        "private": [s.strip() for s in private_subnets.split(",") if s.strip()],
        "database": [s.strip() for s in database_subnets.split(",") if s.strip()],
    }

    availability_zones = st.text_input("Availability Zones (comma-separated)", 
                                       placeholder="e.g., us-west-2a, us-west-2b")
    availability_zones_list = [az.strip() for az in availability_zones.split(",") if az.strip()]

    compute_type = st.selectbox("Compute Type", ["","ec2", "fargate"])
    database_type = st.selectbox("Select Database Type", [""] + database_services)
    is_multi_az = st.checkbox("Enable Multi-AZ", value=True)
    is_serverless = st.checkbox("Use Serverless Architecture", value=False)
    enable_logging = st.checkbox("Enable CloudWatch Logging", value=True)
    enable_monitoring = st.checkbox("Enable Monitoring", value=True)

    load_balancer_type = st.selectbox("Load Balancer Type", ["", "ALB", "NLB", "CLB"])
    enable_waf = st.checkbox("Enable AWS WAF", value=False)

    st.subheader("Tags")
    environment = st.text_input("Environment", "dev")
    managed_by = st.text_input("Managed By", "Terraform")
    owner = st.text_input("Owner", "DevOps")
    tags = {
        "Environment": environment,
        "ManagedBy": managed_by,
        "Owner": owner
    }

    requirements = st.text_area("Additional Requirements", 
                                placeholder="Enter any specific requirements here.")

    st.subheader("Advanced Configuration")
    custom_parameters_raw = st.text_area("Custom Parameters (JSON format)", "{}")
    
    try:
        custom_parameters = json.loads(custom_parameters_raw)
    except json.JSONDecodeError:
        st.error("Invalid JSON in Custom Parameters")
        custom_parameters = {}
    
    st.session_state.form_data = {
        "services": selected_services,
        "region": region,
        "vpc_cidr": vpc_cidr,
        "subnet_configuration": subnet_configuration,
        "availability_zones": availability_zones_list,
        "compute_type": compute_type,
        "database_type": database_type or None,
        "is_multi_az": is_multi_az,
        "is_serverless": is_serverless,
        "enable_logging": enable_logging,
        "enable_monitoring": enable_monitoring,
        "load_balancer_type": load_balancer_type or None,
        "enable_waf": enable_waf,
        "tags": tags,
        "requirements": requirements,
        "custom_parameters": custom_parameters,
    }

## Main Entry Point    
def load_app():
    """
    Main entry point for the Streamlit app using tab-based UI.
    """
    config = Config()
    if 'stage' not in st.session_state:
        initialize_session()

    user_input = load_streamlit_ui(config)
    if not user_input:
        st.error("Error: Failed to load user input from the UI.")
        return

    try:
        # Configure LLM 
        selectedLLM = user_input.get("selected_llm")
        model = None
        
        if selectedLLM == "Gemini":
            obj_llm_config = GeminiLLM(user_controls_input=user_input)
        elif selectedLLM == "Mistral":
            obj_llm_config = MistralLLM(user_controls_input=user_input)
        elif selectedLLM == "Groq":
            obj_llm_config = GroqLLM(user_controls_input=user_input)
        elif selectedLLM == "OpenAI":
            obj_llm_config = OpenAILLM(user_controls_input=user_input)
            
        model = obj_llm_config.get_llm_model()
        
        if not model:
            st.error("Error: LLM model could not be initialized.")
            return

        ## Graph Builder
        graph_builder = GraphBuilder(model)
        try:
            graph = graph_builder.setup_graph()
            graph_executor = GraphExecutor(graph)
        except Exception as e:
            st.error(f"Error: Graph setup failed - {e}")
            return

        # Create tabs for different stages
        tabs = st.tabs(["Infra Requirement", "Code Generation", "Code Validation", "Download Artifacts"])

        # ---------------- Tab 1: Infra Requirement ----------------
        with tabs[0]:
            st.header("Infra Requirement")
            project_name = st.text_input("Enter the project name:", value=st.session_state.get("project_name", ""))
            st.session_state.project_name = project_name

            if st.session_state.stage == const.PROJECT_INITILIZATION:
                if st.button("🚀 Let's Start"):
                    if not project_name:
                        st.error("Please enter a project name.")
                        st.stop()
                    graph_response = graph_executor.start_workflow(project_name)
                    st.session_state.task_id = graph_response["task_id"]
                    st.session_state.state = graph_response["state"]
                    st.session_state.project_name = project_name
                    st.session_state.stage = const.REQUIREMENT_COLLECTION
                    st.rerun()

            # If stage has progressed beyond initialization, show requirements input and details.
            if st.session_state.stage in [const.REQUIREMENT_COLLECTION]:
               
                load_user_input_ui()
                
                if st.button("Submit Requirements"):
                    logger.info("Submit button clicked")
                    
                    user_input = UserInput(**st.session_state.form_data)
                    st.session_state.state["user_input"] = user_input
                    st.json(user_input)
                    st.success("User requirements submitted successfully!")
                        

        # ---------------- Tab 2: Code Generation ----------------
        with tabs[1]:
            st.header("Code Generation")
            if st.session_state.state in [const.GENERATE_CODE]:
               
               logger.info("Code generation stage reached.")
               
            else:
                st.info("Code generation pending or not reached yet.")

        # ---------------- Tab 3: Code Validation ----------------
        with tabs[2]:
            st.header("Code Validation")
            if st.session_state.stage == const.CODE_VALIDATION:
               
               logger.info("Code validation stage reached.") 
               
            else:
                st.info("Design document generation pending or not reached yet.")
                
        # ---------------- Tab 4: Download Artifacts ----------------
        with tabs[3]:
            st.header("Download Artifacts")
            if st.session_state.state == const.DOWNLOAD_ARTIFACTS:
                
                logger.info("Download artifacts stage reached.")
                
                st.subheader("Download Artifacts")
              
            else:
                st.info("No artifacts generated yet.")

    except Exception as e:
        raise ValueError(f"Error occured with Exception : {e}")
    