import os
import sys
import pytest
from unittest.mock import MagicMock
from streamlit.testing.v1 import AppTest

# Mock sklearn to bypass Windows Application Control DLL load failure
sys.modules['sklearn'] = MagicMock()
sys.modules['sklearn.linear_model'] = MagicMock()
sys.modules['sklearn.linear_model'].LinearRegression = MagicMock()

# Set required environment variable for fail-fast configuration
os.environ["WSMIS_ENV"] = "production"

PAGES = [
    "Cockpit", "Overview", "Labour", "Parts Executive", "Parts Detail", "Margin", "Discounts",
    "Leakage Center", "Sales Mix", "Advisors", "Advisor MoM", "Locations",
    "Trends", "Targets", "Reports", "Executive", "Expense Analysis",
    "Profit & Loss", "Internal Audit", "Audit Intelligence"
]

@pytest.fixture(scope="module")
def app_test():
    """Initializes AppTest once for the module to save load time."""
    at = AppTest.from_file("app.py", default_timeout=60)
    return at

@pytest.mark.parametrize("page", PAGES)
def test_dashboard_page_loads(app_test, page):
    """
    Simulates navigating to each dashboard page.
    Verifies that no uncaught exceptions are raised (e.g. ConfigurationError, 
    LoaderError, AggregationError, CalculationError, missing imports).
    """
    app_test.session_state["current_page"] = page
    app_test.run(timeout=300)
    
    # Assert no exceptions occurred during render
    assert not app_test.exception, f"Exception encountered on page '{page}': {app_test.exception[0] if app_test.exception else 'Unknown Error'}"
