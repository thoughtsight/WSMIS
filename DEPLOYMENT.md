# WSMIS Deployment Guide

This document outlines the standard deployment strategies for WSMIS.

## 1. Streamlit Community Cloud (Recommended for Demos)

1. Fork or push the WSMIS repository to a GitHub repository.
2. Log in to [Streamlit Community Cloud](https://share.streamlit.io/).
3. Click "New App".
4. Select the repository, branch, and `app.py` as the main file path.
5. In the "Advanced Settings", paste the contents of `.env` into the Secrets management window.
6. For `service_account.json`, add it to the Secrets as a stringified JSON dictionary, and modify `utils/loaders.py` to parse it from `st.secrets` if deploying exclusively to the cloud.
7. Deploy!

## 2. Windows Server (Production)

To run Streamlit as a persistent background service on Windows Server, use **NSSM (Non-Sucking Service Manager)**.

1. Install Python and set up your virtual environment as detailed in `INSTALL.md`.
2. Download [NSSM](https://nssm.cc/).
3. Open an Administrator PowerShell and install the service:
   ```powershell
   nssm install WSMIS_Dashboard
   ```
4. In the NSSM GUI:
   - **Path**: `C:\path\to\wsmis\venv\Scripts\python.exe`
   - **Arguments**: `-m streamlit run app.py --server.port 8501 --server.address 0.0.0.0`
   - **Details**: Set startup type to Automatic.
   - **Environment**: Add `WSMIS_ENV=production`.
5. Start the service:
   ```powershell
   nssm start WSMIS_Dashboard
   ```

## 3. Linux (Systemd Daemon)

On Ubuntu/Debian or RHEL:

1. Create a systemd service file: `sudo nano /etc/systemd/system/wsmis.service`
2. Add the following configuration:
   ```ini
   [Unit]
   Description=WSMIS Streamlit Dashboard
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/opt/wsmis
   Environment="PATH=/opt/wsmis/venv/bin"
   Environment="WSMIS_ENV=production"
   ExecStart=/opt/wsmis/venv/bin/streamlit run app.py --server.port 8501
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable wsmis
   sudo systemctl start wsmis
   ```

## 4. Docker (Placeholder)

A standard Docker containerization strategy.

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV WSMIS_ENV=production
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```
Build and run:
```bash
docker build -t wsmis-dashboard .
docker run -p 8501:8501 -d wsmis-dashboard
```
