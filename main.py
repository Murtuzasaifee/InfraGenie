from src.infra_genie.ui.streamlit_ui.streamlit_app import load_app
from src.infra_genie.utils.logging_config import setup_logging

def main():
   ## Setup logging level
   setup_logging(log_level="DEBUG")
   load_app()


if __name__ == "__main__":
    main()
