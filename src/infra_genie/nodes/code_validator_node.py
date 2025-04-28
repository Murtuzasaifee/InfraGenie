from src.infra_genie.state.infra_genie_state import InfraGenieState
from src.infra_genie.utils import constants as const
import opik

class CodeValidatorNode:
    
    def __init__(self, llm):
        self.llm = llm
        
    @opik.track
    def validate_terraform_code(self, state: InfraGenieState):
        """
            Validates the generated Terraform code
        """
        state.next_node = const.SAVE_CODE
        return state