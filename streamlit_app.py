import streamlit as st
from agent.graph import agent
from agent.graph import planner_agent, architect_agent, coder_agent, validater_display_agent
import os
from utils.constants import PROJECT_NAME

st.set_page_config(page_title="Idea to App", layout="wide")
st.title("Idea to App")

# App description and instructions
st.markdown("""
<div style='background-color:#f5f5f5;padding:18px;border-radius:10px;margin-bottom:18px;color:#222;'>
<h3 style='color:#1a237e;'>Transform your ideas into working apps with AI!</h3>
<span style='font-size:18px;'><b>Idea to App</b> uses multi-agent AI to plan, design, and build your project from a simple prompt. Select your tech stack, enter your idea, and let the agents do the rest.</span><br>
<ul style='font-size:16px;'>
<li><b>Step 1:</b> Enter a project prompt (e.g., "Build a to-do list app in HTML, CSS, and JS")</li>
<li><b>Step 2:</b> Select your tech stack</li>
<li><b>Step 3:</b> Click <i>Run Full Agent Graph</i> and watch your app come to life!</li>
</ul>
</div>
""", unsafe_allow_html=True)

# Sidebar: settings and help
st.sidebar.header("Settings")
api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")

    
st.sidebar.markdown("---")
st.sidebar.header("Help & Examples")
st.sidebar.markdown("""
**Example Prompts:**
- Build a to-do list app in HTML, CSS, and JS
- Create a calculator in Python
- Make a blog API in FastAPI with SQLite
<br>
**Output Folder:**
All generated files are saved in <code>{PROJECT_NAME}</code>.
""")

col1, col2 = st.columns(2)
recursion_limit = 100
with col1:
    st.markdown("<div class='box-border'>", unsafe_allow_html=True)
    st.subheader("Run Full Agent Graph")
    user_prompt = st.text_area("Enter your project prompt:", "Build app in python adding any numbers", key="full_agent_prompt")
        
    # ...existing code...
    st.markdown("#### Please answer the following to customize your app:")
    language = st.selectbox("Which programming language?", ["None", "Python", "Java", "HTML/CSS", "JavaScript", "Other"], index=0)
    backend = st.selectbox("Which backend framework?", ["None", "FastAPI", "Flask", "Node.js", "Other"], index=0)
    server = st.selectbox("Which server?", ["None","Localhost", "AWS EC2", "Azure App Service", "GCP"], index=0)
    database = st.selectbox("Which database?", ["None", "SQLite", "MySQL", "MongoDB", "PostgreSQL"], index=0)
    # ...existing code...
    # First click opens an editor dialog so user can review/modify the full agent prompt
    if st.button("Run Full Agent Graph", key="run_full_agent_graph"):
       st.session_state["show_prompt_editor"] = True

    # Show a "dialog" (form) to review/edit the generated agent prompt
    if st.session_state.get("show_prompt_editor"):
        st.markdown("### Review & edit agent prompt before running")
        # construct current default prompt from selected fields
        default_agent_prompt = (
            f"Project Idea --> {user_prompt}\n"
            f"Programming Language --> {language}\n"
            f"Backend Framework --> {backend}\n"
            f"Server --> {server}\n"
            f"Database --> {database}\n"
            "If any option is left as 'None', select the best technology or approach based on the project idea. Generate a step-by-step plan and code for this application using the above specifications."
        )

        with st.form("agent_prompt_form"):
            agent_prompt_editor = st.text_area("Agent Prompt (editable)", default_agent_prompt, height=300, key="agent_prompt_editor")
            col_a, col_b = st.columns([1, 1])
            with col_a:
                submit = st.form_submit_button("Approve & Run")
            with col_b:
                cancel = st.form_submit_button("Cancel")

        if cancel:
            st.session_state["show_prompt_editor"] = False

        if submit:
            with st.spinner("Running agent..."):
                try:
                    result = agent.invoke(
                        {
                            "user_prompt": agent_prompt_editor,
                            "recursion_limit": recursion_limit
                        }
                    )
                    st.success("Agent completed!")
                    # remove git_logs from top-level dict before showing
                    try:
                        cleaned = dict(result) if isinstance(result, dict) else result
                        if isinstance(cleaned, dict) and "git_logs" in cleaned:
                            del cleaned["git_logs"]
                        st.json(cleaned)
                    except Exception:
                        st.json(result)
                    st.session_state["agent_result"] = True
                    st.session_state["show_prompt_editor"] = False
                except Exception as e:
                    st.error(f"Agent run failed: {e}")
    st.markdown("</div>", unsafe_allow_html=True)


with col2:
    st.markdown("<div class='box-border'>", unsafe_allow_html=True)
    st.subheader("Generated Files (Chat Stream)")
    project_folder = os.path.join(os.getcwd(), PROJECT_NAME)
    if st.session_state.get("agent_result") and os.path.exists(project_folder):
       for root, dirs, files in os.walk(project_folder):
            # don't descend into .git (or other hidden dir we don't want to show)
            if ".git" in dirs:
                dirs.remove(".git")

            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_folder)

                # Skip typical binary files by simple extension filter or small heuristic
                binary_exts = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".exe", ".dll", ".so", ".pyc"}
                _, ext = os.path.splitext(file)
                if ext.lower() in binary_exts:
                    st.write(f"{rel_path} (binary, skipped preview)")
                    continue

                # Try to read a small text preview safely
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        preview = f.read(2000)  # limit size
                    st.markdown(f"**{rel_path}**")
                    st.code(preview, language="text")
                except Exception as e:
                    st.markdown(f"**{rel_path}**")
                    st.write(f"Could not preview file: {e}")
# ...existing code...
    st.markdown("</div>", unsafe_allow_html=True)

