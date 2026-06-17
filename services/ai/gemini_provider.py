import os
from typing import Optional
from services.logger import app_logger as logger

def generate_from_gemini(prompt: str, system_instruction: str, model: str, api_key: Optional[str] = None) -> str:
    """
    Generates a Markdown report via Google's Generative AI.
    Handles timeouts, rate limits, and authentication errors gracefully.
    """
    try:
        import google.generativeai as genai
        from google.api_core import exceptions
    except ImportError:
        logger.error("google-generativeai package is not installed. Falling back to offline.")
        return ""

    key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        logger.error("GEMINI_API_KEY / GOOGLE_API_KEY not set. Falling back to offline.")
        return ""

    try:
        genai.configure(api_key=key)
        
        generation_config = genai.types.GenerationConfig(
            temperature=0.2,
            max_output_tokens=4000,
        )
        
        gm = genai.GenerativeModel(
            model_name=model,
            system_instruction=system_instruction,
            generation_config=generation_config
        )
        
        resp = gm.generate_content(prompt)
        return (resp.text or "").strip()
        
    except exceptions.InvalidArgument as e:
        logger.error(f"Gemini Invalid Argument (Check API Key): {e}")
    except exceptions.ResourceExhausted as e:
        logger.error(f"Gemini Rate Limit Exceeded: {e}")
    except exceptions.DeadlineExceeded as e:
        logger.error(f"Gemini Timeout Exceeded: {e}")
    except Exception as e:
        logger.error(f"Gemini Unexpected Error: {e}")
        
    return ""
