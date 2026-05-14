# RBI RAG — Command Reference

Always activate the environment first:
```cmd
conda activate rbi_rag
cd D:\projects\rbi_rag
```

---

## 1. Run the app (RAG UI)
```cmd
python run.py
```
Open http://localhost:8501 in browser.

---

## 2. Download RBI Master Circulars (Playwright)
```cmd
python crawl\pdf_downloader.py --limit 21
```
Downloads to `data\pdfs\`. Bypasses bot protection using headless browser.
Run this whenever new Master Circulars are published (typically April each year).

---

## 3. Ingest PDFs into ChromaDB
```cmd
# After downloading new PDFs:
python scripts\run_ingestion.py --skip-crawl

# Full pipeline (crawl + ingest):
python scripts\run_ingestion.py --limit 50
```

---

## 4. Smoke test the pipeline
```cmd
python scripts\test_pipeline.py
```
Fires 5 test queries and shows answers with sources.

---

## 5. Run RAGAS evaluation
```cmd
# Dev split (7 questions) — use Ollama, no rate limits:
python eval\ragas_eval.py --mode rag --split dev --save

# Full eval (all 20 questions):
python eval\ragas_eval.py --mode rag --split all --save
```
Results saved to `benchmarks\`.

---

## 6. Check what's indexed in ChromaDB
```cmd
python -c "
import chromadb
client = chromadb.PersistentClient(path='data/chroma_db')
col = client.get_collection('rbi_circulars')
results = col.get(include=['metadatas'])
print(f'Total chunks: {len(results[\"ids\"])}')
for m in results['metadatas'][:5]:
    print(m.get('circular_no','?'), '|', str(m.get('subject','?'))[:60])
"
```

---

## 7. Check PDF integrity
```cmd
python -c "
import fitz
from pathlib import Path
for p in Path('data/pdfs').glob('*.pdf'):
    doc = fitz.open(p)
    text = doc[0].get_text().strip()[:50]
    status = 'OK' if '%PDF' in open(p,'rb').read(4).decode('latin1') else 'STUB'
    print(f'{status} | {p.name} | {doc.page_count} pages')
    doc.close()
"
```

---

## 8. Clear and re-index from scratch
```cmd
Remove-Item data\chroma_db -Recurse -Force
python scripts\run_ingestion.py --skip-crawl
```

---

## 9. Git workflow
```cmd
git add -A
git commit -m "feat/fix/docs: description"
git push origin main
```

---

## 10. Update requirements after installing new packages
```cmd
pip freeze > requirements.txt
git add requirements.txt
git commit -m "chore: update requirements"
git push origin main
```
