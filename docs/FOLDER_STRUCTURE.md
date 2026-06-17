# Folder Structure

```text
WSMIS/
├── app.py                # Main Streamlit router and cache initialization
├── config/               # Application-level environment and path configurations
├── docs/                 # System architecture and deployment documentation
├── logs/                 # Output log files handled by logs/logger.py
├── pages/                # Streamlit dashboard controllers (Cockpit, Margin, etc)
├── services/             # Middle-tier orchestration for financial logic
├── static/               # Assets (images, custom CSS files)
├── templates/            # HTML templates (if used for custom injection)
├── tests/                # Automated testing suites (Pytest, Streamlit AppTest)
├── ui/                   # Reusable visual components (KPI cards, formatters, tables)
└── utils/                # Data processors, filters, constants, loaders, and math engines
    └── calculations/     # Core mathematical libraries (revenue, discount, etc)
```
