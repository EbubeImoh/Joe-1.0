from agents.web_search_agent import WebSearchAgent
from agents.data_retrieval_agent import DataRetrievalAgent
from agents.report_generation_agent import ReportGenerationAgent
from agents.analysis_dashboard_agent import AnalysisDashboardAgent
from agents.llm_response_agent import LLMResponseAgent
from orchestrator.orchestrator import Orchestrator
import os
from dotenv import load_dotenv

load_dotenv()

agents = {
    "web_search": {
        "instance": WebSearchAgent(),
        "description": WebSearchAgent.description
    },
    "data_retrieval": {
        "instance": DataRetrievalAgent(),
        "description": DataRetrievalAgent.description
    },
    "report_generation": {
        "instance": ReportGenerationAgent(),
        "description": ReportGenerationAgent.description
    },
    "analysis_dashboard": {
        "instance": AnalysisDashboardAgent(),
        "description": AnalysisDashboardAgent.description
    },
    "llm_response": {
        # LLMResponseAgent requires the gemini_model, so we will add it after Orchestrator is initialized
        "instance": None,
        "description": LLMResponseAgent.description
    },
}

gemini_api_key = os.getenv("GEMINI_API_KEY")

orchestrator = Orchestrator(agents, gemini_api_key=gemini_api_key, default_agent_type="llm_response")

# Now that orchestrator.gemini_model is available, set the llm_response agent instance
if orchestrator.gemini_model:
    agents["llm_response"]["instance"] = LLMResponseAgent(orchestrator.gemini_model)
    orchestrator.agents["llm_response"] = agents["llm_response"]["instance"]
else:
    # If Gemini is not available, provide a fallback handler
    class DummyLLMResponseAgent:
        description = "Fallback LLM agent when Gemini is unavailable."
        async def handle(self, task):
            return {"report": "LLM is not available.", "data": []}
    agents["llm_response"]["instance"] = DummyLLMResponseAgent()
    orchestrator.agents["llm_response"] = agents["llm_response"]["instance"]
