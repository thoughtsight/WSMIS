import os
from services.error_handler import ConfigurationError, LoaderError
from services.logger import app_logger
from utils.constants import SERVICE_ACCOUNT

# Environment configuration
# Default to "production" for deployment safety
ENVIRONMENT = os.getenv("WSMIS_ENV", "production")
DEBUG = ENVIRONMENT == "development"

def get_google_credentials():
    """
    Retrieves Google Sheets service account credentials.
    Uses the following priority order:
    1. Streamlit Secrets (st.secrets["service_account"])
    2. Environment Variable (GOOGLE_SERVICE_ACCOUNT_JSON)
    3. Local file (service_account.json)
    """
    import json
    from google.oauth2.service_account import Credentials

    SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']

    def _validate_creds_dict(creds_data, source):
        for field in required_fields:
            if field not in creds_data:
                app_logger.error(f"[CredCheck] {source}: missing required field '{field}'")
                from services.error_handler import ConfigurationError
                raise ConfigurationError(f"{source} missing required field: {field}")
        return Credentials.from_service_account_info(creds_data, scopes=SCOPES)

    # 1. Streamlit Secrets (Cloud/Deployment)
    try:
        import streamlit as st
        if "service_account" in st.secrets:
            app_logger.info("[GSheets] Authenticating via Streamlit Secrets")
            return _validate_creds_dict(dict(st.secrets["service_account"]), "Streamlit Secret 'service_account'")
    except Exception:
        pass

    # 2. Environment Variable
    service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if service_account_json:
        app_logger.info("[GSheets] Authenticating via GOOGLE_SERVICE_ACCOUNT_JSON env var")
        try:
            creds_data = json.loads(service_account_json)
            return _validate_creds_dict(creds_data, "GOOGLE_SERVICE_ACCOUNT_JSON")
        except json.JSONDecodeError as e:
            from services.error_handler import ConfigurationError
            raise ConfigurationError(f"Invalid JSON in GOOGLE_SERVICE_ACCOUNT_JSON: {e}")

    # 3. Local file
    if os.path.exists(SERVICE_ACCOUNT):
        app_logger.info(f"[GSheets] Authenticating via local file: {SERVICE_ACCOUNT}")
        with open(SERVICE_ACCOUNT, 'r', encoding='utf-8') as f:
            try:
                creds_data = json.load(f)
                return _validate_creds_dict(creds_data, "Service account file")
            except json.JSONDecodeError as e:
                from services.error_handler import ConfigurationError
                raise ConfigurationError(f"Service account file is not valid JSON: {e}")

    from services.error_handler import ConfigurationError
    raise ConfigurationError(
        "Google credentials not found. Set one of:\n"
        "- Streamlit Secret: service_account (JSON)\n"
        "- Environment Variable: GOOGLE_SERVICE_ACCOUNT_JSON (JSON string)\n"
        "- Local file: service_account.json (development only)"
    )

def validate_google_credentials():
    """
    Validates Google Sheets service account credentials during startup.
    Fails fast to prevent the app from starting with broken credentials.
    """
    app_logger.info("[CredCheck] Starting Google credential validation")
    get_google_credentials()
    app_logger.info("[CredCheck] Google credentials validated OK")

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
