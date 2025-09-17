import pathlib
import subprocess
import os
import logging
from typing import Tuple
from langchain_core.tools import tool
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
from utils.constants import PROJECT_NAME

# Make PROJECT_PATH configurable via environment variable
PROJECT_PATH = pathlib.Path(os.getenv("PROJECT_NAME", pathlib.Path.cwd() / PROJECT_NAME)).resolve()
logging.info(f"Project path set to: {PROJECT_PATH}")

if not PROJECT_PATH.exists():
    PROJECT_PATH.mkdir(parents=True, exist_ok=True)
else:
    #delete and recreate the directory to ensure it's empty
    import shutil
    shutil.rmtree(PROJECT_PATH)
    PROJECT_PATH.mkdir(parents=True, exist_ok=True)    

def safe_path_for_project(path: str) -> pathlib.Path:
    """Resolve and validate a path within the project root."""
    p = (PROJECT_PATH / path).resolve()
    if PROJECT_PATH.resolve() not in p.parents and PROJECT_PATH.resolve() != p.parent and PROJECT_PATH.resolve() != p:
        logging.error(f"Attempt to write outside project root: {p}")
        raise ValueError("Attempt to write outside project root")
    return p


@tool
def write_file(path: str, content: str) -> str:
    """
    Writes content to a file at the specified path within the project root.
    Returns a status message or error.
    """
    try:
        p = safe_path_for_project(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        logging.info(f"Wrote file: {p}")
        return f"WROTE:{p}"
    except Exception as e:
        logging.error(f"Error writing file {path}: {e}")
        return f"ERROR writing file {path}: {e}"


@tool
def read_file(path: str) -> str:
    """
    Reads content from a file at the specified path within the project root.
    Returns file content or error message.
    """
    try:
        p = safe_path_for_project(path)
        if not p.exists():
            logging.warning(f"File not found: {p}")
            return ""
        with open(p, "r", encoding="utf-8") as f:
            content = f.read()
        logging.info(f"Read file: {p}")
        return content
    except Exception as e:
        logging.error(f"Error reading file {path}: {e}")
        return f"ERROR reading file {path}: {e}"


@tool
def get_current_directory() -> str:
    """
    Returns the current working directory (project root).
    """
    logging.info(f"Current directory: {PROJECT_PATH}")
    return str(PROJECT_PATH)


@tool
def list_files(directory: str = ".") -> str:
    """
    Lists all files in the specified directory within the project root.
    Returns a newline-separated list or error message.
    """
    try:
        p = safe_path_for_project(directory)
        if not p.is_dir():
            logging.warning(f"Not a directory: {p}")
            return f"ERROR: {p} is not a directory"
        files = [str(f.relative_to(PROJECT_PATH)) for f in p.glob("**/*") if f.is_file()]
        logging.info(f"Listed files in: {p}")
        return "\n".join(files) if files else "No files found."
    except Exception as e:
        logging.error(f"Error listing files in {directory}: {e}")
        return f"ERROR listing files in {directory}: {e}"

@tool
def run_cmd(cmd: str, cwd: str = None, timeout: int = 30) -> Tuple[int, str, str]:
    """
    Runs a shell command in the specified directory and returns (returncode, stdout, stderr).
    """
    try:
        cwd_dir = safe_path_for_project(cwd) if cwd else PROJECT_PATH
        res = subprocess.run(cmd, shell=True, cwd=str(cwd_dir), capture_output=True, text=True, timeout=timeout)
        logging.info(f"Ran command: {cmd} in {cwd_dir}")
        return res.returncode, res.stdout, res.stderr
    except Exception as e:
        logging.error(f"Error running command '{cmd}': {e}")
        return -1, "", f"ERROR running command '{cmd}': {e}"


@tool
def read_file_after_completion(path: str) -> str:
    """
    Reads content from a file at the specified path within the project root.
    Waits until the file is fully written (no changes for 1 second).
    Returns file content or error message.
    """
    import time
    try:
        p = safe_path_for_project(path)
        if not p.exists():
            logging.warning(f"File not found: {p}")
            return ""
        
        last_size = -1
        stable_count = 0
        while stable_count < 3:  # Check for stability over 3 intervals
            current_size = p.stat().st_size
            if current_size == last_size:
                stable_count += 1
            else:
                stable_count = 0
                last_size = current_size
            time.sleep(1)  # Wait before checking again

        with open(p, "r", encoding="utf-8") as f:
            content = f.read()
        logging.info(f"Read file after completion: {p}")
        return content
    except Exception as e:
        logging.error(f"Error reading file {path}: {e}")
        return f"ERROR reading file {path}: {e}"
   

def init_project_root():
    """
    Initializes the project root directory.
    """
    PROJECT_PATH.mkdir(parents=True, exist_ok=True)
    logging.info(f"Initialized project root: {PROJECT_PATH}")
    return str(PROJECT_PATH)
