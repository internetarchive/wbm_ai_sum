import os
import subprocess

# Define the path to the chat.py script
chat_script_path = os.path.join("pages", "chat.py")

# Run the Streamlit app
subprocess.run(["streamlit", "run", chat_script_path])
