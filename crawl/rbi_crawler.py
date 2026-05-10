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

RBI_MASTER_CIRCULAR_URL = "https://www.rbi.org.in/Scripts/BS_ViewMasterCirculardetails.aspx"

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
        table = soup.find("table", {"class": "tablebg"})
        if not table:
            log.warning("Table not found")
            return []

        records = []
        for row in table.find_all("tr")[1:]:   # skip header
            cols = row.find_all("td")
            if len(cols) < 4:
                continue

            link     = cols[0].find("a", href=True)
            if not link:
                continue

            circ_no  = link.get_text(separator=" ").strip()
            date_str = cols[1].get_text(strip=True)
            dept     = cols[2].get_text(strip=True)
            subject  = cols[3].get_text(strip=True)

            # Build detail page URL
            href        = link["href"]
            detail_url  = f"{RBI_BASE_URL}/Scripts/{href}" if not href.startswith("http") else href
            filename    = f"{circ_no.split()[0].replace('/','_')}_{date_str.replace('.','_')}.pdf"

            # Filter by year
            year = None
            for part in date_str.replace("-",".").split("."):
                if len(part) == 4 and part.isdigit():
                    year = int(part)
            if year and year < CRAWL_YEAR_FROM:
                continue

            records.append({
                "circular_no": circ_no,
                "date":        date_str,
                "department":  dept,
                "subject":     subject,
                "detail_url":  detail_url,
                "url":         detail_url,   # updated to PDF in download step
                "filename":    filename,
            })
            if len(records) >= MAX_PDFS:
                break

        log.info(f"Found {len(records)} circulars")
        return records

    def download_pdf(self, url: str, filename: str) -> bool:
        dest = PDF_DIR / filename
        if dest.exists():
            return True
        try:
            # Step 1: fetch detail page to find PDF link
            r = self.session.get(url, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            pdf_link = soup.find("a", href=lambda h: h and ".pdf" in h.lower())
            if not pdf_link:
                log.warning(f"No PDF found on detail page: {url}")
                return False
            pdf_url = pdf_link["href"]
            if not pdf_url.startswith("http"):
                pdf_url = f"{RBI_BASE_URL}/{pdf_url.lstrip('/')}"

            # Step 2: download the PDF
            r2 = self.session.get(pdf_url, timeout=REQUEST_TIMEOUT, stream=True)
            r2.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r2.iter_content(8192):
                    f.write(chunk)
            return True
        except Exception as e:
            log.error(f"Failed {filename}: {e}")
            return False    

    

    def run(self):
        records = self.fetch_circular_index()
        master  = self.fetch_master_circulars()
        records = records + master
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

    def fetch_master_circulars(self) -> list:
        log.info(f"Fetching Master Circulars from {RBI_MASTER_CIRCULAR_URL}")
        try:
            resp = self.session.get(RBI_MASTER_CIRCULAR_URL, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as e:
            log.error(f"Failed to fetch master circulars: {e}")
            return []

        soup    = BeautifulSoup(resp.text, "html.parser")
        records = []

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if ".pdf" not in href.lower():
                continue
            subject  = link.get_text(strip=True)
            if not subject:
                continue
            pdf_url  = href if href.startswith("http") else f"{RBI_BASE_URL}/{href.lstrip('/')}"
            filename = pdf_url.split("/")[-1]
            if not filename.endswith(".pdf"):
                filename = subject[:50].replace(" ","_").replace("/","_") + ".pdf"

            records.append({
                "circular_no": f"MC/{filename}",
                "date":        "01.04.2025",
                "department":  "Master Circular",
                "subject":     subject,
                "detail_url":  pdf_url,
                "url":         pdf_url,
                "filename":    filename,
            })
            if len(records) >= MAX_PDFS:
                break

        log.info(f"Found {len(records)} master circulars")
        return records
