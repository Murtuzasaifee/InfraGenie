from src.infra_genie.ui.streamlit_ui.streamlit_app import load_app
from src.infra_genie.utils.logging_config import setup_logging
import os
from dotenv import load_dotenv

def main():
   ## Setup logging level
   setup_logging(log_level="DEBUG")
   
   load_dotenv()
   
   # os.environ["LANGCHAIN_API_KEY"]=os.getenv("LANGCHAIN_API_KEY")
   # os.environ["LANGCHAIN_TRACING_V2"]="true"
   # os.environ["LANGCHAIN_PROJECT"]=os.getenv("LANGCHAIN_PROJECT")
   
   load_app()


if __name__ == "__main__":
    main()
