# crawl/rbi_crawler.py
import sys, time, logging
import requests, pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
sys.path.append(str(Path(__file__).parent.parent))
from config import RBI_BASE_URL, RBI_CIRCULAR_INDEX

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class RBICrawler:
    def __init__(self):
        self.session = requests.Session()

    def fetch_circular_index(self) -> list:
        log.info(f"Fetching index: {RBI_CIRCULAR_INDEX}")
        resp = self.session.get(RBI_CIRCULAR_INDEX, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        table = soup.find("table", {"id": "GridView1"})
        if not table:
            log.warning("Table not found — check HTML selectors")
            return []

        records = []
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue
            link = cols[2].find("a", href=True)
            if not link:
                continue
            href = link["href"]
            url  = href if href.startswith("http") else f"{RBI_BASE_URL}/{href.lstrip('/')}"
            records.append({
                "circular_no": cols[1].get_text(strip=True),
                "date":        cols[0].get_text(strip=True),
                "subject":     cols[2].get_text(strip=True),
                "department":  cols[3].get_text(strip=True),
                "url":         url,
            })
        return records

    def download_pdf(self, url, filename): pass
    def run(self): pass
