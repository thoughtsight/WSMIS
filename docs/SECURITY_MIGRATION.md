# WSMIS Security & Hardening Migration

This document outlines the security audit performed during the V1.0 RC hardening phase.

## 1. Hardcoded Paths
All active modules within `pages/`, `ui/`, `services/`, and `utils/` are free of hardcoded system paths.
The following hardcoded paths were detected in legacy/archived files:
- `archive/internal_audit_app.py`: `SERVICE_ACCOUNT = r"D:\RKM-INDORE\Reports\WSMIS\service_account.json"`
- `archive/audit_frt_search.py`: `D:\RKM-INDORE\Reports\rkm_report_generator_v10.py`

**Recommendation**: Ensure that path configurations rely strictly on the `config/paths.py` relative configuration (e.g. `BASE_DIR`, `DATA_DIR`) or environment variables.

## 2. Credentials & Tokens
- `utils/constants.py` contains: `SERVICE_ACCOUNT = "service_account.json"`
- A `service_account.json` file is present in the repository root.

**Recommendation**: 
1. The physical `service_account.json` file must be added to `.gitignore` to prevent leaking production GCP/Firebase credentials to version control.
2. If WSMIS will be deployed on Streamlit Community Cloud, migrate the contents of the `service_account.json` file into `st.secrets` (`.streamlit/secrets.toml`).
3. For Docker deployments, migrate Google credentials to an environment variable `GOOGLE_APPLICATION_CREDENTIALS`.
