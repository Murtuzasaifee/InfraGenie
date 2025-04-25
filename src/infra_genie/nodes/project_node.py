from src.infra_genie.state.infra_genie_state import InfraGenieState
from src.infra_genie.utils import constants as const
import opik

class ProjectNode:
    
    def __init__(self, llm):
        self.llm = llm
     
    @opik.track  
    def initialize_project(self, state: InfraGenieState):
        """
            Performs the project initilazation
        """
        state.next_node = const.REQUIREMENT_COLLECTION
        return state
    
    
    @opik.track
    def get_user_requirements(self, state: InfraGenieState):
        """
            Gets the requirements from the user
        """
        state.next_node = const.GENERATE_CODE
        return state
