import streamlit as st
from src.infra_genie.LLMS.groqllm import GroqLLM
from src.infra_genie.LLMS.geminillm import GeminiLLM
from src.infra_genie.LLMS.openai_llm import OpenAILLM
from src.infra_genie.LLMS.mistral_llm import MistralLLM
from src.infra_genie.LLMS.qwen_llm import QwenLLM
from src.infra_genie.graph.graph_builder import GraphBuilder
from src.infra_genie.ui.uiconfigfile import Config
import src.infra_genie.utils.constants as const
from src.infra_genie.graph.graph_executor import GraphExecutor
import os
from loguru import logger
import json
from pathlib import Path
from src.infra_genie.state.infra_genie_state import UserInput
import uuid

def initialize_session():
    st.session_state.stage = const.PROJECT_INITILIZATION
    st.session_state.project_name = ""
    st.session_state.requirements = ""
    st.session_state.task_id = f"ig-session-{uuid.uuid4().hex[:8]}"
    st.session_state.state = {}
    st.session_state.form_data = {}
    # Add current tab index tracking
    if "current_tab_index" not in st.session_state:
        st.session_state.current_tab_index = 0


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
        
                
        if user_controls["selected_llm"] == 'Qwen':
            # Model selection
            model_options = config.get_qwen_model_options()
            user_controls["selected_qwen_model"] = st.selectbox("Select Model", model_options)
            # API key input
            os.environ["QWEN_API_KEY"] = user_controls["QWEN_API_KEY"] = st.session_state["QWEN_API_KEY"] = st.text_input("API Key",
                                                                                                    type="password",
                                                                                                    value=os.getenv("QWEN_API_KEY", ""))
            # Validate API key
            if not user_controls["QWEN_API_KEY"]:
                st.warning("⚠️ Please enter your QWEN API key to proceed. Don't have? refer : https://bailian.console.alibabacloud.com/?tab=playground#/api-key ")
    
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
    
    # Sample test data to pre-fill the form
    test_input = {
        "services": ["ec2", "lambda"],
        "region": "us-west-1",
        "vpc_cidr": "10.0.0.0/16",
        "subnet_configuration": {
            "public": ["10.0.1.24/16", "10.0.2.24/16"],
            "private": ["10.0.3.0/24", "10.0.4.0/24"],
            "database": ["10.0.5.0/24", "10.0.6.24/16"]
        },
        "availability_zones": ["us-west-1a", "us-west-1b"],
        "compute_type": "ec2",
        "database_type": "rds",
        "is_multi_az": True,
        "is_serverless": False,
        "enable_logging": True,
        "enable_monitoring": True,
        "load_balancer_type": "ALB",
        "enable_waf": True,
        "tags": {
            "Environment": "dev",
            "ManagedBy": "Terraform",
            "Owner": "DevOps"
        },
        "requirements": "",
        "custom_parameters": {}
    }

    st.subheader("Basic Configuration")
    
    if st.checkbox("Enable Test Mode", value=True):
        test_mode = True
    else:
        test_mode = False
    
    # Resolve the JSON path relative to the current file
    json_path = Path(__file__).resolve().parents[2] / "data" / "aws_services.json"

    # Load the JSON file
    with open(json_path, "r") as f:
        aws_services = json.load(f)
    
    aws_services_list = aws_services.get("services", [])
    database_services = aws_services.get("database", [])

    requirements = st.text_area(
        "Application Requirements",
        value=test_input["requirements"] if test_mode else "",
        placeholder="Enter your application requirements here. E.g., Create Terraform module for VPC setup on AWS"
    )
    
    selected_services = st.multiselect(
    "Select AWS Services",
    aws_services_list,
    default=test_input["services"] if test_mode else []
    )
    
    region = st.text_input(
        "AWS Region",
        value=test_input["region"] if test_mode else "",
        placeholder="e.g., us-west-1"
    )
    vpc_cidr = st.text_input(
        "VPC CIDR Block",
        value=test_input["vpc_cidr"] if test_mode else "",
        placeholder="e.g., 10.0.0.0/16"
    )

    st.subheader("Subnet Configuration")
    public_subnets = st.text_area(
        "Public Subnet CIDRs (comma-separated)",
        value=", ".join(test_input["subnet_configuration"]["public"]) if test_mode else "",
        placeholder="e.g., 10.0.1.0/24, 10.0.2.0/24"
    )
    private_subnets = st.text_area(
        "Private Subnet CIDRs (comma-separated)",
        value=", ".join(test_input["subnet_configuration"]["private"]) if test_mode else "",
        placeholder="e.g., 10.0.3.0/24, 10.0.4.0/24"
    )
    database_subnets = st.text_area(
        "Database Subnet CIDRs (comma-separated)",
        value=", ".join(test_input["subnet_configuration"]["database"]) if test_mode else "",
        placeholder="e.g., 10.0.5.0/24, 10.0.6.0/24"
    )

    subnet_configuration = {
        "public": [s.strip() for s in public_subnets.split(",") if s.strip()],
        "private": [s.strip() for s in private_subnets.split(",") if s.strip()],
        "database": [s.strip() for s in database_subnets.split(",") if s.strip()],
    }

    availability_zones = st.text_input(
        "Availability Zones (comma-separated)",
        value=", ".join(test_input["availability_zones"]) if test_mode else "",
        placeholder="e.g., us-west-1a, us-west-1b"
    )
    availability_zones_list = [az.strip() for az in availability_zones.split(",") if az.strip()]

    compute_type = st.selectbox(
        "Compute Type",
        ["", "ec2", "fargate"],
        index=["", "ec2", "fargate"].index(test_input["compute_type"]) if test_mode else 0
    )
    database_type = st.selectbox(
        "Select Database Type",
        [""] + database_services,
        index=([""] + database_services).index(test_input["database_type"]) if test_mode and test_input["database_type"] in database_services else 0
    )
    is_multi_az = st.checkbox("Enable Multi-AZ", value=test_input["is_multi_az"] if test_mode else True)
    is_serverless = st.checkbox("Use Serverless Architecture", value=test_input["is_serverless"] if test_mode else False)
    enable_logging = st.checkbox("Enable CloudWatch Logging", value=test_input["enable_logging"] if test_mode else True)
    enable_monitoring = st.checkbox("Enable Monitoring", value=test_input["enable_monitoring"] if test_mode else True)

    load_balancer_type = st.selectbox(
        "Load Balancer Type",
        ["", "ALB", "NLB", "CLB"],
        index=["", "ALB", "NLB", "CLB"].index(test_input["load_balancer_type"]) if test_mode else 0
    )
    enable_waf = st.checkbox("Enable AWS WAF", value=test_input["enable_waf"] if test_mode else False)

    st.subheader("Tags")
    environment = st.text_input("Environment", value=test_input["tags"]["Environment"] if test_mode else "dev")
    managed_by = st.text_input("Managed By", value=test_input["tags"]["ManagedBy"] if test_mode else "Terraform")
    owner = st.text_input("Owner", value=test_input["tags"]["Owner"] if test_mode else "DevOps")
    tags = {
        "Environment": environment,
        "ManagedBy": managed_by,
        "Owner": owner
    }

    st.subheader("Advanced Configuration")
    custom_parameters_raw = st.text_area(
        "Custom Parameters (JSON format)",
        value=json.dumps(test_input["custom_parameters"], indent=2) if test_mode else "{}"
    )

    
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


def read_all_generated_code():
    base_path = Path("output/src")
    code_output = {}

    for root in ["environments", "modules"]:
        root_path = base_path / root
        if root_path.exists():
            for section in root_path.iterdir():
                if section.is_dir():
                    files = {}
                    for tf_file in section.glob("*.tf"):
                        with open(tf_file, "r") as f:
                            files[tf_file.name] = f.read()
                    if files:
                        code_output[f"{root}/{section.name}"] = files
    return code_output


def display_terraform_validation(validation_json):
    """
    Displays Terraform validation results in a user-friendly format
    """
    st.subheader("Terraform Validation Results")
    
    # Create columns for a more organized layout
    col1, col2 = st.columns([1,2])
    
    with col1:
        # Display validation status with appropriate icons
        if validation_json.get('valid', False):
            st.success("✅ Terraform configuration is valid")
        else:
            st.error(f"❌ Terraform configuration has {validation_json.get('error_count', 0)} error(s)")
            
        # Display warning count if any
        if validation_json.get('warning_count', 0) > 0:
            st.warning(f"⚠️ {validation_json.get('warning_count')} warning(s)")
    
    # Display detailed diagnostics
    if validation_json.get('diagnostics'):
        st.subheader("Validation Details")
        
        for idx, diagnostic in enumerate(validation_json.get('diagnostics', [])):
            issue_summary = diagnostic.get('summary', 'Unknown issue')
            severity = diagnostic.get('severity', 'error')
            
            # Use different icon based on severity
            icon = "🔴" if severity == "error" else "🟠" if severity == "warning" else "ℹ️"
            
            # Create bold text using markdown syntax with emoji
            expander_label = f"{icon} **Issue #{idx+1}:** **{issue_summary}**"
            
            with st.expander(expander_label):
                
                # Create two columns within the expander
                detail_col1, detail_col2 = st.columns([1, 1])
                
                with detail_col1:
                    st.markdown(f"**Severity:** {diagnostic.get('severity', 'unknown')}")
                    st.markdown(f"**Summary:** {diagnostic.get('summary', 'No summary available')}")
                    st.markdown(f"**Detail:** {diagnostic.get('detail', 'No details available')}")
                
                with detail_col2:
                    if 'range' in diagnostic:
                        st.markdown("**Location:**")
                        st.markdown(f"File: `{diagnostic['range'].get('filename', 'unknown')}`")
                        st.markdown(f"Line: {diagnostic['range'].get('start', {}).get('line', 'unknown')}")
                
                # Display code snippet if available
                if 'snippet' in diagnostic:
                    st.markdown("**Code Snippet:**")
                    
                    # Create a block showing context (e.g., module "ec2")
                    if diagnostic['snippet'].get('context'):
                        st.code(diagnostic['snippet'].get('context'), language="hcl")
                    
                    # Show the problematic code with highlighting
                    if diagnostic['snippet'].get('code'):
                        st.code(diagnostic['snippet'].get('code'), language="hcl")
                        
                    # Show guidance for fixing the issue
                    if diagnostic.get('severity') == "error" and diagnostic.get('summary') == "Unsupported argument":
                        st.markdown("**Suggested Fix:**")
                        st.markdown("This argument is not supported in this context. Check the module documentation for valid arguments.")

def display_generated_code():
    all_code = read_all_generated_code()
    if not all_code:
        st.warning("No Terraform code files found.")
    else:
        for section, files in all_code.items():
            st.subheader(f"🗂️ {section}")
            for filename, content in files.items():
                with st.expander(f"📄 {filename}"):
                    st.code(content, language="hcl")
                                
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
        elif selectedLLM == "Qwen":
            obj_llm_config = QwenLLM(user_controls_input=user_input)
            
        model = obj_llm_config.get_llm_model()
        
        if not model:
            st.error("Error: LLM model could not be initialized.")
            return

        ## Graph Builder
        graph_builder = GraphBuilder(model)
        try:
            graph = graph_builder.setup_graph()
            graph_executor = GraphExecutor(graph, st.session_state.task_id)
        except Exception as e:
            st.error(f"Error: Graph setup failed - {e}")
            return

        # Create a radio button for tab selection instead of tabs
        tab_options = ["Infra Requirement", "Code Generation", "Code Validation", "Download Artifacts"]
        current_tab_index = st.session_state.get("current_tab_index", 0)
        selected_tab = st.radio("Navigation", tab_options, index=current_tab_index, horizontal=True, label_visibility="collapsed")
        
        # Store the selected tab index in session state
        tab_index = tab_options.index(selected_tab)
        st.session_state.current_tab_index = tab_index
        
        # Based on the selected tab/radio button, show the appropriate content
        if tab_index == 0:  # Infra Requirement
            st.header("Infra Requirement")
            project_name = st.text_input("Enter the project name:", value=st.session_state.get("project_name", ""))
            st.session_state.project_name = project_name

            if st.session_state.stage == const.PROJECT_INITILIZATION:
                if st.button("🚀 Let's Start"):
                    
                    logger.info("Initiating the process")
                    
                    if not project_name:
                        st.error("Please enter a project name.")
                        st.stop()
                    graph_response = graph_executor.start_workflow(project_name)
                    st.session_state.task_id = graph_response["task_id"]
                    st.session_state.state = graph_response["state"]
                    st.session_state.project_name = project_name
                    st.session_state.stage = const.REQUIREMENT_COLLECTION
                    st.rerun()

            # If stage has progressed beyond initialization, show requirements input and go to next stage
            if st.session_state.stage in [const.REQUIREMENT_COLLECTION]:
                
                load_user_input_ui()
                
                if st.button("Submit Requirements"):
                    logger.info("Submit button clicked")
                    
                    user_input = UserInput(**st.session_state.form_data)
                    st.session_state.state["user_input"] = user_input
                    st.json(user_input)
                    st.success("User requirements submitted successfully!")
                    
                    graph_response = graph_executor.generate_code(st.session_state.task_id, user_input)
                    st.session_state.state = graph_response["state"]
                    
                    st.session_state.stage = const.GENERATE_CODE
                    # Change tab to Code Generation (index 1)
                    st.session_state.current_tab_index = 1
                    st.rerun()
        
        # ---------------- Tab 2: Code Generation ----------------
        elif tab_index == 1:  # Code Generation
            st.header("Code Generation")
            if st.session_state.stage in [const.GENERATE_CODE]:
                
                logger.info("Code generation stage reached.")
                
                st.info("Generated Terraform code output is shown below:")
                
                # Display Generated Code
                display_generated_code()
                
                # Display requirements summary for reference
                if "user_input" in st.session_state.state:
                    with st.expander("Requirements Summary"):
                        st.json(st.session_state.state["user_input"])
                
                
                st.subheader("Review Code")
                if st.button("✅ Proceed to Next Step"):
                    st.success("✅ Code Validataion Started.")
                    graph_response = graph_executor.graph_review_flow(
                        st.session_state.task_id, status=None, feedback=None, review_type=const.REVIEW_CODE
                    )
                    st.session_state.state = graph_response["state"]
                    st.session_state.stage = const.CODE_VALIDATION
                    
                    # Change tab to Code Validation (index 2)
                    st.session_state.current_tab_index = 2
                    st.rerun()
            
            else:
                st.info("Code generation pending or not reached yet.")
                if st.button("Go back to Requirements"):
                    st.session_state.current_tab_index = 0
                    st.rerun()

        # ---------------- Tab 3: Code Validation ----------------
        elif tab_index == 2:  # Code Validation
            st.header("Code Validation")
            if st.session_state.stage == const.CODE_VALIDATION:
                
                logger.info("Code validation stage reached.") 
                
                # Display validation results
                code_validation_json = json.loads(st.session_state.state["code_validation_json"])
                display_terraform_validation(code_validation_json)
                
                # Display Generated Code
                st.subheader("Generated Code ")
                display_generated_code()
                
                ## Review Section
                st.subheader("Actions")
                feedback_text = st.text_area("Provide feedback for improving code (optional):")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Re-generate Code"):
                        st.info("Regenerating code...")
                        st.rerun()
                        
                        
                with col2:
                    if st.button("✍️ Give Feedback"):
                        if not feedback_text.strip():
                            st.warning("⚠️ Please enter feedback before submitting.")
                            st.rerun()
                        else:
                            st.info("🔄 Sending feedback to revise code.")
                            st.rerun()
                
            else:
                st.info("Code validation pending or not reached yet.")
                
        # ---------------- Tab 4: Download Artifacts ----------------
        elif tab_index == 3:  # Download Artifacts
            st.header("Download Artifacts")
            if st.session_state.state == const.DOWNLOAD_ARTIFACTS:
                
                logger.info("Download artifacts stage reached.")
                
                st.subheader("Download Artifacts")
                
            else:
                st.info("No artifacts generated yet.")

    except Exception as e:
        raise ValueError(f"Error occured with Exception : {e}")