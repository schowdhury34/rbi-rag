# crawl/pdf_downloader.py
import time, shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import PDF_DIR, RBI_BASE_URL

RBI_MASTER_URL = "https://www.rbi.org.in/Scripts/BS_ViewMasterCirculardetails.aspx"

def download_pdfs_via_browser(limit: int = 30):
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    downloaded, failed = 0, 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            accept_downloads=True
        )

        page = context.new_page()
        print("Warming up session on RBI main site...")
        page.goto(RBI_BASE_URL, wait_until="networkidle", timeout=30000)
        time.sleep(2)

        print("Loading Master Circulars page...")
        page.goto(RBI_MASTER_URL, wait_until="networkidle", timeout=30000)
        time.sleep(2)

        links = page.eval_on_selector_all(
            "a[href*='.pdf'], a[href*='.PDF']",
            "els => els.map(e => ({href: e.href, text: e.innerText.trim()}))"
        )
        print(f"Found {len(links)} PDF links\n")
        page.close()

        for item in links[:limit]:
            href  = item["href"]
            fname = href.split("/")[-1]
            if not fname.lower().endswith(".pdf"):
                fname = (item["text"] or "circular")[:40].replace(" ","_") + ".pdf"

            dest = PDF_DIR / fname
            if dest.exists() and dest.read_bytes()[:4] == b'%PDF':
                print(f"✅ Already exists: {fname}")
                downloaded += 1
                continue
            elif dest.exists():
                dest.unlink()

            try:
                dl_page = context.new_page()

                # Set up download handler BEFORE navigation
                download_holder = []
                dl_page.on("download", lambda d: download_holder.append(d))

                # Navigate — download starts automatically
                try:
                    dl_page.goto(href, wait_until="commit", timeout=15000)
                except Exception:
                    pass  # "Download is starting" error is expected, ignore it

                # Wait briefly for download to register
                time.sleep(3)
                dl_page.close()

                if download_holder:
                    download = download_holder[0]
                    tmp_path = download.path()
                    if tmp_path and Path(tmp_path).exists():
                        shutil.copy(tmp_path, dest)
                        if dest.read_bytes()[:4] == b'%PDF':
                            size_kb = dest.stat().st_size // 1024
                            print(f"✅ {fname} ({size_kb} KB)")
                            downloaded += 1
                        else:
                            print(f"❌ Not real PDF: {fname}")
                            dest.unlink()
                            failed += 1
                    else:
                        print(f"❌ No temp file: {fname}")
                        failed += 1
                else:
                    print(f"❌ No download captured: {fname}")
                    failed += 1

                time.sleep(1)

            except Exception as e:
                print(f"❌ {fname}: {e}")
                failed += 1

            

        browser.close()

    print(f"\nDone — {downloaded} downloaded, {failed} failed")
    return downloaded


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=30)
    args = ap.parse_args()
    download_pdfs_via_browser(limit=args.limit)