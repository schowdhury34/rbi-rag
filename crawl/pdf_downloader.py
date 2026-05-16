# crawl/pdf_downloader.py
import time, shutil, argparse
from pathlib import Path
from playwright.sync_api import sync_playwright
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import PDF_DIR, RBI_BASE_URL

RBI_MASTER_CIRCULAR_URL   = "https://www.rbi.org.in/Scripts/BS_ViewMasterCirculardetails.aspx"
RBI_MASTER_DIRECTION_URL  = "https://www.rbi.org.in/Scripts/BS_ViewMasterDirections.aspx"

# Master Direction IDs to download — selected for relevance to banking queries
PRIORITY_DIRECTION_IDS = [
    12799,  # Priority Sector Lending — Targets and Classification
    13149,  # Commercial Banks — Interest Rates on Advances (MCLR)
    12702,  # Fraud Risk Management — Commercial Banks
    12703,  # Fraud Risk Management — UCBs
    10477,  # Frauds — Classification and Reporting
    12939,  # Housing Finance Companies Directions 2025
    12933,  # NBFC Microfinance Institutions
    13157,  # Commercial Banks — Interest Rate on Deposits
    10201,  # Import of Goods and Services
    10395,  # Export of Goods and Services
]


def _download_one(context, href: str, fname: str, dest: Path) -> bool:
    """Download a single PDF via Playwright browser. Returns True on success."""
    if dest.exists() and dest.read_bytes()[:4] == b'%PDF':
        print(f"  ✅ Already exists: {fname}")
        return True
    elif dest.exists():
        dest.unlink()

    try:
        dl_page = context.new_page()
        download_holder = []
        dl_page.on("download", lambda d: download_holder.append(d))

        try:
            dl_page.goto(href, wait_until="commit", timeout=30000)
        except Exception:
            pass  # "Download is starting" is expected

        time.sleep(3)
        dl_page.close()

        if download_holder:
            tmp = download_holder[0].path()
            if tmp and Path(tmp).exists():
                shutil.copy(tmp, dest)
                if dest.read_bytes()[:4] == b'%PDF':
                    size_kb = dest.stat().st_size // 1024
                    print(f"  ✅ {fname} ({size_kb} KB)")
                    return True
                else:
                    print(f"  ❌ Not real PDF: {fname}")
                    dest.unlink()
                    return False
        print(f"  ❌ No download captured: {fname}")
        return False
    except Exception as e:
        print(f"  ❌ Error {fname}: {e}")
        return False


def download_master_circulars(context, limit: int) -> tuple:
    """Download PDFs from Master Circulars page."""
    print(f"\n{'='*60}")
    print("Downloading Master Circulars...")
    print(f"{'='*60}")

    page = context.new_page()
    page.goto(RBI_MASTER_CIRCULAR_URL, wait_until="networkidle", timeout=30000)
    time.sleep(2)

    links = page.eval_on_selector_all(
        "a[href*='.pdf'], a[href*='.PDF']",
        "els => els.map(e => ({href: e.href, text: e.innerText.trim()}))"
    )
    page.close()
    print(f"Found {len(links)} PDF links")

    ok, fail = 0, 0
    for item in links[:limit]:
        href  = item["href"]
        fname = href.split("/")[-1]
        if not fname.lower().endswith(".pdf"):
            fname = (item["text"] or "circular")[:40].replace(" ","_") + ".pdf"
        dest = PDF_DIR / fname
        if _download_one(context, href, fname, dest):
            ok += 1
        else:
            fail += 1
        time.sleep(1)

    return ok, fail


def download_master_directions(context) -> tuple:
    """Download priority Master Directions by ID."""
    print(f"\n{'='*60}")
    print("Downloading Priority Master Directions...")
    print(f"{'='*60}")

    ok, fail = 0, 0
    for direction_id in PRIORITY_DIRECTION_IDS:
        detail_url = f"https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id={direction_id}"

        # Fetch detail page to find PDF link
        import requests
        from bs4 import BeautifulSoup
        try:
            r = requests.get(detail_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            soup = BeautifulSoup(r.text, "html.parser")

            # Get title for filename
            title_el = soup.find("h2") or soup.find("h3") or soup.find("title")
            title = title_el.get_text(strip=True)[:50] if title_el else f"direction_{direction_id}"
            title = title.replace("/","_").replace(" ","_").replace(",","").replace(":","")

            # Find PDF link
            pdf_link = soup.find("a", href=lambda h: h and ".pdf" in h.lower())
            if not pdf_link:
                # Try iframe or embed
                pdf_link = soup.find("iframe", src=lambda s: s and ".pdf" in s.lower())
                attr = "src" if pdf_link else None
            else:
                attr = "href"

            if not pdf_link or not attr:
                print(f"  ❌ No PDF found for ID {direction_id}: {title[:40]}")
                fail += 1
                continue

            pdf_url = pdf_link[attr]
            if not pdf_url.startswith("http"):
                pdf_url = f"https://www.rbi.org.in/{pdf_url.lstrip('/')}"

            fname = f"MD_{direction_id}_{title[:30]}.pdf"
            dest  = PDF_DIR / fname

            print(f"  Downloading: {title[:50]}")
            if _download_one(context, pdf_url, fname, dest):
                ok += 1
            else:
                fail += 1
            time.sleep(1.5)

        except Exception as e:
            print(f"  ❌ Error for ID {direction_id}: {e}")
            fail += 1

    return ok, fail


def download_pdfs_via_browser(limit: int = 21, include_directions: bool = True):
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    total_ok, total_fail = 0, 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            accept_downloads=True
        )

        # Warm up session
        page = context.new_page()
        print("Warming up session on RBI main site...")
        page.goto(RBI_BASE_URL, wait_until="networkidle", timeout=30000)
        time.sleep(2)
        page.goto(RBI_MASTER_CIRCULAR_URL, wait_until="networkidle", timeout=30000)
        time.sleep(2)
        page.close()

        # Download Master Circulars
        ok, fail = download_master_circulars(context, limit)
        total_ok += ok
        total_fail += fail

        # Download Master Directions
        if include_directions:
            ok, fail = download_master_directions(context)
            total_ok += ok
            total_fail += fail

        browser.close()

    print(f"\n{'='*60}")
    print(f"TOTAL: {total_ok} downloaded, {total_fail} failed")
    print(f"PDFs saved to: {PDF_DIR}")
    print(f"{'='*60}")
    return total_ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Download RBI PDFs via Playwright")
    ap.add_argument("--limit",              type=int,  default=21,   help="Max Master Circulars to download")
    ap.add_argument("--no-directions",      action="store_true",     help="Skip Master Directions download")
    args = ap.parse_args()

    download_pdfs_via_browser(
        limit=args.limit,
        include_directions=not args.no_directions
    )