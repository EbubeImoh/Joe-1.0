# Orchestrator Agent Setup Guide

This guide details the steps to implement the Orchestrator Agent for Zia-AI, responsible for routing tasks, decomposing complex requests, delegating to specialized agents, and integrating with the Slack Interface Agent.

---

## 1. Implement Orchestrator Skeleton for Task Routing

**Purpose:**  
The Orchestrator Agent acts as the central coordinator. It receives user requests (from Slack), determines which specialized agent(s) should handle each part, and manages the flow of information and results.

**Steps:**

1. **Create the Orchestrator Module:**
    - File: `orchestrator/orchestrator.py`
    - Define an `Orchestrator` class with a main entrypoint method (e.g., `route_task`).

    ```python
    # filepath: orchestrator/orchestrator.py
    class Orchestrator:
        def __init__(self, agents: dict):
            self.agents = agents  # Dictionary mapping agent names to agent instances

        async def route_task(self, task: dict) -> dict:
            """
            Receives a task, determines the appropriate agent(s), and delegates the task.
            """
            # Example: route based on task['type']
            agent_type = task.get("type")
            agent = self.agents.get(agent_type)
            if agent:
                return await agent.handle(task)
            else:
                return {"error": f"No agent found for type: {agent_type}"}
    ```

2. **Register Specialized Agents:**
    - Import and instantiate your agents (e.g., WebSearchAgent, DataRetrievalAgent).
    - Pass them to the Orchestrator.

    ```python
    # Example (in main.py or a setup module)
    from agents.web_search_agent import WebSearchAgent
    from agents.data_retrieval_agent import DataRetrievalAgent
    from orchestrator.orchestrator import Orchestrator

    agents = {
        "web_search": WebSearchAgent(),
        "data_retrieval": DataRetrievalAgent(),
        # Add more agents as needed
    }
    orchestrator = Orchestrator(agents)
    ```

---

## 2. Define Protocol for Task Decomposition and Delegation

**Purpose:**  
Enable the Orchestrator to break down complex user requests into sub-tasks and delegate them to the appropriate agents.

**Steps:**

1. **Define a Task Schema:**
    - Standardize the structure of tasks and sub-tasks (e.g., type, payload, user, context).

    ```python
    # Example task structure
    task = {
        "type": "web_search",
        "payload": {"query": "latest AI news"},
        "user": "U123456",
        "context": {}
    }
    ```

2. **Implement Task Decomposition Logic:**
    - For complex requests, split the main task into sub-tasks.
    - Example: A user asks for a report that requires both data retrieval and analysis.

    ```python
    class Orchestrator:
        ...
        async def route_task(self, task: dict) -> dict:
            if task["type"] == "report_generation":
                # Decompose into data retrieval and analysis
                data_task = {"type": "data_retrieval", "payload": task["payload"], "user": task["user"]}
                data_result = await self.agents["data_retrieval"].handle(data_task)
                analysis_task = {"type": "analysis", "payload": data_result, "user": task["user"]}
                analysis_result = await self.agents["analysis"].handle(analysis_task)
                # Compose final report
                return {"report": analysis_result}
            else:
                # Simple routing
                agent = self.agents.get(task["type"])
                if agent:
                    return await agent.handle(task)
                else:
                    return {"error": f"No agent found for type: {task['type']}"}
    ```

3. **Define Delegation Protocol:**
    - Each agent should implement a standard `handle(task: dict) -> dict` method (async if needed).
    - The Orchestrator calls this method to delegate sub-tasks.

---

## 3. Integrate with Slack Interface Agent

**Purpose:**  
Connect the Orchestrator to the Slack Interface Agent so that user requests from Slack are routed through the Orchestrator and responses are sent back to Slack.

**Steps:**

1. **Modify Slack Event Handler to Use Orchestrator:**
    - In `slack_interface/slack_events.py`, import the Orchestrator instance.
    - When a message event is received, parse the user request and create a task for the Orchestrator.

    ```python
    # filepath: slack_interface/slack_events.py
    from orchestrator.orchestrator import orchestrator  # Import the orchestrator instance

    async def handle_message_event(event):
        user = event.get("user")
        text = event.get("text", "")
        channel = event.get("channel")
        # Parse user intent (could use LLM or simple rules)
        task_type = "web_search" if "search" in text else "data_retrieval"  # Example logic
        task = {
            "type": task_type,
            "payload": {"query": text},
            "user": user,
            "context": {"channel": channel}
        }
        result = await orchestrator.route_task(task)
        # Send result back to Slack
        response_text = result.get("report") or str(result)
        slack_client.chat_postMessage(channel=channel, text=response_text)
    ```

2. **(Optional) Use LLM for Task Parsing:**
    - For advanced intent detection, use the Gemini LLM to parse user messages and determine task type and parameters.

3. **Handle Responses and Errors:**
    - Ensure the Orchestrator returns user-friendly error messages if a task cannot be routed or fails.

---

## 4. Testing and Validation

- **Unit Test the Orchestrator:**  
  Write tests for task routing, decomposition, and delegation logic.
- **Integration Test with Slack:**  
  Send sample messages via Slack and verify that the Orchestrator routes tasks correctly and responses are delivered.

---

## 5. Next Steps

- Expand the Orchestrator to support more complex workflows and additional agent types.
- Add logging and monitoring for task flows.
- Optimize for concurrency and error handling as needed.

---

**End of Orchestrator Agent Setup Guide**