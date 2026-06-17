import sys
import time
import functools
import traceback
import pandas as pd
from typing import Callable, Any

from services.logger import error_logger, perf_logger

def log_exception(page: str = "Unknown") -> None:
    """
    Captures the current exception and logs it securely without exposing
    the stack trace to the frontend user.
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()
    
    if not exc_type:
        return
        
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    error_msg = (
        f"Page: {page} | "
        f"Type: {exc_type.__name__} | "
        f"Message: {str(exc_value)}\n"
        f"Traceback:\n{tb_str}"
    )
    
    error_logger.error(error_msg)

def log_performance(page_context: str = "Backend"):
    """
    Decorator to log execution time, processed rows, and status.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            status = "Success"
            rows_processed = 0
            
            try:
                result = func(*args, **kwargs)
                
                # Auto-detect DataFrame returns to count rows
                if isinstance(result, pd.DataFrame):
                    rows_processed = len(result)
                elif isinstance(result, tuple) and any(isinstance(r, pd.DataFrame) for r in result):
                    # Sum rows if multiple dataframes are returned
                    rows_processed = sum(len(r) for r in result if isinstance(r, pd.DataFrame))
                    
                return result
                
            except Exception as e:
                status = "Failure"
                log_exception(page=page_context)
                raise e
            
            finally:
                duration = time.perf_counter() - start_time
                perf_logger.info(
                    f"Context: {page_context} | "
                    f"Function: {func.__name__} | "
                    f"Duration: {duration:.3f}s | "
                    f"Rows: {rows_processed} | "
                    f"Status: {status}"
                )
                
        return wrapper
    return decorator
