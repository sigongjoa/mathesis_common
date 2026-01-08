import functools
import logging
import time
from typing import Any, Callable, Type, Tuple, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)

def retry_llm_call(
    max_attempts: int = 3,
    min_seconds: float = 1,
    max_seconds: float = 10,
    retry_on: Tuple[Type[Exception], ...] = (Exception,),
    delay: Optional[float] = None # For compatibility with tests
):
    """
    Decorator to retry LLM calls with exponential backoff.
    Uses tenacity for robust retry logic.
    """
    
    # If delay is provided, we use fixed wait for tests/simplicity
    if delay:
        wait_strategy = wait_exponential(multiplier=delay, min=delay, max=delay)
    else:
        wait_strategy = wait_exponential(multiplier=min_seconds, min=min_seconds, max=max_seconds)

    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_strategy,
            retry=retry_if_exception_type(retry_on),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True
        )
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator
