# notebooks/01_run_pipeline.py
# Full pipeline — run cell-by-cell in Google Colab

# CELL 1: Mount Drive
from google.colab import drive
drive.mount("/content/drive")
import sys; sys.path.append("/content/rbi-rag")

# CELL 2: Install
# !pip install -r requirements.txt -q

# CELL 3: API Key
import os
from google.colab import userdata
os.environ["GROQ_API_KEY"] = userdata.get("GROQ_API_KEY")

# CELL 4: Crawl
from crawl.rbi_crawler import RBICrawler
df = RBICrawler().run()

# CELL 5: Ingest
from ingest.pdf_parser import PDFParser
from ingest.embedder import Embedder
docs = PDFParser().parse_all()
Embedder().embed_and_store(docs)

# CELL 6: Test RAG chain
from retrieval.rag_chain import RAGChain
rag = RAGChain()
r   = rag.answer("What are the KYC guidelines?")
print(r["answer"])

# CELL 7: Test Agent
from agent.rbi_agent import run_agent
r = run_agent("What are the latest FEMA guidelines for NRIs?")
print(r["answer"])

# CELL 8: Run RAGAS eval (dev split)
from eval.ragas_eval import run_eval
run_eval(mode="rag", split="dev", save=True)

# CELL 9: Compare RAG vs Agent
run_eval(mode="rag",   split="dev", save=True)
run_eval(mode="agent", split="dev", save=True)

# CELL 10: Launch Streamlit
# import subprocess, threading, time
# from google.colab.output import eval_js
# t = threading.Thread(target=lambda: subprocess.run(
#     ["streamlit","run","app/streamlit_app.py","--server.port=8501","--server.headless=true"]
# ), daemon=True)
# t.start(); time.sleep(3)
# print(eval_js("google.colab.kernel.proxyPort(8501)"))
