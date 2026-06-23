from config.ai_config import get_ai_config

def get_ai_client():
    """
    Returns an instantiated AI client based on the current configuration.
    Currently returns an Anthropic client for backward compatibility,
    but is designed to support generic providers (e.g. OpenRouter) in the future.
    """
    config = get_ai_config()
    
    # In the future, we can branch here based on config["provider"].
    # For today, as requested, we return the existing Anthropic implementation
    # configured with the possibly generic settings.
    import anthropic
    
    key = config["api_key"]
    if not key:
        # Anthropic SDK can sometimes automatically pick up the env var if we pass None,
        # but if we have no key at all, it's better to let it fail or we can pass it if we have it.
        pass
        
    kwargs = {}
    if key:
        kwargs["api_key"] = key
    if config["base_url"]:
        kwargs["base_url"] = config["base_url"]
        
    return anthropic.Anthropic(**kwargs)

def get_default_model() -> str:
    """Returns the default model configured in the environment or secrets."""
    config = get_ai_config()
    return config["model"]
