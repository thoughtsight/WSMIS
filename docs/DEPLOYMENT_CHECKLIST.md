# Pilot Deployment Checklist - WSMIS v1.0.0-RC1

Before initiating the Pilot Deployment for the WSMIS application, ensure that all the following checks are completed by the Infrastructure/Deployment team.

## 1. Environment Readiness
- [ ] Server/Cloud environment provisioned with at least 4GB RAM (8GB Recommended).
- [ ] Python version 3.9+ installed and accessible via `python` or `python3`.
- [ ] Virtual environment created (`python -m venv venv`) and activated.
- [ ] All dependencies installed using `pip install -r requirements.txt`.
- [ ] Dependencies are cleanly resolved without conflicts.

## 2. Secrets & Configuration
- [ ] `.env` file created in the project root by copying `.env.example`.
- [ ] `GOOGLE_CREDENTIALS` securely set in the `.env` file or cloud secrets manager.
- [ ] Application configuration variables (e.g. valid months, targets, etc.) verified with business.

## 3. Data Connectivity
- [ ] Verify that the Google Service Account has `Viewer` access to the WSMIS Google Sheets.
- [ ] Verify the sheet IDs defined in the system are correct and accessible.

## 4. Application Health & Smoke Tests
- [ ] Execute the internal test suite: `python -m pytest tests/ -v`. Verify 100% pass rate.
- [ ] Launch application locally/staging via `streamlit run app.py`.
- [ ] Access the hidden Operations Dashboard (`/system_health` or via side menu if enabled).
- [ ] Verify Memory Usage and Data Metrics load properly on the health page.

## 5. End-User Smoke Tests
- [ ] Dashboard Navigation: Open Cockpit, Labour, Parts, and Expense Analysis.
- [ ] Ensure that filter changes (Location, Month) actively refresh KPI blocks.
- [ ] Verify that an export to CSV functions correctly without throwing 500 errors.

## 6. Security
- [ ] Remove `requirements-dev.txt` dependencies from the production build.
- [ ] Ensure Streamlit debug mode (`[server] runOnSave`) is disabled in `.streamlit/config.toml`.
- [ ] Ensure Google Credentials file/string is not exposed to the frontend.

## Sign-off
**Date:** _______________  
**Approved By:** _______________  
