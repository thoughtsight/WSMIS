import os
from services.error_handler import ConfigurationError, LoaderError
from utils.constants import SERVICE_ACCOUNT

# Environment configuration
# Default to "production" for deployment safety
ENVIRONMENT = os.getenv("WSMIS_ENV", "production")
DEBUG = ENVIRONMENT == "development"

def validate_google_credentials():
    """
    Validates Google Sheets service account credentials during startup.
    Uses the same priority order as utils/loaders.py:
    1. Streamlit Secrets (st.secrets["service_account"])
    2. Environment Variable (GOOGLE_SERVICE_ACCOUNT_JSON)
    3. Local file (service_account.json)

    Only raises ConfigurationError if none of these sources exist or if a
    present source is invalid. Fails fast to prevent the app from starting
    with broken credentials.
    """
    import json
    from google.oauth2.service_account import Credentials

    SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']

    def _validate_creds_dict(creds_data, source):
        for field in required_fields:
            if field not in creds_data:
                raise ConfigurationError(f"{source} missing required field: {field}")
        Credentials.from_service_account_info(creds_data, scopes=SCOPES)

    # 1. Streamlit Secrets (Cloud/Deployment)
    try:
        import streamlit as st
        if "service_account" in st.secrets:
            try:
                creds_data = dict(st.secrets["service_account"])
                _validate_creds_dict(creds_data, "Streamlit Secret 'service_account'")
                return
            except ConfigurationError:
                raise
            except Exception as e:
                raise ConfigurationError(f"Streamlit Secret 'service_account' is invalid: {e}")
    except ConfigurationError:
        raise
    except Exception:
        # st.secrets unavailable (no secrets file); fall through to other sources
        pass

    # 2. Environment Variable (JSON string)
    service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if service_account_json:
        try:
            creds_data = json.loads(service_account_json)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON: {e}")
        _validate_creds_dict(creds_data, "GOOGLE_SERVICE_ACCOUNT_JSON")
        return

    # 3. Local file (development)
    if os.path.exists(SERVICE_ACCOUNT):
        if not os.access(SERVICE_ACCOUNT, os.R_OK):
            raise ConfigurationError(f"Service account file is not readable: {SERVICE_ACCOUNT}")
        try:
            with open(SERVICE_ACCOUNT, 'r') as f:
                creds_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Service account file is not valid JSON: {e}")
        _validate_creds_dict(creds_data, "Service account file")
        return

    # None of the credential sources are available
    raise ConfigurationError(
        "Google credentials not found. Set one of:\n"
        "- Streamlit Secret: service_account (JSON)\n"
        "- Environment Variable: GOOGLE_SERVICE_ACCOUNT_JSON (JSON string)\n"
        "- Local file: service_account.json (development only)"
    )

def validate_environment():
    """
    Validates that the required environment variables are set correctly.
    Fails fast with a ConfigurationError if invalid, preventing the app from starting
    in an undefined state.
    """
    if ENVIRONMENT not in ["development", "production"]:
        raise ConfigurationError(f"Invalid WSMIS_ENV value: '{ENVIRONMENT}'. Must be 'development' or 'production'.")
    
    # Validate Google credentials in production mode
    if ENVIRONMENT == "production":
        validate_google_credentials()
