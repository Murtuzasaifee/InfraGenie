from src.infra_genie.state.infra_genie_state import InfraGenieState, UserInput
from src.infra_genie.cache.redis_cache import flush_redis_cache, save_state_to_redis, get_state_from_redis
import uuid
import src.infra_genie.utils.constants as const
from loguru import logger
from langfuse.callback import CallbackHandler

class GraphExecutor:
    def __init__(self, graph, task_id):
        self.graph = graph
        self.task_id = task_id
        self.user_id = "msaifee"
        self.langfuse_handler = CallbackHandler(session_id=self.task_id, user_id=self.user_id)

    def get_thread(self, task_id):
        return {"configurable": {"thread_id": task_id}}
    
    def get_langfuse_callback(self):
        return {"callbacks": [self.langfuse_handler]}
    
    def get_config(self, task_id):
        config = {}
        config.update(self.get_thread(task_id))
        config.update(self.get_langfuse_callback())
        logger.debug(f"Config: {config}")
        return config
    
    ## ------- Start the Workflow ------- ##
    def start_workflow(self, project_name: str):
        graph = self.graph

        flush_redis_cache()

        task_id = self.task_id
        thread = self.get_thread(task_id)

        state = None
        for event in graph.stream(
            {"project_name": project_name},
            config=self.get_config(task_id),
            stream_mode="values"
        ):
            state = event

        current_state = graph.get_state(thread)
        save_state_to_redis(task_id, current_state)

        return {"task_id": task_id, "state": state}
    
    
    ## ------- Code Generation ------- ##
    def generate_code(self, task_id:str, user_input : UserInput):
        
        saved_state = get_state_from_redis(task_id)
        if saved_state:
            saved_state.user_input = user_input
            saved_state.next_node = const.GENERATE_CODE
        
        return self.update_and_resume_graph(saved_state,task_id,"get_user_requirements")
    
   
   
   ## ------- Generic Review Flow for all the feedback stages  ------- ##
    def graph_review_flow(self, task_id, status, feedback, review_type):
        saved_state = get_state_from_redis(task_id)
        
        if saved_state:
            if review_type == const.SAVE_CODE:
                node_name = "save_code"
                saved_state.next_node = const.CODE_VALIDATION
                
            elif review_type == const.CODE_VALIDATION:
                node_name = "code_validator"
                saved_state.code_validation_user_feedback = feedback
                saved_state.code_review_status = status
                
                if status == "approved":
                    logger.success("User Approved the code")
                    saved_state.is_code_valid = True
                
                saved_state.next_node = const.GENERATE_CODE if status == "feedback" else const.DOWNLOAD_ARTIFACTS
                
            # elif review_type == const.GENERATE_PLAN:
            #     node_name = "create_terraform_plan"
            #     saved_state.code_validation_user_feedback = feedback
            #     saved_state.code_review_status = status
                
            #     ## For testing only
            #     # saved_state.is_plan_success = True
                
            #     saved_state.next_node = const.GENERATE_CODE if status == "feedback" else const.DOWNLOAD_ARTIFACTS
                
            else:
                raise ValueError(f"Unsupported review type: {review_type}")
            
        return self.update_and_resume_graph(saved_state,task_id,node_name)
    
    
    ## -------- Helper Method to handle the graph resume state ------- ##
    def update_and_resume_graph(self, saved_state,task_id, as_node):
        graph = self.graph
        thread = self.get_thread(task_id)
        
        graph.update_state(thread, saved_state, as_node=as_node)
        
         # Resume the graph
        state = None
        for event in graph.stream(
            None, 
            config=self.get_config(task_id),
            stream_mode="values"
        ):
            logger.debug(f"Event Received: {event}")
            state = event
        
        current_state = graph.get_state(thread)
        save_state_to_redis(task_id, current_state)
        
        return {"task_id" : task_id, "state": state}


    def get_updated_state(self, task_id):
        saved_state = get_state_from_redis(task_id)
        return {"task_id" : task_id, "state": saved_state}
    
