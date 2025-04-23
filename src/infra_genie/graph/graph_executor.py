from src.infra_genie.state.infra_genie_state import InfraGenieState
from src.infra_genie.cache.redis_cache import flush_redis_cache, save_state_to_redis, get_state_from_redis
import uuid
import src.infra_genie.utils.constants as const
from loguru import logger

class GraphExecutor:
    def __init__(self, graph):
        self.graph = graph

    def get_thread(self, task_id):
        return {"configurable": {"thread_id": task_id}}
    
    ## ------- Start the Workflow ------- ##
    def start_workflow(self, project_name: str):
        
        graph = self.graph
        
        flush_redis_cache()
        
        # Generate a unique task id
        task_id = f"ig-session-{uuid.uuid4().hex[:8]}"
        
        thread = self.get_thread(task_id)
        
        state = None
        for event in graph.stream({"project_name": project_name},thread, stream_mode="values"):
           state = event
        
        current_state = graph.get_state(thread)
        save_state_to_redis(task_id, current_state)
        
        return {"task_id" : task_id, "state": state}
    
   
    ## -------- Helper Method to handle the graph resume state ------- ##
    def update_and_resume_graph(self, saved_state,task_id, as_node):
        graph = self.graph
        thread = self.get_thread(task_id)
        
        graph.update_state(thread, saved_state, as_node=as_node)
        
         # Resume the graph
        state = None
        for event in graph.stream(None, thread, stream_mode="values"):
            logger.debug(f"Event Received: {event}")
            state = event
        
        # saving the state before asking the product owner for review
        current_state = graph.get_state(thread)
        save_state_to_redis(task_id, current_state)
        
        return {"task_id" : task_id, "state": state}


    def get_updated_state(self, task_id):
        saved_state = get_state_from_redis(task_id)
        return {"task_id" : task_id, "state": saved_state}
    
