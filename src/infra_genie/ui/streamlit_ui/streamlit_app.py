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
from src.infra_genie.state.infra_genie_state import UserInput, BasicInfo
import uuid
from pathlib import Path
import tempfile
from datetime import datetime
import zipfile
from typing import List

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
    
def load_user_input_ui():
    
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
        
    
    st.session_state.form_data = {
        "project_name": project_name,
        "description": description,
        "application_type": app_type,
        "detected_services": detected,
        "security_level": security_level
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
                            
def create_zip_from_output_folder():
    """
    Creates a zip file from the output/src folder maintaining the directory structure
    Returns the path to the created zip file
    """
    output_folder = Path("output/src")
    
    if not output_folder.exists():
        return None
    
    # Create a temporary file for the zip
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"terraform_artifacts_{timestamp}.zip"
    
    # Create zip in a temporary directory
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through the output/src directory
        for root, dirs, files in os.walk(output_folder):
            for file in files:
                file_path = os.path.join(root, file)
                # Create archive path relative to output/src
                arcname = os.path.relpath(file_path, output_folder)
                zipf.write(file_path, arcname)
    
    return zip_path

def get_folder_structure_display():
    """
    Returns a string representation of the output folder structure for display
    """
    output_folder = Path("output/src")
    
    if not output_folder.exists():
        return "No artifacts found"
    
    structure = []
    
    def add_to_structure(path, prefix=""):
        items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            structure.append(f"{prefix}{current_prefix}{item.name}")
            
            if item.is_dir():
                next_prefix = prefix + ("    " if is_last else "│   ")
                add_to_structure(item, next_prefix)
    
    structure.append("📁 terraform_artifacts/")
    add_to_structure(output_folder, "")
    
    return "\n".join(structure)

def get_artifact_summary():
    """
    Returns summary information about the generated artifacts
    """
    output_folder = Path("output/src")
    
    if not output_folder.exists():
        return {}
    
    summary = {
        "environments": [],
        "modules": [],
        "total_files": 0,
        "total_size": 0
    }
    
    # Count environments
    env_folder = output_folder / "environments"
    if env_folder.exists():
        for env_dir in env_folder.iterdir():
            if env_dir.is_dir():
                file_count = len(list(env_dir.glob("*.tf")))
                summary["environments"].append({
                    "name": env_dir.name,
                    "files": file_count
                })
    
    # Count modules
    modules_folder = output_folder / "modules"
    if modules_folder.exists():
        for module_dir in modules_folder.iterdir():
            if module_dir.is_dir():
                file_count = len(list(module_dir.glob("*.tf")))
                summary["modules"].append({
                    "name": module_dir.name,
                    "files": file_count
                })
    
    # Count total files and size
    for file_path in output_folder.rglob("*"):
        if file_path.is_file():
            summary["total_files"] += 1
            summary["total_size"] += file_path.stat().st_size
    
    return summary
    
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
                    
                    basic_info = BasicInfo(**st.session_state.form_data)
                    user_input = UserInput(basic_info=basic_info)
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
                
                
                st.subheader("Actions")
                if st.button("Proceed to Validation"):
                    st.success("Code Validataion Started.")
                    graph_response = graph_executor.graph_review_flow(
                        st.session_state.task_id, status=None, feedback=None, review_type=const.SAVE_CODE
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
                st.subheader("Review Code")
                feedback_text = st.text_area("Provide feedback for improving code (optional):")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Approve Code"):
                        st.info("Generating Terraform Plan for approved code...")
                        graph_response = graph_executor.graph_review_flow(
                            st.session_state.task_id, status="approved", feedback=None,  review_type=const.CODE_VALIDATION
                        )
                        st.session_state.state = graph_response["state"]
                        st.session_state.stage = const.DOWNLOAD_ARTIFACTS
                       
                        # Change tab to Downaload Artifacts (index 3)
                        st.session_state.current_tab_index = 3
                        st.rerun()
                        
                        
                with col2:
                    if st.button("🔄 Re-generate Code"):
                        if not feedback_text.strip():
                            st.warning("✍️ Give Feedback. Please enter feedback before submitting.")
                        else:
                            st.info("🔄 Sending feedback to revise code.")
                            graph_response = graph_executor.graph_review_flow(
                                st.session_state.task_id, status="feedback", feedback=feedback_text.strip(),review_type=const.CODE_VALIDATION
                            )
                            st.session_state.state = graph_response["state"]
                            st.session_state.stage = const.GENERATE_CODE
                            # Change tab to Code Generation (index 1)
                            st.session_state.current_tab_index = 1
                            st.rerun()
                
            else:
                st.info("Code validation pending or not reached yet.")
       
        # # ---------------- Tab 4: Terraform Plan ----------------
        # elif tab_index == 3:  # Terraform Plan
        #     st.header("Terraform Plan")
        #     if st.session_state.stage == const.GENERATE_PLAN:
                
        #         logger.info("Terraform Plan stage reached.")
                
        #         # Display Generated Code
        #         display_generated_code()
                
        #         # Display requirements summary for reference
        #         if "user_input" in st.session_state.state:
        #             with st.expander("Requirements Summary"):
        #                 st.json(st.session_state.state["user_input"])
                
                
        #         ## Review Section
        #         st.subheader("Review Plan")
        #         feedback_text = st.text_area("Provide feedback for improving code (optional):")
        #         col1, col2 = st.columns(2)
        #         with col1:
        #             if st.button("Download Artifacts"):
        #                 graph_response = graph_executor.graph_review_flow(
        #                     st.session_state.task_id, status="approved", feedback=None,  review_type=const.GENERATE_PLAN
        #                 )
        #                 st.session_state.state = graph_response["state"]
        #                 st.session_state.stage = const.DOWNLOAD_ARTIFACTS
                       
        #                 # Change tab to Terraform Plan (index 4)
        #                 st.session_state.current_tab_index = 4
        #                 st.rerun()
                        
                        
        #         with col2:
        #             if st.button("🔄 Re-generate Code"):
        #                 if not feedback_text.strip():
        #                     st.warning("✍️ Give Feedback. Please enter feedback before submitting.")
        #                 else:
        #                     st.info("🔄 Sending feedback to revise code.")
        #                     graph_response = graph_executor.graph_review_flow(
        #                         st.session_state.task_id, status="feedback", feedback=feedback_text.strip(),review_type=const.GENERATE_PLAN
        #                     )
        #                     st.session_state.state = graph_response["state"]
        #                     st.session_state.stage = const.GENERATE_CODE
        #                     # Change tab to Code Generation (index 1)
        #                     st.session_state.current_tab_index = 1
        #                     st.rerun()
                            
        #     else:
        #         st.info("No Terraform Plan generated yet.")
                
                         
        # ---------------- Tab 3: Download Artifacts ----------------
        elif tab_index == 3:  # Download Artifacts
            st.header("Download Artifacts")
            if st.session_state.stage == const.DOWNLOAD_ARTIFACTS:
                logger.info("Download artifacts stage reached.")
                
                # Check if artifacts exist
                output_folder = Path("output/src")
                if not output_folder.exists() or not any(output_folder.iterdir()):
                    st.warning("⚠️ No artifacts found to download.")
                    st.info("Please generate code first by going through the previous steps.")
                else:
                    # Display artifact summary
                    st.subheader("📊 Artifact Summary")
                    
                    summary = get_artifact_summary()
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Files", summary["total_files"])
                    
                    with col2:
                        st.metric("Environments", len(summary["environments"]))
                    
                    with col3:
                        st.metric("Modules", len(summary["modules"]))
                    
                    with col4:
                        size_mb = summary["total_size"] / (1024 * 1024)
                        st.metric("Total Size", f"{size_mb:.2f} MB")
                    
                    # Display detailed breakdown
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("🏗️ Environments")
                        if summary["environments"]:
                            for env in summary["environments"]:
                                st.write(f"• **{env['name']}** - {env['files']} files")
                        else:
                            st.write("No environments found")
                    
                    with col2:
                        st.subheader("📦 Modules")
                        if summary["modules"]:
                            for module in summary["modules"]:
                                st.write(f"• **{module['name']}** - {module['files']} files")
                        else:
                            st.write("No modules found")
                    
                    # Display folder structure
                    st.subheader("📁 Folder Structure")
                    with st.expander("View complete folder structure"):
                        structure = get_folder_structure_display()
                        st.code(structure, language="text")
                    
                    # Display generated code preview
                    st.subheader("📄 Generated Code Preview")
                    display_generated_code()
                    
                    # Download section
                    st.subheader("⬇️ Download Options")
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.info("💡 **What you'll get:**\n"
                            "• Complete Terraform configuration files\n"
                            "• Organized by environments and modules\n"
                            "• Ready-to-deploy infrastructure code\n"
                            "• Maintains proper directory structure")
                    
                    with col2:
                        # Create download button
                        if st.button("🗜️ Create Download Package", type="primary"):
                            with st.spinner("Creating download package..."):
                                zip_path = create_zip_from_output_folder()
                                
                                if zip_path:
                                    # Store zip path in session state for download
                                    st.session_state.zip_path = zip_path
                                    st.success("✅ Download package created successfully!")
                                else:
                                    st.error("❌ Failed to create download package")
                    
                    # Download button (appears after package is created)
                    if hasattr(st.session_state, 'zip_path') and os.path.exists(st.session_state.zip_path):
                        st.subheader("📥 Download Ready")
                        
                        # Read the zip file for download
                        with open(st.session_state.zip_path, "rb") as file:
                            zip_data = file.read()
                        
                        # Get the filename from the path
                        zip_filename = os.path.basename(st.session_state.zip_path)
                        
                        st.download_button(
                            label="📥 Download Terraform Artifacts",
                            data=zip_data,
                            file_name=zip_filename,
                            mime="application/zip",
                            type="primary",
                            help="Click to download your complete Terraform configuration"
                        )
                        
                        # Display download instructions
                        st.subheader("📋 Next Steps")
                        st.markdown("""
                        **After downloading:**
                        
                        1. **Extract the ZIP file** to your desired location
                        2. **Navigate to the environment** you want to deploy (dev/stage/prod)
                        3. **Initialize Terraform:**
                        ```bash
                        terraform init
                        ```
                        4. **Review the plan:**
                        ```bash
                        terraform plan
                        ```
                        5. **Apply the configuration:**
                        ```bash
                        terraform apply
                        ```
                        
                        **Important Notes:**
                        - Ensure you have AWS credentials configured
                        - Review all configurations before applying
                        - Start with the dev environment for testing
                        - Customize variables as needed for your specific requirements
                        """)
                        
                        # Cleanup option
                        if st.button("🧹 Clear Download Package"):
                            try:
                                if os.path.exists(st.session_state.zip_path):
                                    os.remove(st.session_state.zip_path)
                                del st.session_state.zip_path
                                st.success("Package cleared successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error clearing package: {e}")
            
            else:
                st.info("🔄 Download artifacts are not ready yet.")
                st.markdown("""
                **To reach this stage, you need to:**
                1. ✅ Complete the infrastructure requirements
                2. ✅ Generate Terraform code
                3. ✅ Validate the generated code
                4. ✅ Review and approve the Terraform plan
                
                Please go through the previous steps first.
                """)

    except Exception as e:
        raise ValueError(f"Error occured with Exception : {e}")