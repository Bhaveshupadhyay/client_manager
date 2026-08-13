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
from backend.core.config import config

from functools import lru_cache
import inspect

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


@lru_cache(maxsize=1)
def _load_faq_text() -> str:
    try:
        faq_path = Path(__file__).parent.parent.parent / "data" / "faq.json"
        if faq_path.exists():
            with open(faq_path, "r", encoding="utf-8") as f:
                faqs = json.load(f)
            if faqs:
                lines = ["\n    GENERAL FAQ: Use the following knowledge base to answer common questions:\n"]
                for item in faqs:
                    lines.append(f"    * {item.get('question')}: {item.get('answer')}\n")
                return "".join(lines)
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load FAQ JSON: {e}")
    return ""


class LLmProvider(ABC):
    DEFAULT_INSTRUCTIONS = """
    You are an AI assistant for a software development agency. Your job is to analyze the user's input, extract data, and draft a polite, helpful response.

    DATA EXTRACTION AND SCHEMA RULES:
    - `intent_type`: Classify the user's immediate request into one of the following:
      * `general_faq`: General inquiries, greetings, or casual talk.
    - `text`: Your polite response to the user.
    - `budget`: If the user explicitly mentions a budget or amount, extract it here as a string of numbers (no symbols, e.g., "50000").
    - `timeline`: If the user mentions a duration (e.g., "3 months"), extract the numeric value and the unit.
    - `reply_needed`: Set to true if a text reply is being sent to the user.

    CONVERSATIONAL RULES:
    - NEVER reject a project outright based on a low budget.
    - NEVER mention the agency's standard minimum charges.
    - COST DISCLOSURE: If the user asks for the cost and `Estimated Cost` in the project state is greater than 0, you MUST explicitly state that exact amount in your reply.
    - BUDGET MISMATCH: If the estimated cost is significantly higher than the client budget, explain that the cost is driven by the requirements and ask if they want to reduce the scope.
    - REQUIREMENT GATHERING: For new projects, ask them to elaborate on technical requirements, features, and overall goals before discussing pricing.
    - GUARDRAILS: Answering coding questions or writing code for the user is strictly prohibited. You may answer general technical questions (e.g., "what is a server?") ONLY if project requirements have already been gathered. If no requirements are gathered yet, politely redirect the user back to discussing their project.
    """

    def __init__(self, detailed_instructions: str | None = None):
        base_instructions = detailed_instructions or self.DEFAULT_INSTRUCTIONS
        self.detailed_instructions = base_instructions + _load_faq_text()

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
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model_name = model_name

    async def _execute_tools(self, tool_list: list, function_calls: list) -> list[dict[str, Any]]:
        tool_map = {}
        for t in tool_list:
            name = getattr(t, "name", None) or getattr(t, "__name__", str(t))
            tool_map[name] = t

        results = []
        for fc in function_calls:
            func_name = getattr(fc, "name", "")
            func_args = getattr(fc, "args", {}) or {}
            if func_name in tool_map:
                target_tool = tool_map[func_name]
                try:
                    if hasattr(target_tool, "ainvoke"):
                        res = await target_tool.ainvoke(func_args)
                    elif inspect.iscoroutinefunction(target_tool):
                        res = await target_tool(**func_args)
                    elif callable(target_tool):
                        res = target_tool(**func_args)
                    else:
                        res = str(target_tool)
                    results.append({"name": func_name, "response": res})
                except Exception as err:
                    logger.error(f"Error executing tool {func_name}: {err}")
                    results.append({"name": func_name, "response": f"Error: {err}"})
        return results

    async def generate_text(
        self,
        prompt: str,
        context_data: dict[str, Any],
        old_chats: list[ChatMessage],
        tools: list | None = None,
        system_instruction: str | None = None
    ) -> LLMResponse:
        gemini_content = []
        dynamic_system_instruction = self.detailed_instructions
        
        if system_instruction:
            dynamic_system_instruction += f"\n\n--- AGENT ROLE & RULES ---\n{system_instruction}"

        if context_data:
            dynamic_system_instruction += "\n\n--- CURRENT PROJECT STATE ---\n"
            dynamic_system_instruction += "Use this current data to inform your response:\n"

            for key, value in context_data.items():
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

        if tools:
            gen_config = types.GenerateContentConfig(
                system_instruction=dynamic_system_instruction,
                temperature=0.1,
                tools=tools,
            )
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=gemini_content,
                config=gen_config
            )
            if getattr(response, "function_calls", None):
                tool_results = await self._execute_tools(tools, response.function_calls)
                logger.info(f"Executed tools: {tool_results}")
                
            structured_config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=LLMResponse,
                system_instruction=dynamic_system_instruction,
                temperature=0.1,
            )
            final_response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=gemini_content,
                config=structured_config
            )
            return LLMResponse.model_validate_json(final_response.text or "{}")

        gen_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=LLMResponse,
            system_instruction=dynamic_system_instruction,
            temperature=0.1,
        )
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=gemini_content,
            config=gen_config
        )

        return LLMResponse.model_validate_json(response.text or "{}")

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

        gen_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            system_instruction=dynamic_system_instruction,
            temperature=temperature,
        )
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=gemini_content,
            config=gen_config
        )

        return response_schema.model_validate_json(response.text or "{}")