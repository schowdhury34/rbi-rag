# run.py — convenience script to run the Streamlit app locally
# Usage: python run.py
import subprocess, sys

subprocess.run([sys.executable, "-m", "streamlit", "run", "app/streamlit_app.py"])
