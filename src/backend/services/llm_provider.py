import os
from abc import ABC, abstractmethod
from google import genai
from google.genai import types

from backend.models.llm import ClientIntent

client = genai.Client()

class LLmProvider(ABC):
    @abstractmethod
    async def generate_text(self, prompt:str)->str:
        pass

class GeminiLLmProvider(LLmProvider):
    def __init__(self, model_name: str = "gemini-3.1-flash-lite"):
        detailed_instructions = """
        You are a routing backend assistant for a software agency. Your job is to analyze the user's input, extract data, and draft a polite response.
        
        INTENT CLASSIFICATION RULES:
        - If the user mentions a budget or timeline, set intent_type to 'save_lead'.
        - If they ask general questions about past projects or services, set intent_type to 'general_faq'.
        
        CONVERSATIONAL RULES (CRITICAL):
        - NEVER reject a project outright based on a low budget.
        - NEVER mention the agency's standard minimum charges.
        - If a client provides a budget (even a very low one like $200), politely acknowledge their message and IMMEDIATELY ask them to elaborate on their technical requirements, features, and overall project goals. 
        - Your goal is to gather project requirements first before any pricing discussions occur.
        """
        
        self.model_name = model_name
        self.config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ClientIntent,
            system_instruction=(
                "You are a routing backend assistant for a software agency. Analyze the user's input. "
                "If they mention a budget or timeline, set intent_type to 'save_lead'. "
                "If they ask general questions about past projects, set intent_type to 'general_faq'."
            )
        )

    async def generate_text(self, prompt:str)->str:
        response = await client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=self.config
        )
        return response.text or ""