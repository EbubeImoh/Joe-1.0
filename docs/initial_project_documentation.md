# Zia-AI: Multi-Agent System for Slack

## Overview

Zia-AI is a modular, scalable, and intelligent multi-agent system integrated with Slack. Powered by the Gemini LLM, it automates web search, data retrieval, report generation, and data analysis tasks for organizational users—all accessible via conversational Slack interactions.

---

## Features

- **Slack Integration:** Interact with Zia-AI via direct messages, mentions, and slash commands.
- **Multi-Agent Architecture:** Specialized agents for web search, data retrieval, report generation, and analysis/dashboarding.
- **LLM-Powered Intelligence:** Uses Gemini LLM for natural language understanding, summarization, and content generation.
- **Visual Feedback:** Slack reactions and interactive elements provide real-time task status and options.
- **Extensible & Modular:** Easily add new agents or capabilities as requirements evolve.

---

## Quick Start

1. **Clone the Repository**
   ```sh
   git clone <repo-url>
   cd Zia-AI
   ```

2. **Set Up Python Environment**
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   - Copy `.env.example` to `.env` and fill in required values (Slack tokens, Gemini API key, database credentials, etc.).

4. **Register Slack App**
   - Create a new Slack app, configure permissions, and set up event subscriptions as described in the [Slack App Setup Guide](docs/SLACK_SETUP.md).

5. **Run the Application**
   ```sh
   python main.py
   ```

---

## Repository Structure

```
Zia-AI/
├── agents/                # Specialized agent implementations
├── orchestrator/          # Task routing and orchestration logic
├── slack_interface/       # Slack event handling and integration
├── llm_integration/       # Gemini API wrapper and prompt engineering
├── data/                  # Data connectors and storage
├── tests/                 # Unit and integration tests
├── docs/                  # Documentation and guides
├── requirements.txt
├── .env.example
└── main.py
```

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on submitting issues and pull requests.

---

## Documentation

- [Requirements](requirements.md)
- [Master Plan](master_plan.md)
- [Tasks & Subtasks](tasks_&_subtasks.md)
- [Slack App Setup Guide](docs/SLACK_SETUP.md) *(to be created)*
- [User & Admin Guides](docs/) *(to be expanded)*

---

## License

This project is licensed under the MIT License.

---

## Contact

For questions or support, please open an issue or contact the maintainers via the repository.
