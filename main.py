from src.infra_genie.ui.streamlit_ui.streamlit_app import load_app
from src.infra_genie.utils.logging_config import setup_logging
import os
from dotenv import load_dotenv

def main():
   ## Setup logging level
   setup_logging(log_level="DEBUG")
   
   load_dotenv()
   
   ## LangChain Tracing
   # os.environ["LANGCHAIN_API_KEY"]=os.getenv("LANGCHAIN_API_KEY")
   # os.environ["LANGCHAIN_TRACING_V2"]="true"
   # os.environ["LANGCHAIN_PROJECT"]=os.getenv("LANGCHAIN_PROJECT")
   
   ## LangFuse Tracing
   os.environ["LANGFUSE_PUBLIC_KEY"] = os.getenv("LANGFUSE_PUBLIC_KEY")
   os.environ["LANGFUSE_SECRET_KEY"] = os.getenv("LANGFUSE_SECRET_KEY")
   os.environ["LANGFUSE_HOST"] = os.getenv("LANGFUSE_HOST")
   
   load_app()


if __name__ == "__main__":
    main()
