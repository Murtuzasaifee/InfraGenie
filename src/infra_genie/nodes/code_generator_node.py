from pydantic import BaseModel, Field
from typing import List
import os
from loguru import logger
from src.infra_genie.state.infra_genie_state import InfraGenieState
    

class ResumeProcessor:
    
    def __init__(self, llm):
        self.llm = llm
       
        
    def generate_terraform_code(self, state: InfraGenieState):
        """
        
        """
        
        return state