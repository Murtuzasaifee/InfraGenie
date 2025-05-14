from langgraph.graph import StateGraph,START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables.graph import MermaidDrawMethod
from src.infra_genie.state.infra_genie_state import InfraGenieState
from src.infra_genie.nodes.code_generator_node import CodeGeneratorNode
from src.infra_genie.nodes.fallback_node import FallbackNode
from src.infra_genie.nodes.project_node import ProjectNode
from src.infra_genie.nodes.code_process_node import ProcessCodeNode
from src.infra_genie.nodes.code_validator_node import CodeValidatorNode

    
class GraphBuilder:
    
    def __init__(self, llm):
        self.llm = llm
        self.graph_builder = StateGraph(InfraGenieState)
        self.memory = MemorySaver()
                
    
    def set_groq_llm(self, groq_llm):
        self.groq_llm = groq_llm
    

    def set_gemini_llm(self, gemini_llm):
        self.gemini_llm = gemini_llm
        
        
    def set_openai_llm(self, openai_llm):
        self.openai_llm = openai_llm
        
    def set_mistral_llm(self, mistral_llm):
        self.mistral_llm = mistral_llm
    
    
    def build_infra_graph(self):
        """
            Configure the graph by adding nodes, edges
        """
        
        self.project_node = ProjectNode(self.llm)
        self.code_generation_node = CodeGeneratorNode(self.llm)
        self.fallback_node = FallbackNode(self.llm)
        self.process_code_node = ProcessCodeNode(self.llm)
        self.code_validator_node = CodeValidatorNode(self.llm)
        
        # Add nodes
        self.graph_builder.add_node("initialize_project", self.project_node.initialize_project)
        self.graph_builder.add_node("get_user_requirements", self.project_node.get_user_requirements)
        self.graph_builder.add_node("generate_terraform_code", self.code_generation_node.generate_terraform_code)
        self.graph_builder.add_node("fallback_generate_terraform_code", self.fallback_node.fallback_generate_terraform_code)
        self.graph_builder.add_node("save_code", self.process_code_node.save_terraform_files)
        self.graph_builder.add_node("code_validator", self.code_validator_node.validate_terraform_code)
        self.graph_builder.add_node("creat_terraform_plan", self.code_validator_node.create_terraform_plan)
        self.graph_builder.add_node("fix_code", self.code_generation_node.fix_code)
        

        ## Edges
        self.graph_builder.add_edge(START,"initialize_project")
        self.graph_builder.add_edge("initialize_project","get_user_requirements")
        self.graph_builder.add_edge("get_user_requirements","generate_terraform_code")
        self.graph_builder.add_conditional_edges(
            "generate_terraform_code",
            self.code_generation_node.is_code_generated,
            {True: "save_code", False: "fallback_generate_terraform_code"}
        )
        self.graph_builder.add_conditional_edges(
            "fallback_generate_terraform_code",
            self.code_generation_node.is_code_generated,
            {True: "save_code", False: END}
        )
        
        self.graph_builder.add_edge("save_code","code_validator")
        self.graph_builder.add_conditional_edges(
            "code_validator",
            self.code_validator_node.code_validation_router,
            {
                "approved": "creat_terraform_plan",
                "feedback": "fix_code"
            }
        )
        self.graph_builder.add_edge("fix_code","generate_terraform_code")
        self.graph_builder.add_edge("code_validator","creat_terraform_plan")
        self.graph_builder.add_edge("creat_terraform_plan", END)
    
         
        
    def setup_graph(self):
        """
        Sets up the graph
        """
        self.build_infra_graph()
        return self.graph_builder.compile(
            interrupt_before=[
                'get_user_requirements'
                ],checkpointer=self.memory
        )
        
             
    # def setup_graph(self):
    #     """
    #     Sets up the graph
    #     """
    #     self.build_infra_graph()
    #     graph =self.graph_builder.compile(
    #         interrupt_before=[
    #             'get_user_requirements',
    #         ],checkpointer=self.memory
    #     )
    #     self.save_graph_image(graph)         
    #     return graph
    
    
    def save_graph_image(self,graph):
        # Generate the PNG image
        img_data = graph.get_graph().draw_mermaid_png(
            draw_method=MermaidDrawMethod.API
            )

        # Save the image to a file
        graph_path = "workflow_graph.png"
        with open(graph_path, "wb") as f:
            f.write(img_data)        
            
        