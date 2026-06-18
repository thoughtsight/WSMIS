import traceback
import functools
import streamlit as st
from services.logger import logger

class WSMISError(Exception):
    """Base class for all custom WSMIS exceptions."""
    pass

class ConfigurationError(WSMISError):
    """Raised when the application configuration is invalid or missing."""
    pass

class LoaderError(WSMISError):
    """Raised when an error occurs during data extraction or loading."""
    pass

class CalculationError(WSMISError):
    """Raised when a business calculation fails."""
    pass

class AggregationError(WSMISError):
    """Raised when an error occurs during data aggregation."""
    pass

def with_error_context(exception_cls=WSMISError):
    """
    Decorator that catches any exception within a service/loader function,
    logs the complete context, and raises a structured exception.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # If it's already a structured error, don't wrap it again
                if isinstance(e, WSMISError):
                    raise
                func_name = func.__name__
                err_msg = f"Error in {func_name}: {str(e)}"
                logger.error(err_msg)
                logger.error(traceback.format_exc())
                raise exception_cls(err_msg) from e
        return wrapper
    return decorator

def safe_render(render_func, *args, **kwargs):
    """
    Wraps a dashboard rendering function to catch and log exceptions safely,
    preventing the entire application from crashing.
    Displays friendly UI errors based on the structured exception type.
    """
    try:
        render_func(*args, **kwargs)
    except ConfigurationError as e:
        logger.error(f"Configuration Error rendering page: {str(e)}")
        st.error(f"⚠️ **Configuration Error**: {str(e)}")
    except LoaderError as e:
        logger.error(f"Loader Error rendering page: {str(e)}")
        st.error(f"🔌 **Data Loading Error**: Unable to fetch required data. Please check connection to Google Sheets. ({str(e)})")
    except CalculationError as e:
        logger.error(f"Calculation Error rendering page: {str(e)}")
        st.error(f"🧮 **Calculation Error**: A mathematical operation failed. ({str(e)})")
    except AggregationError as e:
        logger.error(f"Aggregation Error rendering page: {str(e)}")
        st.error(f"📊 **Data Processing Error**: Failed to summarize dashboard metrics. ({str(e)})")
    except Exception as e:
        logger.error(f"Unexpected Error rendering page: {str(e)}")
        logger.error(traceback.format_exc())
        st.error(f"🚨 **Unexpected Application Error**: {str(e)}")
        with st.expander("View Error Details"):
            st.code(traceback.format_exc())
    except BaseException:
        # Catches Streamlit-internal StopException / RerunException
        raise
