# WSMIS Installation Guide

This guide covers setting up WSMIS for local development and testing.

## Prerequisites

- **Python**: Version 3.9 through 3.12 is recommended.
- **Git**: To clone the repository.
- **Google Service Account**: Required for reading Google Sheets data.
- **internal_audit_app.py**: A legacy module that must remain in the project root. It is dynamically loaded for the Internal Audit application features.

## 1. Clone the Repository

```bash
git clone https://github.com/your-org/wsmis.git
cd wsmis
```

## 2. Virtual Environment Setup

It is highly recommended to isolate dependencies using a virtual environment.

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install Dependencies

Install the core production dependencies:
```bash
pip install -r requirements.txt
```

If you are a developer or running tests, also install the development dependencies:
```bash
pip install -r requirements-dev.txt
```

## 4. Google Credentials

WSMIS reads data from Google Sheets and requires an authenticated service account.

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the **Google Sheets API** and **Google Drive API**
3. Create a Service Account and download the JSON key.
4. Rename the downloaded file to `service_account.json`
5. Place `service_account.json` in the root directory of the WSMIS project.
6. **Important**: Share your target Google Sheet with the Service Account email address.

## 5. Environment Variables

Copy the environment template:
```bash
cp .env.example .env
```

Edit `.env` to match your environment. At minimum, ensure the `WSMIS_ENV` variable is set.

Alternatively, export it directly in your terminal:
```bash
# Linux/Mac
export WSMIS_ENV=development

# Windows (PowerShell)
$env:WSMIS_ENV="development"
```

> **Note**: If `WSMIS_ENV` is not set, the application will fail-fast with a `ConfigurationError` to prevent accidental production deployments without proper configurations.

## 6. Run the Application

Launch the Streamlit server:
```bash
streamlit run app.py
```

The application will be accessible in your web browser at `http://localhost:8501`.
