# Joe 1.0: Multi-Agent Slack Assistant

Joe 1.0 is a modular, scalable, and intelligent multi-agent system integrated with Slack. Powered by the Gemini LLM, it automates web search, data retrieval, report generation, and data analysis tasks for organizational users—all accessible via conversational Slack interactions.

---

## Features

- **Slack Integration:** Interact with Joe 1.0 via direct messages, mentions, and slash commands.
- **Multi-Agent Architecture:** Specialized agents for web search, data retrieval, report generation, and analysis/dashboarding.
- **LLM-Powered Intelligence:** Uses Gemini LLM for natural language understanding, summarization, and content generation.
- **Visual Feedback:** Slack reactions and interactive elements provide real-time task status and options.
- **Extensible & Modular:** Easily add new agents or capabilities as requirements evolve.

---

## Architecture Overview

```
Joe 1.0/
├── agents/                # Specialized agent implementations
├── orchestrator/          # Task routing and orchestration logic
├── slack_interface/       # Slack event handling and integration
├── llm_integration/       # Gemini API wrapper and prompt engineering
├── data/                  # Data connectors and storage
├── config/                # Configuration management
├── tests/                 # Unit and integration tests
├── docs/                  # Documentation and guides
├── requirements.txt
├── main.py                # Application entry point
└── README.md
```

- **Slack Interface Agent:** Handles Slack events, messages, reactions, and interactive components.
- **Orchestrator Agent:** Receives user requests, decomposes tasks, delegates to specialized agents, aggregates results.
- **Specialized Agents:** Web Search, Data Retrieval, Report Generation, Analysis/Dashboard
- **LLM Integration Layer:** Connects to Gemini API for NLU, summarization, and content generation.

For a detailed architecture and implementation plan, see [`docs/master_plan.md`](docs/master_plan.md).

---

## Quick Start

1. **Clone the Repository**
   ```sh
   git clone <repo-url>
   cd Joe\ 1.0
   ```

2. **Set Up Python Environment**
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   - Create a `.env` file and fill in required values (Slack tokens, Gemini API key, database credentials, etc.).

4. **Register Slack App**
   - Create a new Slack app, configure permissions, and set up event subscriptions as described in the [Slack App Setup Guide](docs/slack_app_setup_guide.md).

5. **Run the Application**
   ```sh
   python main.py
   ```

---

## Contributing

Contributions are welcome! Please see `CONTRIBUTING.md` (to be created) for guidelines on submitting issues and pull requests.

---

## Documentation

- [Requirements](docs/requirements.md)
- [Master Plan](docs/master_plan.md)
- [Tasks & Subtasks](docs/tasks_&_subtasks.md)
- [Slack App Setup Guide](docs/slack_app_setup_guide.md)
- [User & Admin Guides](docs/)

---

## License

This project is licensed under the MIT License.

---

## Contact

For questions or support, please open an issue or contact the maintainers via the repository. 