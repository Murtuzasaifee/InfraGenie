import os
import streamlit as st
from langchain_qwq import ChatQwQ


class QwenLLM:
    def __init__(self, user_controls_input=None, model=None, api_key=None):
        self.user_controls_input = user_controls_input
        self.model = model
        self.api_key = api_key
        
        
    def get_llm_model(self):
        try:
            if  self.user_controls_input:
                qwen_api_key = self.user_controls_input['QWEN_API_KEY']
                selected_openai_model = self.user_controls_input['selected_qwen_model']
                llm = ChatQwQ(api_key=qwen_api_key, model= selected_openai_model)
            else:
                llm = ChatQwQ(api_key=qwen_api_key, model= self.model)

        except Exception as e:
            raise ValueError(f"Error occured with Exception : {e}")
        
        return llm