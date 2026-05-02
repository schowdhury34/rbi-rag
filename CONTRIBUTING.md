# Contributing

## Setup
```bash
git clone https://github.com/schowdhury34/rbi-rag.git
cd rbi-rag
pip install -r requirements.txt
cp .env.example .env
# Add your GROQ_API_KEY to .env
```

## Project Structure
```
crawl/          Crawler — scrapes RBI site, downloads PDFs
ingest/         PDF parser, chunker, ChromaDB embedder
retrieval/      Hybrid search, RAG chain
agent/          LangGraph ReAct agent and tools
eval/           RAGAS evaluation pipeline and dataset
benchmarks/     Saved eval results (tracked in git)
utils/          Logging and shared utilities
app/            Streamlit UI
```

## Running the pipeline
```python
from crawl.rbi_crawler import RBICrawler
from ingest.pdf_parser import PDFParser
from ingest.embedder import Embedder

RBICrawler().run()                        # crawl + download
docs = PDFParser().parse_all()            # parse + chunk
Embedder().embed_and_store(docs)          # embed + store
```

## Running evaluation
```bash
python eval/ragas_eval.py --mode rag   --split dev --save
python eval/ragas_eval.py --mode agent --split dev --save
python eval/benchmark.py  --compare
```

## Notes
- PDFs and ChromaDB are gitignored — they live in data/ locally
- Benchmark CSVs in benchmarks/ ARE tracked in git
- Always run on dev split during development, test split for final numbers only
