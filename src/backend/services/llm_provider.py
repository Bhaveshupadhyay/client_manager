import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, TypeVar, Type
import logging

from google import genai
from google.genai import types
from pydantic import BaseModel

from backend.models.llm import LLMResponse
from backend.schemas.chat import ChatMessage

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class LLmProvider(ABC):
    DEFAULT_INSTRUCTIONS = """
    You are an AI assistant for a software development agency. Your job is to analyze the user's input, extract data, and draft a polite, helpful response.

    DATA EXTRACTION AND SCHEMA RULES:
    - `intent_type`: Classify the user's immediate request into one of the following:
      * `budget`: Questions or updates regarding pricing, budget, or costs.
      * `requirements`: Feature requests, tech stack choices, or scope revisions.
      * `general_faq`: General inquiries, greetings, or casual talk.
    - `text`: Your polite response to the user.
    - `budget`: If the user explicitly mentions a budget or amount, extract it here as a string of numbers (no symbols, e.g., "50000").
    - `timeline`: If the user mentions a duration (e.g., "3 months"), extract the numeric value and the unit.
    - `requirements`: If new features are described, list them here.
    - `project_id`: If the user provides a project ID, extract it.
    - `reply_needed`: Set to true if a text reply is being sent to the user.

    CONVERSATIONAL RULES:
    - NEVER reject a project outright based on a low budget.
    - NEVER mention the agency's standard minimum charges.
    - COST DISCLOSURE: If the user asks for the cost and `Estimated Cost` in the project state is greater than 0, you MUST explicitly state that exact amount in your reply.
    - BUDGET MISMATCH: If the estimated cost is significantly higher than the client budget, explain that the cost is driven by the requirements and ask if they want to reduce the scope.
    - REQUIREMENT GATHERING: For new projects, ask them to elaborate on technical requirements, features, and overall goals before discussing pricing.
    """

    def __init__(self, detailed_instructions: str | None = None):
        self.detailed_instructions = detailed_instructions or self.DEFAULT_INSTRUCTIONS

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        context_data: dict[str, Any],
        old_chats: list[ChatMessage],
        tools: list | None = None,
        system_instruction: str | None = None
    ) -> LLMResponse:
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str | list[dict[str, Any]],
        response_schema: Type[T],
        system_instruction: str | None = None,
        temperature: float = 0.1,
    ) -> T:
        pass


class GeminiLLmProvider(LLmProvider):
    def __init__(self, model_name: str = "gemini-3.1-flash-lite", detailed_instructions: str | None = None):
        super().__init__(detailed_instructions)
        self.client = genai.Client()
        self.model_name = model_name

    async def generate_text(
        self,
        prompt: str,
        context_data: dict[str, Any],
        old_chats: list[ChatMessage],
        tools: list | None = None,
        system_instruction: str | None = None
    ) -> LLMResponse:
        gemini_content = []
        dynamic_system_instruction = system_instruction or self.detailed_instructions

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

    async def generate_structured(
        self,
        prompt: str | list[dict[str, Any]],
        response_schema: Type[T],
        system_instruction: str | None = None,
        temperature: float = 0.1,
    ) -> T:
        dynamic_system_instruction = system_instruction or self.detailed_instructions
        
        gemini_content: Any
        if isinstance(prompt, list):
            gemini_content = prompt
        else:
            gemini_content = [{
                "role": "user",
                "parts": [{"text": prompt}]
            }]

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            system_instruction=dynamic_system_instruction,
            temperature=temperature,
        )
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=gemini_content,
            config=config
        )

        return response_schema.model_validate_json(response.text or "{}")