# Import necessary modules
import ast
import dotenv
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Logging Setup for CSV Output ---
# Determine project root to place the 'logs' folder correctly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR_NAME = "logs"
LOG_DIR = os.path.join(PROJECT_ROOT, LOG_DIR_NAME)
LOG_FILE_NAME = "orchestrator_log.csv"
LOG_FILE_PATH = os.path.join(LOG_DIR, LOG_FILE_NAME)

LOG_LEVEL = logging.INFO
CSV_HEADER = "timestamp,name,levelname,message\n"
# Simple CSV format. Note: Messages containing double quotes (") or newlines will break this CSV structure.
# For more robust CSV logging, a custom logging.Formatter that handles CSV quoting/escaping would be needed.
LOG_FORMAT = '%(asctime)s,%(name)s,%(levelname)s,"%(message)s"'

# Ensure log directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

# Configure file handler for CSV logging, only if no handlers are already configured
if not logger.handlers:
    # Determine if the CSV header needs to be written
    write_header = not os.path.exists(LOG_FILE_PATH) or os.path.getsize(LOG_FILE_PATH) == 0

    if write_header:
        # If file doesn't exist or is empty, write the header.
        # Open in 'w' mode to create/truncate and write header.
        with open(LOG_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(CSV_HEADER)

    file_handler = logging.FileHandler(LOG_FILE_PATH, mode='a', encoding='utf-8') # Append mode
    file_handler.setLevel(LOG_LEVEL)
    formatter = logging.Formatter(LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
# --- End of Logging Setup ---

# == Orchestrator Module ==
# Try importing google.generativeai for Gemini integration
try:
    import google.generativeai as genai
except ImportError:
    genai = None

class Orchestrator:
    """
    Orchestrator class for routing tasks to agents, optionally using Gemini LLM for classification and decomposition.
    """
    def __init__(self, agents: dict, gemini_api_key: str = None, default_agent_type: str = "llm_response"):
        # Store agents and descriptions from the new structure
        self.agents = {k: v["instance"] for k, v in agents.items()}
        self.agent_descriptions = {k: v["description"] for k, v in agents.items()}
        self.gemini_api_key = gemini_api_key
        self.default_agent_type = default_agent_type
        self.gemini_model = None
        logger.info(f"Agent descriptions for Gemini: {self.agent_descriptions}")
        # --- Gemini Initialization Optimization ---
        api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        logger.info(f"Gemini genai module: {'available' if genai else 'not available'}, api_key: {'set' if api_key else 'not set'}")
        if genai and api_key:
            try:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
                logger.info("Gemini model initialized successfully using API key.")
            except Exception as e:
                logger.warning(f"Could not initialize Gemini model: {e}. Orchestrator will operate without Gemini features.")
        else:
            if not genai:
                logger.warning("google.genai library not found. Orchestrator will operate without Gemini features.")
            elif not api_key:
                logger.info("No Gemini API key provided. Orchestrator will operate without Gemini features unless GOOGLE_API_KEY is set.")
        logger.info(f"Orchestrator initialized with agents: {list(self.agents.keys())}")
        logger.info(f"Gemini model is {'set' if self.gemini_model else 'NOT set'} after initialization.")

    async def route_task(self, task: dict) -> dict:
        """
        Routes a task to the appropriate agent, using Gemini if available. Returns user-friendly error messages if routing fails.
        """
        try:
            agent_type = task.get("type")
            # Use Gemini to determine agent type if available
            if self.gemini_model:
                determined_agent_type = await self._get_agent_type_from_gemini(task)
                if determined_agent_type and determined_agent_type in self.agents:
                    agent_type = determined_agent_type
                elif not agent_type:
                    agent_type = self.default_agent_type
                    logger.warning(f"No agent type in task and Gemini failed to determine one. Defaulting to '{agent_type}'. Task: {task}")
            agent = self.agents.get(agent_type)
            logger.info(f"Routing task: {task}. Final agent type: {agent_type}")
            if agent:
                logger.info(f"Agent '{agent_type}' found. Handling task.")
                try:
                    return await agent.handle(task)
                except Exception as e:
                    logger.error(f"Agent '{agent_type}' failed to handle task: {e}")
                    return {
                        "error": f"Sorry, the agent '{agent_type}' encountered an issue. Please try again later.",
                        "details": str(e)
                    }
            else:
                logger.error(f"No agent found for type: {agent_type}. Task: {task}")
                return {
                    "error": f"Sorry, I couldn't find an agent for your request (type: '{agent_type}'). Available agents: {list(self.agents.keys())}"
                }
        except Exception as e:
            logger.error(f"Failed to route task: {e}")
            return {"error": "Sorry, something went wrong while routing your request. Please try again later.", "details": str(e)}

    async def _get_agent_type_from_gemini(self, task: dict) -> str:
        """
        Uses Gemini LLM to determine the best agent type for a given task.
        """
        if not self.gemini_model:
            logger.info("Gemini model not available for agent type determination.")
            return task.get("type")
        available_agents = list(self.agents.keys())
        # Build prompt for Gemini
        prompt = (
            "Given the following task, determine the best agent type to handle it.\n"
            "Possible agent types and their descriptions:\n" +
            "\n".join([f"- {name}: {desc}" for name, desc in self.agent_descriptions.items()]) +
            "\nTask: " + str(task) +
            "\nRespond with only the agent type."
        )
        logger.debug(f"Prompting Gemini for agent type. Prompt: {prompt}")
        try:
            response = await self.gemini_model.generate_content_async(prompt)
            response_text = getattr(response, 'text', '').strip()
            logger.debug(f"Gemini response for agent type: {response_text}")
            determined_type = response_text.split()[0] if response_text else None
            if determined_type and determined_type in available_agents:
                return determined_type
            else:
                logger.warning(f"Gemini returned an invalid or unknown agent type: '{determined_type}'. Full response: '{response_text}'")
                return task.get("type")
        except Exception as e:
            logger.error(f"Error calling Gemini for agent type determination: {e}")
            return task.get("type")

    async def classify_task(self, text: str, user: str = None, channel: str = None) -> dict:
        """
        Uses Gemini LLM to classify the user's message into a task dictionary if available, otherwise falls back to a simple rule-based classifier.
        """
        logger.info(f"Classifying task for text: '{text}', user: '{user}', channel: '{channel}'")
        if self.gemini_model:
            try:
                available_agents = list(self.agents.keys())
                # Build prompt for Gemini
                prompt = (
                    "Classify the following user message into a task dictionary with keys: "
                    "'type', 'payload'. The 'type' should be one of: " + ", ".join(available_agents) + ". "
                    "The 'payload' should contain relevant information, typically a 'query' key with the original text or key entities. "
                    f"Message: \"{text}\"\n"
                    "Respond with only a valid Python dictionary string. Example: {'type': 'web_search', 'payload': {'query': 'search term'}}"
                )
                logger.debug(f"Prompting Gemini for task classification. Prompt: {prompt}")
                response = await self.gemini_model.generate_content_async(prompt)
                response_text = getattr(response, 'text', '').strip()
                logger.debug(f"Gemini response for task classification: {response_text}")
                task_dict_str = response_text
                # Remove code block formatting if present
                if task_dict_str.startswith("```python"):
                    task_dict_str = task_dict_str.split("```python")[1].split("```")[0].strip()
                elif task_dict_str.startswith("```json"):
                    task_dict_str = task_dict_str.split("```json")[1].split("```")[0].strip()
                elif task_dict_str.startswith("```"):
                    task_dict_str = task_dict_str.split("```")[1].strip()
                parsed_task = ast.literal_eval(task_dict_str)
                if isinstance(parsed_task, dict) and "type" in parsed_task and "payload" in parsed_task:
                    task_dict = parsed_task
                    logger.info(f"Successfully classified task via Gemini: {task_dict}")
                    task_dict.update({"user": user, "context": {"channel": channel}})
                    return task_dict
            except Exception as e:
                logger.warning(f"Gemini task classification failed: {e}. Falling back to rule-based classification. Response text: '{response_text if 'response_text' in locals() else 'N/A'}'")
        # Fallback: improved rule-based classification
        lowered = (text or "").lower()
        if "search" in lowered:
            task_type = "web_search"
        elif "data" in lowered or "fetch" in lowered:
            task_type = "data_retrieval"
        elif "report" in lowered:
            task_type = "report_generation"
        elif "dashboard" in lowered or "analy" in lowered:
            task_type = "analysis_dashboard"
        else:
            task_type = self.default_agent_type
        task_dict = {
            "type": task_type,
            "payload": {"query": text},
            "user": user,
            "context": {"channel": channel}
        }
        logger.info(f"Defaulting to rule-based task_dict: {task_dict}")
        return task_dict

    async def handle_task(self, task: dict) -> dict:
        """
        Handles complex, multi-step tasks by decomposing them and chaining agent calls as needed.
        Returns the final or aggregated result.
        Adds detailed logging and monitoring for task flows.
        Optimized for concurrency and robust error handling.
        """
        logger.info(f"[TASK_FLOW] Starting handle_task for: {task}")
        # Decompose task if possible
        if hasattr(self, "decompose_task") and self.gemini_model:
            sub_tasks = await self.decompose_task(task)
            logger.info(f"[TASK_FLOW] Decomposed task into {len(sub_tasks)} sub-tasks: {sub_tasks}")
        else:
            sub_tasks = [task]
            logger.info(f"[TASK_FLOW] No decomposition. Single task: {task}")
        results = []
        prev_result = None
        # If all sub-tasks are independent (no chaining), run concurrently
        can_run_concurrent = all(idx == 0 or not sub_tasks[idx]["payload"].get("input") for idx in range(len(sub_tasks)))
        if can_run_concurrent and len(sub_tasks) > 1:
            logger.info(f"[TASK_FLOW] Executing {len(sub_tasks)} sub-tasks concurrently.")
            import asyncio
            async def run_agent(sub_task, idx):
                agent_type = sub_task.get("type")
                agent = self.agents.get(agent_type)
                logger.info(f"[TASK_FLOW] [CONCURRENT] Sub-task {idx+1}: {sub_task}")
                if not agent:
                    logger.error(f"[TASK_FLOW] [CONCURRENT] No agent found for sub-task type: {agent_type}. Sub-task: {sub_task}")
                    return {"error": f"No agent for type: {agent_type}"}
                try:
                    result = await agent.handle(sub_task)
                    logger.info(f"[TASK_FLOW] [CONCURRENT] Agent '{agent_type}' completed sub-task {idx+1} with result: {result}")
                    return result
                except Exception as e:
                    logger.error(f"[TASK_FLOW] [CONCURRENT] Agent '{agent_type}' failed for sub-task {idx+1}: {e}", exc_info=True)
                    return {"error": f"Agent '{agent_type}' failed: {str(e)}", "sub_task": sub_task}
            results = await asyncio.gather(*[run_agent(st, idx) for idx, st in enumerate(sub_tasks)])
            prev_result = results[-1] if results else None
        else:
            # Run sub-tasks sequentially, passing previous result as input if needed
            for idx, sub_task in enumerate(sub_tasks):
                agent_type = sub_task.get("type")
                agent = self.agents.get(agent_type)
                logger.info(f"[TASK_FLOW] Sub-task {idx+1}/{len(sub_tasks)}: {sub_task}")
                if not agent:
                    logger.error(f"[TASK_FLOW] No agent found for sub-task type: {agent_type}. Sub-task: {sub_task}")
                    results.append({"error": f"No agent for type: {agent_type}"})
                    continue
                if idx > 0 and prev_result is not None:
                    sub_task = sub_task.copy()
                    sub_task.setdefault("payload", {})
                    sub_task["payload"]["input"] = prev_result
                    logger.info(f"[TASK_FLOW] Passing previous result to sub-task {idx+1}: {prev_result}")
                try:
                    logger.info(f"[TASK_FLOW] Delegating sub-task {idx+1} to agent '{agent_type}'")
                    result = await agent.handle(sub_task)
                    logger.info(f"[TASK_FLOW] Agent '{agent_type}' completed sub-task {idx+1} with result: {result}")
                    results.append(result)
                    prev_result = result
                except Exception as e:
                    logger.error(f"[TASK_FLOW] Agent '{agent_type}' failed for sub-task {idx+1}: {e}", exc_info=True)
                    results.append({"error": f"Agent '{agent_type}' failed: {str(e)}", "sub_task": sub_task})
                    prev_result = None
        # Return results based on success or error
        if not results:
            logger.error("[TASK_FLOW] No results generated from sub-tasks.")
            return {"error": "No results generated from task execution."}
        if len(results) == 1 and "error" not in results[0]:
            logger.info(f"[TASK_FLOW] Task flow completed successfully with single result: {results[0]}")
            return results[0]
        if all(isinstance(r, dict) and "error" not in r for r in results):
            logger.info(f"[TASK_FLOW] Task flow completed successfully with multiple results. Returning last result: {results[-1]}")
            return results[-1]
        logger.warning(f"[TASK_FLOW] Task flow completed with errors or multiple results: {results}")
        return {"final_status": "Completed with errors or multiple results", "results": results}

    async def decompose_task(self, task: dict) -> list:
        """
        Uses Gemini to decompose a complex task into a list of sub-tasks for chaining agents. If Gemini is unavailable, returns [task].
        """
        if not self.gemini_model:
            logger.info("Gemini model not available for task decomposition. Returning original task.")
            return [task]
        available_agents = list(self.agents.keys())
        # Build prompt for Gemini
        prompt = (
            "Given the following task dictionary, decompose it into a list of sub-task dictionaries "
            "for a multi-agent workflow. Each sub-task should be a valid Python dictionary. "
            "Each sub-task dictionary must have a 'type' key, chosen from: " + ", ".join(available_agents) + ". "
            "It must also have a 'payload' key. "
            "If the task does not require decomposition, return a list containing only the original task. "
            "Respond with only a valid Python list of dictionaries string. Example: [{'type': 'data_retrieval', 'payload': {'source': 'db'}}, {'type': 'analysis', 'payload': {'data_key': 'input'}}]\n"
            f"Original Task: {task}"
        )
        logger.debug(f"Prompting Gemini for task decomposition. Prompt: {prompt}")
        try:
            response = await self.gemini_model.generate_content_async(prompt)
            response_text = getattr(response, 'text', '').strip()
            logger.debug(f"Gemini response for decomposition: {response_text}")
            # Remove code block formatting if present
            if response_text.startswith("```python"):
                response_text = response_text.split("```python")[1].split("```")[0].strip()
            elif response_text.startswith("```json"):
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif response_text.startswith("```"):
                response_text = response_text.split("```")[1].strip()
            sub_tasks = ast.literal_eval(response_text)
            if isinstance(sub_tasks, list) and all(isinstance(st, dict) for st in sub_tasks):
                return sub_tasks
            else:
                logger.warning(f"Gemini did not return a valid list of dictionaries for decomposition. Response: '{response_text}'. Falling back to [task].")
                return [task]
        except Exception as e:
            logger.error(f"Failed to decompose task with Gemini: {e}. Response text: '{response_text if 'response_text' in locals() else 'N/A'}'")
            return [task]
