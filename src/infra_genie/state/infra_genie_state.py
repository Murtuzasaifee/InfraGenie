from pydantic import BaseModel, Field
from typing import Any, Dict, Literal, Optional
import json
import src.infra_genie.utils.constants as const

    
   
class InfraGenieState(BaseModel):
    """
    Represents the structure of the state used in the graph

    """    

    
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        # Check if the object is any kind of Pydantic model
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        
        return super().default(obj)
    

    