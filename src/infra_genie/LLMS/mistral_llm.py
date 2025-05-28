from langchain_mistralai.chat_models import ChatMistralAI


class MistralLLM:
    def __init__(self, user_controls_input=None, model=None, api_key=None):
        self.user_controls_input = user_controls_input
        self.model = model
        self.api_key = api_key
        
        
    def get_llm_model(self):
        try:
            if  self.user_controls_input:
                mistral_api_key = self.user_controls_input['MISTRAL_API_KEY']
                selected_model = self.user_controls_input['selected_mistral_model']
                llm = ChatMistralAI(api_key=mistral_api_key, model= selected_model, temperature=0.0)
            else:
                llm = ChatMistralAI(api_key=mistral_api_key, model= self.model, temperature=0.0)

        except Exception as e:
            raise ValueError(f"Error occured with Exception : {e}")
        
        return llm