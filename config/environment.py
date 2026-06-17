import os
from services.error_handler import ConfigurationError, LoaderError
from services.logger import app_logger
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

    app_logger.info("[CredCheck] Starting Google credential validation")

    def _validate_creds_dict(creds_data, source):
        for field in required_fields:
            if field not in creds_data:
                app_logger.error(f"[CredCheck] {source}: missing required field '{field}'")
                raise ConfigurationError(f"{source} missing required field: {field}")
        Credentials.from_service_account_info(creds_data, scopes=SCOPES)

    # 1. Streamlit Secrets (Cloud/Deployment)
    secrets_available = False
    service_account_key_found = False
    try:
        import streamlit as st
        # Accessing membership forces st.secrets to parse; if no secrets file
        # exists this raises and we fall through to other credential sources.
        service_account_key_found = "service_account" in st.secrets
        secrets_available = True
    except Exception:
        # st.secrets unavailable (no secrets file); treat as not available
        secrets_available = False
        service_account_key_found = False

    app_logger.info(f"[CredCheck] Streamlit secrets available: {'Yes' if secrets_available else 'No'}")
    app_logger.info(f"[CredCheck] service_account key found: {'Yes' if service_account_key_found else 'No'}")

    if service_account_key_found:
        app_logger.info("[CredCheck] Validating via Streamlit Secret 'service_account'")
        try:
            import streamlit as st
            creds_data = dict(st.secrets["service_account"])
            _validate_creds_dict(creds_data, "Streamlit Secret 'service_account'")
            app_logger.info("[CredCheck] Streamlit Secret 'service_account' validated OK")
            return
        except ConfigurationError:
            raise
        except Exception as e:
            app_logger.error(f"[CredCheck] Streamlit Secret 'service_account' is invalid: {e}")
            raise ConfigurationError(f"Streamlit Secret 'service_account' is invalid: {e}")

    # 2. Environment Variable (JSON string)
    service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    env_var_found = bool(service_account_json)
    app_logger.info(f"[CredCheck] GOOGLE_SERVICE_ACCOUNT_JSON found: {'Yes' if env_var_found else 'No'}")
    if env_var_found:
        app_logger.info("[CredCheck] Validating via GOOGLE_SERVICE_ACCOUNT_JSON")
        try:
            creds_data = json.loads(service_account_json)
        except json.JSONDecodeError as e:
            app_logger.error(f"[CredCheck] GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON: {e}")
            raise ConfigurationError(f"GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON: {e}")
        _validate_creds_dict(creds_data, "GOOGLE_SERVICE_ACCOUNT_JSON")
        app_logger.info("[CredCheck] GOOGLE_SERVICE_ACCOUNT_JSON validated OK")
        return

    # 3. Local file (development)
    local_file_exists = os.path.exists(SERVICE_ACCOUNT)
    app_logger.info(f"[CredCheck] Local file exists: {'Yes' if local_file_exists else 'No'}")
    if local_file_exists:
        app_logger.info("[CredCheck] Validating via local service_account file")
        if not os.access(SERVICE_ACCOUNT, os.R_OK):
            app_logger.error(f"[CredCheck] Service account file is not readable: {SERVICE_ACCOUNT}")
            raise ConfigurationError(f"Service account file is not readable: {SERVICE_ACCOUNT}")
        try:
            with open(SERVICE_ACCOUNT, 'r') as f:
                creds_data = json.load(f)
        except json.JSONDecodeError as e:
            app_logger.error(f"[CredCheck] Service account file is not valid JSON: {e}")
            raise ConfigurationError(f"Service account file is not valid JSON: {e}")
        _validate_creds_dict(creds_data, "Service account file")
        app_logger.info("[CredCheck] Service account file validated OK")
        return

    # None of the credential sources are available
    app_logger.error(
        "[CredCheck] No credential source found "
        f"(secrets_available={secrets_available}, service_account_key={service_account_key_found}, "
        f"env_var={env_var_found}, local_file={local_file_exists})"
    )
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
