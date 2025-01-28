from pprint import pprint
from typing import Dict, List, Union

from langchain.schema import BaseMessage


def message_to_dict(message: Union[BaseMessage, tuple]) -> Dict:
    if isinstance(message, tuple):
        if len(message) == 2 and isinstance(message[1], BaseMessage):
            message = message[1]
        else:
            raise ValueError("Invalid tuple format. Expected (role, BaseMessage)")
            
    result = {
        "content": message.content,
        "type": type(message).__name__,
        "additional_kwargs": message.additional_kwargs,
        "id": getattr(message, "id", None),
        "response_metadata": getattr(message, "response_metadata", {}),
        "usage_metadata": getattr(message, "usage_metadata", {}),
        "example": getattr(message, "example", False)
    }
    
    if hasattr(message, "tool_calls"):
        result["tool_calls"] = getattr(message, "tool_calls", [])
        result["tool_call_id"] = getattr(message, "tool_call_id", None)
        
    return result

def visualize_messages(result: Union[BaseMessage, List[BaseMessage], tuple]) -> Union[Dict, List[Dict]]:
    if isinstance(result, list):
        return [message_to_dict(msg) for msg in result]
    elif isinstance(result, tuple):
        return message_to_dict(result)
    return message_to_dict(result)

def print_messages(result: Union[BaseMessage, List[BaseMessage]]) -> None:
    pprint(visualize_messages(result))
