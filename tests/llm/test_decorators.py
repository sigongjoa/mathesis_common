import pytest
import time
from unittest.mock import MagicMock
from mathesis_core.llm.decorators import retry_llm_call

def test_retry_successful_on_first_try():
    mock_func = MagicMock(return_value="Success")
    decorated = retry_llm_call(max_attempts=3)(mock_func)
    
    result = decorated("test")
    
    assert result == "Success"
    assert mock_func.call_count == 1

def test_retry_on_exception():
    mock_func = MagicMock(side_effect=[ValueError("Fail"), "Success"])
    decorated = retry_llm_call(max_attempts=3, delay=0.1)(mock_func)
    
    result = decorated("test")
    
    assert result == "Success"
    assert mock_func.call_count == 2

def test_retry_max_attempts_reached():
    mock_func = MagicMock(side_effect=ValueError("Permanent Fail"))
    decorated = retry_llm_call(max_attempts=2, delay=0.1)(mock_func)
    
    with pytest.raises(ValueError, match="Permanent Fail"):
        decorated("test")
    
    assert mock_func.call_count == 2
