import pytest
import json
from pydantic import BaseModel
from mathesis_core.llm.parsers import LLMJSONParser

class MockSchema(BaseModel):
    key: str
    value: int

def test_parse_simple_json():
    response = '{"key": "test", "value": 123}'
    result = LLMJSONParser.parse(response)
    assert result == {"key": "test", "value": 123}

def test_parse_markdown_json():
    response = '```json\n{"key": "test", "value": 123}\n```'
    result = LLMJSONParser.parse(response)
    assert result == {"key": "test", "value": 123}

def test_parse_with_outer_text():
    response = 'Sure! Here is the JSON: {"key": "test", "value": 123} Hope this helps!'
    result = LLMJSONParser.parse(response)
    assert result == {"key": "test", "value": 123}

def test_parse_with_schema():
    response = '{"key": "test", "value": 123}'
    result = LLMJSONParser.parse(response, schema=MockSchema)
    assert result == {"key": "test", "value": 123}

def test_parse_missing_required_keys():
    response = '{"key": "test"}'
    with pytest.raises(ValueError, match="Missing required keys"):
        LLMJSONParser.parse(response, required_keys=["value"])

def test_safe_parse():
    response = 'Invalid JSON'
    result = LLMJSONParser.safe_parse(response, default={"fixed": True})
    assert result == {"fixed": True}
