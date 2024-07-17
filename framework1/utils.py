from typing import Any
from pydantic import BaseModel, validator
import logging
import logging
from dotenv import load_dotenv
from openai import OpenAI
import subprocess
from typing import Any
from pydantic import BaseModel, validator
import requests
import os
import json
# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class Message(BaseModel):
    role: str
    content: str
    tool_calls: list[Any] | None = None




class Function(BaseModel):
    arguments: str
    name: str


class ToolCall(BaseModel):
    id: str
    function: Function | dict
    type: str

    @validator("function", pre=True)
    @classmethod
    def ensure_function_dict(cls, v):
        return v if isinstance(v, dict) else v.dict()


class ToolCallMessage(BaseModel):
    content: str | None = None
    role: str
    tool_calls: list[ToolCall]

from typing import Optional
from pydantic import BaseModel, field_validator
class AssistantMessage(BaseModel):
    role: str
    content: str | None = None
    name: str | None = None
    """An optional name for the participant.

    Provides the model information to differentiate between participants of the same
    role.
    """
    tool_calls: Optional[list[ToolCall]] = []  # if it's None, assign empty list
    """The tool calls generated by the model, such as function calls."""

    @field_validator("role", mode="before")
    def check_role(cls, value):
        if value not in ["assistant"]:
            raise ValueError('Role must be "assistant"')
        return value


class ToolResponseMessage(BaseModel):
    tool_call_id: str
    role: str
    name: str
    content: str


def process_tool_calls(tool_calls, available_tools):
    tool_call_responses = []
    logger.info("Number of function calls: %i", len(tool_calls))
    for tool_call in tool_calls:
        tool_call_id = tool_call.id
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        function_to_call = available_tools.get(function_name)

        try:
            function_response = function_to_call(**function_args)
            logger.info('function name: %s, function args: %s, function response: %s', function_name, function_args, function_response)
            tool_response_message = ToolResponseMessage(
                tool_call_id=tool_call_id,
                role="tool",
                name=function_name,
                content=str(function_response),
            )
            tool_call_responses.append(tool_response_message)
        except Exception as e:
            logger.error(f"Error while calling function <{function_name}>: {e}")

    return tool_call_responses

def send_completion_request(client, messages: list, tools: list = None, available_tools: dict = None, depth: int = 0) -> dict:
    if depth >= 8:
        return None

    if tools is None:
        response = client.chat.completions.create(
            model="gpt-4o", messages=messages
        )
        logger.info('depth: %s, response: %s', depth, response)
        message = AssistantMessage(**response.choices[0].message.model_dump())
        messages.append(message)
        return response

    response = client.chat.completions.create(
        model="gpt-4o", messages=messages, tools=tools, tool_choice="auto"
    )

    tool_calls = response.choices[0].message.tool_calls
    if tool_calls is None:
        logger.info('depth: %s, response: %s', depth, response)
        message = AssistantMessage(**response.choices[0].message.model_dump())
        messages.append(message)
        return response

    logger.info('depth: %s, response: %s', depth, response)
    tool_calls = [
        ToolCall(id=call.id, function=call.function, type=call.type)
        for call in response.choices[0].message.tool_calls
    ]
    tool_call_message = ToolCallMessage(
        content=response.choices[0].message.content,
        role=response.choices[0].message.role,
        tool_calls=tool_calls
    )

    messages.append(tool_call_message)
    tool_responses = process_tool_calls(tool_calls, available_tools)
    messages.extend(tool_responses)
    return send_completion_request(client, messages, tools, available_tools, depth + 1)

def send_prompt(client, messages, content: str, tools, available_tools):
    messages.append(Message(role="user", content=content))
    return send_completion_request(client, messages, tools, available_tools, 0)