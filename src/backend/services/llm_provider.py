import json
from abc import ABC, abstractmethod
from pathlib import Path

from google import genai
from google.genai import types

from backend.models.llm import ClientIntent
from backend.schemas.chat import ChatMessage


class LLmProvider(ABC):
    @abstractmethod
    async def generate_text(self, prompt:str,old_chats:list[ChatMessage])->ClientIntent:
        pass

class GeminiLLmProvider(LLmProvider):
    def __init__(self, model_name: str = "gemini-3.1-flash-lite"):
        self.client = genai.Client()
        current_dir = Path(__file__).parent
        json_path = current_dir.parent.parent / 'data' / 'llm_response_example.json'
        with open(json_path, 'r') as file:
            llm_response_example = json.load(file)

        detailed_instructions = f"""
        You are a routing backend assistant for a software agency. Your job is to analyze the user's input, extract data, and draft a polite response.
        
        INTENT CLASSIFICATION RULES:
        You must classify the user's input into one of the following intent types:
        - `update_budget`: Use when the client explicitly changes or provides their budget.
        - `update_estimated_cost`: Use when the client's feature requirements change (added or removed), implying a change in the overall cost estimate.
        - `reset_requirements`: Use when the client disagrees with the AI's suggested requirements or requests modifications to the proposed feature set. You must output the COMPLETE, newly adjusted list of requirements.
        - `update_tech_stack`: Use when a change in requirements necessitates a change in the required technologies (e.g., they initially wanted just an app so tech was Flutter/Python, but now they want a web app too, so the tech stack becomes Flutter, Python, and React/Javascript).
        - `general_faq`: Use when the user asks general questions about past projects, services, or initial greetings without specific project details.
        
        CONVERSATIONAL RULES (CRITICAL):
        - NEVER reject a project outright based on a low budget.
        - NEVER mention the agency's standard minimum charges.
        - If a client provides a budget (even a very low one like $200), politely acknowledge their message and IMMEDIATELY ask them to elaborate on their technical requirements, features, and overall project goals. 
        - Your goal is to gather project requirements first before any pricing discussions occur.
        - If a client asks to build an app similar to an existing, well-known app, use your internal knowledge to list the core functionalities of the specific app they requested. Then, ask the client which of those specific features they want in their version, and if they require any custom additions.
        - If the client agrees with all proposed requirements, list ALL the agreed-upon requirements in the `requirements` parameter.
        
        EXAMPLES OF EXPECTED BEHAVIOR AND JSON OUTPUT:
        {json.dumps(llm_response_example, indent=2)}
        """

        self.model_name = model_name
        self.config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ClientIntent,
            system_instruction=detailed_instructions,
            temperature=0.1
        )

    async def generate_text(self, prompt:str,old_chats:list[ChatMessage])->ClientIntent:
        gemini_content=[]
        if old_chats:
            for chat in old_chats:
                gemini_content.append({
                    "role": chat.role,
                    "parts": [{"text": chat.text}]
                })

        gemini_content.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=gemini_content,
            config=self.config
        )
        return ClientIntent.model_validate_json(response.text or "")

    async def generate_embeddings(self, text:str)->list[float] | None:
        response = self.client.models.embed_content(
            model='text-embedding-004',
            contents=text,
        )
        vector = response.embeddings[0].values
        return vector