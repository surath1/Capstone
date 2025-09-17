
# � Idea to App

**Idea to App** is an AI-powered coding assistant that automates project planning and implementation using multi-agent workflows. Built with [LangGraph](https://github.com/langchain-ai/langgraph), it transforms your ideas into complete, working projects—file by file—using real developer workflows.

---

## 🚀 Features & Architecture

- **Planner Agent:** Converts user prompts into structured engineering project plans.
- **Architect Agent:** Breaks down plans into explicit engineering tasks, specifying file structure, integration, and implementation details.
- **Coder Agent:** Implements each engineering task, writing code directly to files using available tools.
- **Validator Agent:** Validates the main file for basic implementation and entry points.


Project output is saved in the `project` folder. The system supports Python, HTML, Java, and Streamlit tech stacks.

---


## 🏗️ Directory Structure

```
capstone_project/
├── main.py                # CLI entry point
├── streamlit_app.py       # Streamlit web UI (Idea to App)
├── agent/                 # Agent orchestration logic
├── prompt/                # Prompt templates for agents
├── state/                 # Data models for plans, tasks, and agent state
├── tool/                  # Utility tools for file operations and commands
├── utils/                 # Constants and logging configuration
├── project/           # Output folder for generated projects
├── requirements.txt       # Project dependencies
├── README.md              # Project documentation
```

---

## ⚙️ Installation & Setup

1. **Install [uv](https://docs.astral.sh/uv/getting-started/installation/)** for virtual environment and dependency management.
2. **Clone the repository** and navigate to the project folder.
3. **Create a virtual environment:**
   ```bash
   uv venv
   # Activate the environment
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```
4. **Install dependencies:**
   ```bash
   uv pip install -r requirements.txt
   ```
5. **Set up environment variables:**
   - Create a `.env` file and add your Groq/OpenAI API key and other required variables.

---

## 🖥️ Usage

### Command Line

Run the CLI and enter your project prompt:
```bash
python main.py
```


### Streamlit Web UI (Idea to App)

Launch the interactive app:
```bash
streamlit run streamlit_app.py
```

The app is branded as **Idea to App**. Generated files will appear in the newly create project folder.

---

## 💡 Example Prompts

- Create a to-do list application using html, css, and javascript.
- Create a simple calculator web application.
- Create a simple blog API in FastAPI with a SQLite database.

---

## 📦 Tech Stack & Dependencies

**Core Technologies:**
- **LangChain & LangGraph:** Multi-agent orchestration and prompt engineering.
- **OpenAI / Groq API:** LLM-powered code generation and planning.
- **Streamlit:** Interactive web UI for project creation.
- **Python:** Main backend language for agent logic and orchestration.

**Supported Output Tech Stacks:**
- **Python:** CLI apps, APIs, scripts.
- **HTML/CSS/JavaScript:** Static and interactive web apps.
- **Java:** Basic Java applications.
- **Streamlit:** Python-based web apps for rapid prototyping.

**Key Python Packages:**
- `langchain-core`
- `langchain-openai`
- `python-dotenv`
- `pydantic`
- `streamlit`

---

## 📝 License & Credits

Copyright ©️ Codebasics Inc. All rights reserved.