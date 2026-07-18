import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
import logging

from google import genai
from google.genai import types

from backend.models.llm import LLMResponse
from backend.schemas.chat import ChatMessage

logger = logging.getLogger(__name__)


class LLmProvider(ABC):
    @abstractmethod
    async def generate_text(self, prompt:str,context_data:dict[str,Any],old_chats:list[ChatMessage],tools: list | None =None)->LLMResponse:
        pass

class GeminiLLmProvider(LLmProvider):
    def __init__(self, model_name: str = "gemini-3.1-flash-lite"):
        self.client = genai.Client()
        current_dir = Path(__file__).parent
        json_path = current_dir.parent.parent / 'data' / 'llm_response_example.json'
        with open(json_path, 'r') as file:
            llm_response_example = json.load(file)

        self.detailed_instructions = f"""
        You are a routing backend assistant for a software agency. Your job is to analyze the user's input, extract data, and draft a polite response.
        
        INTENT CLASSIFICATION RULES:
        You must classify the user's input into one of the following intent types:
        - `update_budget`: Use when the client explicitly changes or provides their budget.
        - `update_estimated_cost`: Use when the client's feature requirements change (added or removed), implying a change in the overall cost estimate.
        - `reset_requirements`: Use when the client disagrees with the AI's suggested requirements or requests modifications to the proposed feature set. You must output the COMPLETE, newly adjusted list of requirements.
        - `update_tech_stack`: Use when a change in requirements necessitates a change in the required technologies (e.g., they initially wanted just an app so tech was Flutter/Python, but now they want a web app too, so the tech stack becomes Flutter, Python, and React/Javascript).
        - `general_faq`: Use when the user asks general questions about past projects, services, or initial greetings without specific project details.
        - `query_cost_estimate`: Use when the user asks for the current estimated cost of their project.
        - `found_project_id`: Use when the user explicitly mentions or provides an existing project ID in their message. You must extract this ID into the `project_id` field.
        
        CONVERSATIONAL RULES (CRITICAL):
        - NEVER reject a project outright based on a low budget.
        - NEVER mention the agency's standard minimum charges.
        - COST DISCLOSURE OVERRIDE: If the user asks for the cost, check the `estimated_cost` in the CURRENT PROJECT STATE. If it is greater than 0, you MUST explicitly tell the user that exact amount. Do not deflect.
        - HANDLING BUDGET MISMATCHES: If you reveal an `estimated_cost` that is significantly higher than the `client_budget` (e.g., a $135k estimate for a $100 budget), politely explain that the cost is driven by their current `agreed_requirements`. Immediately ask if they would like to remove features or reduce the scope to lower the price.
        - MISSING PROJECT CONTEXT: If the current project details (such as `requirements`, `estimated_cost`, or `budget`) are entirely unknown or empty, politely ask the user if they would like to start a new project or, if they are returning, to provide their existing `project_id` so you can retrieve their details. 
        - REQUIREMENT GATHERING: If starting a new project (or if the `estimated_cost` is 0/missing after confirming no project ID), politely acknowledge their message and IMMEDIATELY ask them to elaborate on their technical requirements, features, and overall project goals before any pricing is discussed.
        - If a client asks to build an app similar to an existing, well-known app, use your internal knowledge to list the core functionalities of the specific app they requested. Then, ask the client which of those specific features they want in their version, and if they require any custom additions.
        - If the client agrees with all proposed requirements, list ALL the agreed-upon requirements in the `requirements` parameter.
        
        EXAMPLES OF EXPECTED BEHAVIOR AND JSON OUTPUT:
        {json.dumps(llm_response_example, indent=2)}
        """

        self.model_name = model_name

    async def generate_text(self, prompt:str,context_data:dict[str,Any],old_chats:list[ChatMessage],tools: list|None = None)->LLMResponse:
        gemini_content=[]
        dynamic_system_instruction = self.detailed_instructions

        if context_data:
            dynamic_system_instruction += "\n\n--- CURRENT PROJECT STATE ---\n"
            dynamic_system_instruction += "Use this current data to inform your response:\n"

            for key, value in context_data.items():
                # Replace underscores with spaces for better LLM readability
                formatted_key = key.replace('_', ' ').title()
                dynamic_system_instruction += f"- {formatted_key}: {value}\n"

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
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=LLMResponse,
            system_instruction=dynamic_system_instruction,
            temperature=0.1,
            tools=tools,
        )
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=gemini_content,
            config=config
        )

        return LLMResponse.model_validate_json(response.text or "")