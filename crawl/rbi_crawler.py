# crawl/rbi_crawler.py
import sys, time, logging
import requests, pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
from tqdm import tqdm
sys.path.append(str(Path(__file__).parent.parent))
from config import RBI_BASE_URL, RBI_CIRCULAR_INDEX, PDF_DIR, METADATA_FILE

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

MAX_PDFS      = 500
REQUEST_DELAY = 1.5


class RBICrawler:
    def __init__(self):
        self.session = requests.Session()
        PDF_DIR.mkdir(parents=True, exist_ok=True)

    def fetch_circular_index(self) -> list:
        log.info(f"Fetching index: {RBI_CIRCULAR_INDEX}")
        resp = self.session.get(RBI_CIRCULAR_INDEX, timeout=30)
        resp.raise_for_status()
        soup  = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", {"id": "GridView1"})
        if not table:
            log.warning("Table not found")
            return []
        records = []
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) < 4: continue
            link = cols[2].find("a", href=True)
            if not link: continue
            href    = link["href"]
            url     = href if href.startswith("http") else f"{RBI_BASE_URL}/{href.lstrip('/')}"
            circ_no = cols[1].get_text(strip=True)
            date    = cols[0].get_text(strip=True)
            records.append({
                "circular_no": circ_no,
                "date":        date,
                "subject":     cols[2].get_text(strip=True),
                "department":  cols[3].get_text(strip=True),
                "url":         url,
                "filename":    f"{circ_no.replace('/','_')}_{date.replace('/','_')}.pdf",
            })
            if len(records) >= MAX_PDFS: break
        return records

    def download_pdf(self, url: str, filename: str) -> bool:
        dest = PDF_DIR / filename
        if dest.exists():
            return True
        try:
            r = self.session.get(url, timeout=30, stream=True)
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(8192): f.write(chunk)
            return True
        except Exception as e:
            log.error(f"Download failed {url}: {e}")
            return False

    def run(self):
        records  = self.fetch_circular_index()
        ok, fail = 0, 0
        for r in tqdm(records, desc="Downloading"):
            if self.download_pdf(r["url"], r["filename"]): ok += 1
            else: fail += 1
            time.sleep(REQUEST_DELAY)
        pd.DataFrame(records).to_csv(METADATA_FILE, index=False)
        log.info(f"{ok} downloaded, {fail} failed")
        return pd.DataFrame(records)
