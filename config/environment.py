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
    Checks:
    1. Service account file exists
    2. Credential file is readable
    3. Authentication is possible
    
    Fails fast with ConfigurationError if invalid, preventing the app from starting
    with broken credentials.
    """
    # Check if service account file exists
    if not os.path.exists(SERVICE_ACCOUNT):
        raise ConfigurationError(f"Service account file not found: {SERVICE_ACCOUNT}")
    
    # Check if file is readable
    if not os.access(SERVICE_ACCOUNT, os.R_OK):
        raise ConfigurationError(f"Service account file is not readable: {SERVICE_ACCOUNT}")
    
    # Attempt authentication to verify credentials are valid
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        import json
        
        SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Try to load and parse the JSON file to verify it's valid
        with open(SERVICE_ACCOUNT, 'r') as f:
            creds_data = json.load(f)
        
        # Verify required fields exist
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in creds_data:
                raise ConfigurationError(f"Service account file missing required field: {field}")
        
        # Attempt to create Credentials object
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT, scopes=SCOPES)
        
        # Attempt to authorize with gspread
        client = gspread.authorize(creds)
        
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Service account file is not valid JSON: {e}")
    except KeyError as e:
        raise ConfigurationError(f"Service account file missing required field: {e}")
    except Exception as e:
        raise ConfigurationError(f"Google Sheets credential validation failed: {e}")

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
