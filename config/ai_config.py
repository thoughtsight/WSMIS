import os
import streamlit as st

def get_ai_config():
    """
    Reads from .streamlit/secrets.toml for generic AI settings.
    Falls back to existing ANTHROPIC_API_KEY for backward compatibility.
    """
    config = {
        "provider": "anthropic",
        "model": "claude-3-5-sonnet-20241022",
        "api_key": None,
        "base_url": None
    }
    
    # Try reading from streamlit secrets
    try:
        if "AI_PROVIDER" in st.secrets:
            config["provider"] = st.secrets["AI_PROVIDER"]
        if "AI_MODEL" in st.secrets:
            config["model"] = st.secrets["AI_MODEL"]
        if "AI_API_KEY" in st.secrets:
            config["api_key"] = st.secrets["AI_API_KEY"]
        if "AI_BASE_URL" in st.secrets:
            config["base_url"] = st.secrets["AI_BASE_URL"]
    except Exception:
        pass
        
    # Fallback overrides from environment
    if os.getenv("AI_PROVIDER"):
        config["provider"] = os.getenv("AI_PROVIDER")
    if os.getenv("AI_MODEL"):
        config["model"] = os.getenv("AI_MODEL")
    if os.getenv("AI_API_KEY"):
        config["api_key"] = os.getenv("AI_API_KEY")
    if os.getenv("AI_BASE_URL"):
        config["base_url"] = os.getenv("AI_BASE_URL")
        
    # Backward compatibility for Anthropic
    if not config["api_key"]:
        try:
            config["api_key"] = st.secrets.get("ANTHROPIC_API_KEY")
        except Exception:
            pass
        if not config["api_key"]:
            config["api_key"] = os.getenv("ANTHROPIC_API_KEY")
            
    return config
