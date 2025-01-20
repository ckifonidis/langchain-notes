from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
import os

load_dotenv()

def model_config_error(message):
    """Raise a configuration error with the given message"""
    raise ValueError(f"Model configuration error: {message}")

def use_model(model_name):
    """Helper function to create ChatOpenAI instances for different models.
    
    Args:
        model_name (str): Model identifier (e.g. "DEEPSEEK", "GPT4")
    
    Returns:
        ChatOpenAI: Configured chat model instance
    
    Raises:
        ValueError: If model configuration is invalid or model_name is not recognized
    """
    model_name = model_name.upper()
    
    if model_name == "DEEPSEEK":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = os.getenv("DEEPSEEK_BASE_URL")
        
        if not api_key:
            model_config_error("DEEPSEEK_API_KEY environment variable is required")
        if not base_url:
            model_config_error("DEEPSEEK_BASE_URL environment variable is required")
            
        return ChatOpenAI(
            model="deepseek-chat",
            api_key=api_key,
            base_url=base_url
        )
        
    elif model_name == "GPT4":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            model_config_error("OPENAI_API_KEY environment variable is required")
            
        return ChatOpenAI(
            model="gpt-4",
            api_key=api_key
        )
        
    elif model_name == "GPT4O":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            model_config_error("OPENAI_API_KEY environment variable is required")
            
        return ChatOpenAI(
            model="gpt-4o",
            api_key=api_key
        )
        
    else:
        raise ValueError(f"Unknown model: {model_name}")

# Example usage:
# model = use_model("DEEPSEEK")
# model = use_model("GPT4")
