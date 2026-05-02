# crawl/rbi_crawler.py
import sys, time, logging
import requests, pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
from tqdm import tqdm
sys.path.append(str(Path(__file__).parent.parent))
from config import (RBI_BASE_URL, RBI_CIRCULAR_INDEX, PDF_DIR,
                    METADATA_FILE, MAX_PDFS, REQUEST_DELAY,
                    REQUEST_TIMEOUT, REQUEST_HEADERS, CRAWL_YEAR_FROM)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def _parse_year(date_str: str) -> int | None:
    """Extract year from date strings like '01/04/2023' or '2023-04-01'."""
    for part in date_str.replace("-", "/").split("/"):
        if len(part) == 4 and part.isdigit():
            return int(part)
    return None


class RBICrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(REQUEST_HEADERS)
        PDF_DIR.mkdir(parents=True, exist_ok=True)

    def fetch_circular_index(self) -> list:
        log.info(f"Fetching index from {RBI_CIRCULAR_INDEX}")
        try:
            resp = self.session.get(RBI_CIRCULAR_INDEX, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as e:
            log.error(f"Failed to fetch index: {e}")
            return []

        soup  = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", {"id": "GridView1"})
        if not table:
            log.warning("Circular table not found — RBI may have changed HTML structure")
            return []

        records  = []
        skipped  = 0
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue
            link = cols[2].find("a", href=True)
            if not link:
                continue

            date_str = cols[0].get_text(strip=True)

            # Skip circulars older than CRAWL_YEAR_FROM
            year = _parse_year(date_str)
            if year and year < CRAWL_YEAR_FROM:
                skipped += 1
                continue

            href     = link["href"]
            url      = href if href.startswith("http") else f"{RBI_BASE_URL}/{href.lstrip('/')}"
            circ_no  = cols[1].get_text(strip=True)
            filename = f"{circ_no.replace('/','_')}_{date_str.replace('/','_')}.pdf"

            records.append({
                "circular_no": circ_no,
                "date":        date_str,
                "subject":     cols[2].get_text(strip=True),
                "department":  cols[3].get_text(strip=True),
                "url":         url,
                "filename":    filename,
            })
            if len(records) >= MAX_PDFS:
                break

        log.info(f"Found {len(records)} circulars (skipped {skipped} older than {CRAWL_YEAR_FROM})")
        return records

    def download_pdf(self, url: str, filename: str) -> bool:
        dest = PDF_DIR / filename
        if dest.exists():
            return True   # resume-safe
        try:
            r = self.session.get(url, timeout=REQUEST_TIMEOUT, stream=True)
            r.raise_for_status()
            if "pdf" not in r.headers.get("Content-Type", "").lower():
                log.warning(f"Not a PDF: {url}")
                return False
            with open(dest, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            return True
        except Exception as e:
            log.error(f"Download failed {filename}: {e}")
            return False

    def run(self):
        records = self.fetch_circular_index()
        if not records:
            log.error("No records found. Exiting.")
            return None
        ok, fail = 0, 0
        for r in tqdm(records, desc="Downloading PDFs"):
            if self.download_pdf(r["url"], r["filename"]): ok += 1
            else: fail += 1
            time.sleep(REQUEST_DELAY)
        df = pd.DataFrame(records)
        df.to_csv(METADATA_FILE, index=False)
        log.info(f"Done — {ok} downloaded, {fail} failed. Metadata saved.")
        return df
