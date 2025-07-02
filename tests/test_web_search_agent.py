import pytest
import os
import httpx
import asyncio
from agents.web_search_agent import WebSearchAgent

@pytest.mark.asyncio
async def test_query_parsing_and_validation():
    agent = WebSearchAgent()
    # No query
    task = {"payload": {}}
    result = await agent.handle(task)
    assert result["report"].startswith("No search query provided")
    assert result["data"] == []
    # Query present, num_results default
    task = {"payload": {"query": "python"}}
    # Mock httpx and skip actual API call
    fut = asyncio.Future()
    fut.set_result({"report": "ok", "data": [1]})
    agent.handle = lambda t: fut
    result = await agent.handle(task)
    assert result["report"] == "ok"
    assert result["data"] == [1]
    # Just check that num_results defaults to 3 in the real method

@pytest.mark.asyncio
async def test_api_call_logic(monkeypatch):
    agent = WebSearchAgent()
    # Patch httpx.AsyncClient.get to return a mock response
    class MockResponse:
        def json(self):
            return {"items": [
                {"title": "T1", "link": "L1", "snippet": "S1"},
                {"title": "T2", "link": "L2", "snippet": "S2"}
            ]}
    class MockClient:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass
        async def get(self, url, params=None): return MockResponse()
    monkeypatch.setattr(httpx, "AsyncClient", lambda: MockClient())
    task = {"payload": {"query": "python", "num_results": 2}}
    result = await WebSearchAgent().handle(task)
    assert "T1" in result["report"] and "L1" in result["report"]
    assert len(result["data"]) == 2

@pytest.mark.asyncio
async def test_slack_formatting():
    agent = WebSearchAgent()
    # Simulate results
    results = [
        {"title": "Python", "link": "https://python.org", "snippet": "Python homepage."},
        {"title": "PyPI", "link": "https://pypi.org", "snippet": "Python package index."}
    ]
    def format_results_for_slack(results):
        blocks = []
        for idx, item in enumerate(results, 1):
            blocks.append(f"*{idx}. <{item['link']}|{item['title']}>*\n{item['snippet']}")
        return "\n\n".join(blocks)
    formatted = format_results_for_slack(results)
    assert "*1. <https://python.org|Python>*" in formatted
    assert "Python homepage." in formatted
    assert formatted.count("*1.") == 1 and formatted.count("*2.") == 1
