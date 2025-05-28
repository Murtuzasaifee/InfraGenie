from langchain_google_genai import ChatGoogleGenerativeAI


class GeminiLLM:
    def __init__(self, user_controls_input=None, model=None, api_key=None):
        self.user_controls_input = user_controls_input
        self.model = model
        self.api_key = api_key
        
    def get_llm_model(self):
        try:
            if  self.user_controls_input:
                gemini_api_key = self.user_controls_input['GEMINI_API_KEY']
                selected_gemini_model = self.user_controls_input['selected_gemini_model']
                llm = ChatGoogleGenerativeAI(api_key=gemini_api_key, model= selected_gemini_model, temperature=0.0)
            else:
                llm = ChatGoogleGenerativeAI(api_key=self.api_key,model=self.model, temperature=0.0)
        
        except Exception as e:
            raise ValueError(f"Error occured with Exception : {e}")
        
        return llm