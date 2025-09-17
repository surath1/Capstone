# ...existing code...
from utils.constants import MODEL, logging
from dotenv import load_dotenv
from langchain.globals import set_verbose, set_debug
from langchain_openai import ChatOpenAI
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent
from prompt.prompts import planner_prompt, architect_prompt, coder_system_prompt
from state.states import Plan, TaskPlan, CoderState
from tool.tools import write_file, read_file, get_current_directory, list_files, read_file_after_completion, run_cmd
import os
import json
import shutil
import stat
import time
from utils.constants import PROJECT_NAME

load_dotenv()

set_debug(True)
#set_verbose(True)


def _on_rm_error(func, path, exc_info):
    """
    Error handler for shutil.rmtree: make writable and retry once.
    """
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass
    try:
        func(path)
    except Exception:
        # small backoff and final retry
        time.sleep(0.2)
        os.chmod(path, stat.S_IWRITE)
        func(path)

def safe_rmtree(path: str, max_retries: int = 5, delay: float = 0.5):
    """
    Robust rmtree for Windows. Retries on PermissionError and uses onerror handler.
    """
    if not os.path.exists(path):
        return
    last_exc = None
    for attempt in range(max_retries):
        try:
            shutil.rmtree(path, onerror=_on_rm_error)
            return
        except PermissionError as e:
            last_exc = e
            time.sleep(delay)
        except OSError as e:
            last_exc = e
            time.sleep(delay)
    # If we reach here, raise the last exception to be visible
    if last_exc:
        raise last_exc


# ...existing code...
def _git_is_healthy(new_folder: str) -> bool:
    """
    Return True if the git repo at new_folder appears usable (not corrupt and accepts basic git commands).
    This function checks basic git commands and runs a fsck to detect corruption. It does not treat
    an empty repository (no commits yet) as unhealthy.
    """
    try:
        # Ensure it's a git work tree
        rc, out, err = run_cmd.run(f'git -C "{new_folder}" rev-parse --is-inside-work-tree')
        logging.debug({"check": "rev-parse --is-inside-work-tree", "rc": rc, "out": out, "err": err})
        if rc != 0:
            return False

        # Basic status should succeed (working tree with changes is still healthy)
        rc, out, err = run_cmd.run(f'git -C "{new_folder}" status --porcelain -b')
        logging.debug({"check": "status --porcelain -b", "rc": rc, "out": out, "err": err})
        if rc != 0:
            return False

        # Run fsck to detect repository corruption. If fsck reports problems, treat repo as unhealthy.
        rc, out, err = run_cmd.run(f'git -C "{new_folder}" fsck --no-reflogs --full')
        logging.debug({"check": "fsck --no-reflogs --full", "rc": rc, "out": out, "err": err})

        if rc != 0:
            # fsck may fail on an otherwise fine but empty repo (no HEAD). Treat that as healthy.
            combined = (out or "") + (err or "")
            if "bad object HEAD" in combined or "fatal: bad object HEAD" in combined or "unable to find" in combined:
                return True
            return False

        return True
    except Exception as e:
        logging.debug(f"_git_is_healthy exception: {e}")
        return False
# ...existing code...

llm = ChatOpenAI(
    model="gpt-4o",max_retries=3, request_timeout=120
)

# Planner Agent
def planner_agent(state: dict) -> dict:
    """Converts user prompt into a structured Plan."""
    user_prompt = state["user_prompt"]
    resp = llm.with_structured_output(Plan).invoke(
        planner_prompt(user_prompt)
    )
    if resp is None:
        raise ValueError("Planner did not return a valid response.")
    return {"plan": resp}

# Architect Agent
def architect_agent(state: dict) -> dict:
    """Creates TaskPlan from Plan."""
    plan: Plan = state["plan"]
    resp = llm.with_structured_output(TaskPlan).invoke(
        architect_prompt(plan=plan.model_dump_json())
    )
    if resp is None:
        raise ValueError("Planner did not return a valid response.")

    resp.plan = plan
    print(resp.model_dump_json())
    return {"task_plan": resp}

# Coder Agent
def coder_agent(state: dict) -> dict:
    """LangGraph tool-using coder agent."""
    coder_state: CoderState = state.get("coder_state")
    if coder_state is None:
        coder_state = CoderState(task_plan=state["task_plan"], current_step_idx=0)

    steps = coder_state.task_plan.implementation_steps
    if coder_state.current_step_idx >= len(steps):
        return {"coder_state": coder_state, "status": "DONE"}

    current_task = steps[coder_state.current_step_idx]
    existing_content = read_file.run(current_task.filepath)

    system_prompt = coder_system_prompt()
    user_prompt = (
        f"Task: {current_task.task_description}\n"
        f"File: {current_task.filepath}\n"
        f"Existing content:\n{existing_content}\n"
        "Use write_file(path, content) to save your changes."
    )

    coder_tools = [read_file, write_file, list_files, get_current_directory]
    react_agent = create_react_agent(llm, coder_tools)

    react_agent.invoke({"messages": [{"role": "system", "content": system_prompt},
                                     {"role": "user", "content": user_prompt}]})

    coder_state.current_step_idx += 1
    return {"coder_state": coder_state}


# Validator and Display Agent
def validater_display_agent(state: dict) -> dict:
    project_root = os.getcwd()
    techstack = None
    # Try to get techstack from state
    if "plan" in state and hasattr(state["plan"], "techstack"):
        techstack = state["plan"].techstack.lower()
    # Determine main file based on techstack
    if techstack == "python":
        main_file = os.path.join(project_root, PROJECT_NAME, "main.py")
        main_label = "main.py"
    elif techstack == "html":
        main_file = os.path.join(project_root, PROJECT_NAME, "index.html")
        main_label = "index.html"
    elif techstack == "java":
        main_file = os.path.join(project_root, PROJECT_NAME, "Main.java")
        main_label = "Main.java"
    elif techstack == "streamlit":
        main_file = os.path.join(project_root, PROJECT_NAME, "streamlit_app.py")
        main_label = "streamlit_app.py"
    else:
        main_file = None
        main_label = None
    result = {}
    # NOTE: validator_success removed — validator returns validation messages only
    if main_file and os.path.exists(main_file):
        try:
            content = read_file_after_completion.run(main_file)
            # Check for non-empty and basic implementation
            if not content or not content.strip():
                result["validation"] = f"{main_label} exists but is empty."
            elif content.strip() in ["pass", "", "// TODO", "# TODO"]:
                result["validation"] = f"{main_label} exists but only contains a placeholder (e.g., 'pass', '// TODO', '# TODO')."
            else:
                # Optionally, check for main function/class for each techstack
                basic_ok = False
                if techstack == "python" and ("def main" in content or "if __name__" in content):
                    basic_ok = True
                elif techstack == "java" and "public static void main" in content:
                    basic_ok = True
                elif techstack == "html" and "<html" in content.lower():
                    basic_ok = True
                elif techstack == "streamlit" and "streamlit" in content.lower():
                    basic_ok = True
                if basic_ok:
                    result["validation"] = f"{main_label} found and contains basic implementation."
                else:
                    result["validation"] = f"{main_label} found but may not contain a valid entry point or implementation."
            result["main_file_content"] = content
        except Exception as e:
            result["validation"] = f"Error reading {main_label}: {e}"
    # If main_file does not exist, do not set a validation message about missing file
    return result
    

def git_agent(state: dict) -> dict:
    """
    Commits and attempts to push the project. Do NOT delete .git by default; if you want
    to force removal set env FORCE_CLEAN_GIT=1. Use safe_rmtree for robust deletion.
    """
    result = {"git_logs": []}
    new_folder = os.path.join(os.getcwd(), PROJECT_NAME)
    git_dir = os.path.join(new_folder, ".git")

    # If .git exists, prefer re-using it. Try a quick git status first.
    if os.path.exists(git_dir):
        try:
            if _git_is_healthy(new_folder):
                result["git_reused"] = True
            else:
                # Only attempt destructive cleanup if explicitly requested
                if os.getenv("FORCE_CLEAN_GIT") == "1":
                    try:
                        safe_rmtree(git_dir)
                        result["git_reused"] = False
                        result["git_cleaned"] = True
                    except Exception as e:
                        result["git_clean_error"] = str(e)
                        # don't abort; continue and try to proceed (may still fail)
                else:
                    result["git_reused"] = True
        except Exception as e:
            # Non-fatal — record and continue
            result["git_reuse_check_error"] = str(e)

    def run(cmd: str):
        rc, out, err = run_cmd.run(cmd)
        result["git_logs"].append({"cmd": cmd, "rc": rc, "stdout": out, "stderr": err})
        return rc, out, err

    try:
        # Init / reuse repo
        rc, _, _ = run(f"git -C \"{new_folder}\" rev-parse --is-inside-work-tree || git init -b main \"{new_folder}\" || true")
        # Configure user
        name = os.getenv("GIT_USER_NAME", "surath1")
        email = os.getenv("GIT_USER_EMAIL", "surath12321@gmail.com")
        run(f'git -C "{new_folder}" config user.name "{name}"')
        run(f'git -C "{new_folder}" config user.email "{email}"')
        # Add files and commit
        run(f'git -C "{new_folder}" add .')
        rc, out, err = run(f'git -C "{new_folder}" commit -m "Initial commit from Idea to App" || true')
        # Remote and push if available
        github_repo = os.getenv("GITHUB_REPO") or os.getenv("GIT_REMOTE")
        github_token = os.getenv("GITHUB_TOKEN")
        if github_repo:
            if github_token:
                remote_url = f"https://{github_token}@github.com/{github_repo}.git"
            else:
                remote_url = f"https://github.com/{github_repo}.git"
            run(f'git -C "{new_folder}" remote add origin {remote_url} || git -C "{new_folder}" remote set-url origin {remote_url}')
            rc, out, err = run(f'git -C "{new_folder}" push -u origin main --force || git -C "{new_folder}" push --all || true')
        result["status"] = "OK"
    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)
    return result


graph = StateGraph(dict)

graph.add_node("planner", planner_agent)
graph.add_node("architect", architect_agent)
graph.add_node("coder", coder_agent)
graph.add_node("validator", validater_display_agent)
graph.add_node("git", git_agent)


graph.add_edge("planner", "architect")
graph.add_edge("architect", "coder")
graph.add_conditional_edges(
    "coder",
    lambda s: "validator" if s.get("status") == "DONE" else "coder",
    {"validator": "validator", "coder": "coder"}
)

# validator_success gating removed — always proceed from validator to git
graph.add_edge("validator", "git")

graph.add_edge("git", END)

graph.set_entry_point("planner")
agent = graph.compile()

# If you need to modify the agent's behavior, you can do so here
if __name__ == "__main__":
    result = agent.invoke({"user_prompt": "Build a colourful modern todo app in html css and js"},
                          {"recursion_limit": 100})
    print("Final State:", result)

    # For debugging: print the entire state graph execution trace
    print("-----------LOGS--------")
    print(json.dumps(graph.execution_trace, indent=2))
    print("---------------------------")
# ...existing code...