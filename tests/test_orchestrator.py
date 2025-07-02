import pytest
import asyncio
import sys
import os
from dotenv import load_dotenv

# Add the project root to sys.path to allow imports from the 'orchestrator' package
# when running this script directly.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from orchestrator.orchestrator import Orchestrator

# Dummy agent classes for testing
class DummyAgent:
    async def handle(self, task):
        return {"handled_by": self.__class__.__name__, "task": task}

class DataRetrievalAgent(DummyAgent):
    pass

class ReportGenerationAgent(DummyAgent):
    pass

class AnalysisDashboardAgent(DummyAgent):
    pass

class AnalysisAgent(DummyAgent):
    pass

@pytest.fixture
def orchestrator_instance(monkeypatch):
    load_dotenv() # Load .env file from project root
    agents = {
        "web_search": DummyAgent(),
        "data_retrieval": DataRetrievalAgent(),
        "analysis": AnalysisAgent(),
        "report_generation": ReportGenerationAgent(),
        "analysis_dashboard": AnalysisDashboardAgent(),
    }
    api_key = os.getenv("GEMINI_API_KEY", "DUMMY_API_KEY_FOR_PYTEST")
    return Orchestrator(agents, gemini_api_key=api_key, default_agent_type="web_search")

@pytest.mark.asyncio
async def test_simple_task_routing(orchestrator_instance):
    task = {
        "type": "web_search",
        "payload": {"query": "test"},
        "user": "U1",
        "context": {}
    }
    result = await orchestrator_instance.route_task(task)
    assert result["handled_by"] == "DummyAgent"
    assert result["task"]["type"] == "web_search"

@pytest.mark.asyncio
async def test_no_agent_found(orchestrator_instance):
    task = {
        "type": "nonexistent_agent",
        "payload": {},
        "user": "U1",
        "context": {}
    }
    result = await orchestrator_instance.route_task(task)
    assert "error" in result
    assert "nonexistent_agent" in result["error"]

@pytest.mark.asyncio
async def test_task_classification_fallback(orchestrator_instance, monkeypatch):
    # Simulate Gemini model not being available or failing
    monkeypatch.setattr(orchestrator_instance, "gemini_model", None)
    
    text = "generate a sales report for last quarter"
    task = await orchestrator_instance.classify_task(text, user="U1", channel="C1")
    
    assert task["type"] == "report_generation" # Based on fallback rules
    assert task["payload"]["query"] == text
    assert task["user"] == "U1"
    assert task["context"]["channel"] == "C1"

@pytest.mark.asyncio
async def test_task_decomposition_and_chaining(orchestrator_instance, monkeypatch):
    # Mock the Gemini model's response for decomposition
    class MockGeminiResponse:
        def __init__(self, text):
            self.text = text

    async def mock_generate_content_async(prompt):
        if "decompose it into a list of sub-task dictionaries" in prompt:
            # Simulate Gemini decomposing a "complex_report" task
            return MockGeminiResponse("""
                [
                    {"type": "data_retrieval", "payload": {"source": "database", "query_details": "sales data Q3"}},
                    {"type": "analysis", "payload": {"analysis_type": "trend"}},
                    {"type": "report_generation", "payload": {"report_format": "pdf"}}
                ]
            """)
        elif "determine the best agent type" in prompt: # For _get_agent_type_from_gemini
            if "data_retrieval" in prompt: return MockGeminiResponse("data_retrieval")
            if "analysis" in prompt: return MockGeminiResponse("analysis")
            if "report_generation" in prompt: return MockGeminiResponse("report_generation")
        return MockGeminiResponse("web_search") # Default for other calls

    if orchestrator_instance.gemini_model: # Only mock if a model object exists
        monkeypatch.setattr(orchestrator_instance.gemini_model, "generate_content_async", mock_generate_content_async)
    else: # If no gemini model, this test might not be fully effective for decomposition
        pytest.skip("Skipping decomposition test as Gemini model is not initialized.")
        return

    # Original complex task
    task = {
        "type": "complex_report", # This type might be initially classified or given
        "payload": {"topic": "Q3 Sales Performance", "output_format": "pdf"},
        "user": "U1",
        "context": {}
    }

    # We are testing the orchestrator's handle_task method which uses decompose_task
    final_result = await orchestrator_instance.handle_task(task)

    assert "results" in final_result
    results_list = final_result["results"]
    assert len(results_list) == 3

    # Check if agents were called in order and results chained (implicitly by payload)
    assert results_list[0]["handled_by"] == "DataRetrievalAgent"
    assert results_list[0]["task"]["payload"]["source"] == "database"

    assert results_list[1]["handled_by"] == "AnalysisAgent"
    # Check if the previous result (from DataRetrievalAgent) is in the input for AnalysisAgent
    assert "input" in results_list[1]["task"]["payload"]
    assert results_list[1]["task"]["payload"]["input"]["handled_by"] == "DataRetrievalAgent"

    assert results_list[2]["handled_by"] == "ReportGenerationAgent"
    # Check if the previous result (from AnalysisAgent) is in the input for ReportGenerationAgent
    assert "input" in results_list[2]["task"]["payload"]
    assert results_list[2]["task"]["payload"]["input"]["handled_by"] == "AnalysisAgent"

    # Check the final status message
    assert final_result.get("final_status") == "Completed with errors or multiple results" or \
           (len(results_list) == 3 and all("error" not in r for r in results_list))

    # If all succeeded, the orchestrator's handle_task returns the last result directly
    if all(isinstance(r, dict) and "error" not in r for r in results_list):
         assert final_result["handled_by"] == "ReportGenerationAgent"

# Main section to manually test the agent logic
if __name__ == "__main__":
    async def main():
        load_dotenv() # Ensure .env is loaded for manual script execution
        agents = {
            "web_search": DummyAgent(),
            "data_retrieval": DataRetrievalAgent(),
            "analysis": AnalysisAgent(),
            "report_generation": ReportGenerationAgent(),
            "analysis_dashboard": AnalysisDashboardAgent(),
        }
        api_key = os.getenv("GEMINI_API_KEY", "DUMMY_API_KEY_FOR_MANUAL_RUN")
        if api_key == "DUMMY_API_KEY_FOR_MANUAL_RUN":
            print("Warning: GEMINI_API_KEY not found in environment. Using a dummy key for manual run. API calls will likely fail.")
        
        orchestrator = Orchestrator(agents, gemini_api_key=api_key, default_agent_type="web_search")

        # Test simple routing
        task = {
            "type": "web_search",
            "payload": {"query": "manual test"},
            "user": "U2",
            "context": {}
        }
        result = await orchestrator.route_task(task)
        print("Simple Routing Result:", result)

        # Test missing agent
        task = {
            "type": "unknown",
            "payload": {},
            "user": "U2",
            "context": {}
        }
        result = await orchestrator.route_task(task)
        print("Missing Agent Result:", result)

        # Test task classification (will use fallback if Gemini key is dummy/invalid)
        print("\n--- Testing Task Classification ---")
        classified_task = await orchestrator.classify_task("Generate a sales report for Q1", user="U_manual", channel="C_manual")
        print("Classified Task:", classified_task)
        if classified_task:
            routing_result_after_classification = await orchestrator.route_task(classified_task)
            print("Routing Result after Classification:", routing_result_after_classification)

        # Test complex task handling (will likely not decompose fully with dummy key, but test flow)
        print("\n--- Testing Complex Task Handling (handle_task) ---")
        complex_task_def = {"type": "complex_report", "payload": {"details": "quarterly financial summary and forecast"}}
        # Manually classify it first for the test, or let handle_task do its thing
        # For this manual test, let's assume it's already classified or we use a specific type
        complex_task_result = await orchestrator.handle_task(complex_task_def)
        print("Complex Task Result:", complex_task_result)

    asyncio.run(main())