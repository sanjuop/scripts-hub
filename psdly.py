"""
Universal Web Listing Scraper (psdly.py)
Crawls and extracts article/course titles, links, and rich metadata from PSDLY
or any listing/blog website across paginated pages into a CSV file.

Features:
- Configurable target URL (--url)
- Configurable destination CSV file (--output)
- Deep extraction of File Size, Updated Date, and Description (--deep)
- Real-time live auto-save (zero data loss if script is stopped)
- Auto-resume & deduplication across multiple runs
- Page limit control (--max-pages, 0 = all)
- Keyword filtering (--keyword)
- Universal extraction engine (WordPress, Card grids, custom selectors)
- Polite request delays (--delay)
- UTF-8 Windows safe stream encoding
"""

import sys
import os
import csv
import time
import re
import argparse
import datetime
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

# Ensure Windows UTF-8 stdout
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

DEFAULT_START_URL = "https://www.psdly.site/ai-courses/"
DEFAULT_OUTPUT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scraped_listings.csv")

# Standard browser headers to avoid default bot blocks
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
}


def find_next_page_url(soup: BeautifulSoup, current_url: str) -> str | None:
    """Finds the 'Next' page link using standard pagination structures."""
    # 1. Look for <link rel="next" href="..."> in the HTML <head>
    head_next = soup.find("link", rel="next")
    if head_next and head_next.get("href"):
        return urljoin(current_url, head_next["href"].strip())

    # 2. Look for <a rel="next" href="..."> in pagination bars
    anchor_rel_next = soup.find("a", rel="next")
    if anchor_rel_next and anchor_rel_next.get("href"):
        return urljoin(current_url, anchor_rel_next["href"].strip())

    # 3. Standard WordPress pagination classes
    wp_next = soup.select_one(
        "a.next.page-numbers, .pagination .next, .nav-links .next, a.next-page, .pagination a.next"
    )
    if wp_next and wp_next.get("href"):
        return urljoin(current_url, wp_next["href"].strip())

    # 4. Text-based fallback matching common 'Next' labels
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True).lower()
        if text in ["next", "next »", "next ›", "next page", "older posts", "»", "›"]:
            return urljoin(current_url, a["href"].strip())

    return None


def extract_listings(
    soup: BeautifulSoup,
    base_url: str,
    custom_selector: str = "",
    keyword_filter: str = ""
) -> list[dict[str, str]]:
    """Extracts course titles and article URLs using universal selectors or custom override."""
    listings = []
    candidates = []

    # Priority 1: User-specified custom CSS selector
    if custom_selector.strip():
        try:
            candidates = soup.select(custom_selector.strip())
        except Exception as e:
            print(f"[Warning] Invalid custom selector '{custom_selector}': {e}", flush=True)

    # Priority 2: Standard WordPress theme article title selectors (including JNews / PSDLY)
    if not candidates:
        candidates = soup.select(
            ".jeg_post_title a, "
            "article h3.jeg_post_title a, "
            "article h2.entry-title a, "
            "article h3.entry-title a, "
            "article h2.post-title a, "
            "article h3.post-title a, "
            ".post h2 a, "
            ".post h3 a, "
            "article h2 a, "
            "article h3 a, "
            ".entry-header h2 a, "
            ".entry-title a"
        )

    # Priority 3: General card and item title selectors
    if not candidates:
        candidates = soup.select(
            ".card-title a, .course-title a, .item-title a, "
            "[class*='course'] h2 a, [class*='course'] h3 a, "
            "[class*='card'] h2 a, [class*='card'] h3 a"
        )

    # Priority 4: Main content area headings
    if not candidates:
        main_container = soup.select_one("main, #main, #content, .content-area, .site-main")
        if main_container:
            candidates = main_container.select("h2 a, h3 a")

    filter_word = keyword_filter.strip().lower()

    for link in candidates:
        title = link.get_text(strip=True)
        href = link.get("href", "").strip()

        if not title or not href:
            continue

        # Ignore anchor jumps or javascript links
        if href.startswith("#") or href.startswith("javascript:"):
            continue

        # Apply keyword filter if specified
        if filter_word and filter_word not in title.lower():
            continue

        full_url = urljoin(base_url, href)
        listings.append({
            "title": title,
            "url": full_url
        })

    return listings


def extract_deep_details(session: requests.Session, url: str) -> dict[str, str]:
    """
    Visits the item's detail page to extract rich metadata:
    - File size (e.g. 5.1 GB, 1.2 GB, 500 MB)
    - Updated / Published date
    - Description summary paragraph
    """
    details = {
        "file_size": "N/A",
        "updated_date": "N/A",
        "description": "N/A"
    }

    try:
        resp = session.get(url, timeout=20)
        if resp.status_code != 200:
            return details

        d_soup = BeautifulSoup(resp.text, "html.parser")

        # 1. Updated / Published Date
        date_el = d_soup.select_one(".jeg_meta_date, time, .entry-date, .post-date, [class*='date']")
        if date_el and date_el.get_text(strip=True):
            details["updated_date"] = date_el.get_text(strip=True)
        elif d_soup.find("time"):
            t = d_soup.find("time")
            details["updated_date"] = t.get("datetime") or t.get_text(strip=True)

        # 2. File Size Extraction
        # Look for elements containing 'file size' or 'size'
        size_el = d_soup.find(string=re.compile(r'file\s*size', re.I))
        if size_el and size_el.parent and size_el.parent.parent:
            text_block = size_el.parent.parent.get_text(separator=' ', strip=True)
            m = re.search(r'(?:file\s*size|size)\s*[:\-]?\s*([0-9\.]+\s*(?:GB|MB|KB|TB))', text_block, re.I)
            if m:
                details["file_size"] = m.group(1).strip()
            else:
                m2 = re.search(r'\b([0-9\.]+\s*(?:GB|MB))\b', text_block, re.I)
                if m2:
                    details["file_size"] = m2.group(1).strip()

        # Fallback regex across main content container
        if details["file_size"] == "N/A":
            content_main = d_soup.select_one(".content-inner, .entry-content, .jeg_post_content, article")
            if content_main:
                m3 = re.search(r'(?:file\s*size|size)\s*[:\-]?\s*([0-9\.]+\s*(?:GB|MB|KB|TB))', content_main.get_text(), re.I)
                if m3:
                    details["file_size"] = m3.group(1).strip()

        # 3. Description Summary Paragraph
        content_inner = d_soup.select_one(".content-inner, .entry-content, .jeg_post_content, article")
        if content_inner:
            for p in content_inner.find_all("p"):
                t = p.get_text(strip=True)
                # Filter out short fragments, download links, or disclaimers
                if len(t) > 35 and not any(t.lower().startswith(b) for b in ["download", "password", "file size", "http", "www.", "click here"]):
                    details["description"] = t
                    break

    except Exception:
        pass

    return details


def init_csv(filename: str, is_deep: bool) -> tuple[set[str], int]:
    """
    Initializes the output CSV file.
    If it already exists, reads existing URLs for deduplication and resumes seamlessly.
    If it doesn't exist, creates it and writes the header row.
    Returns (set of seen URLs, existing item count).
    """
    output_path = os.path.abspath(filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    seen_urls = set()
    count = 0

    if is_deep:
        fieldnames = ["title", "url", "file_size", "updated_date", "description", "page_discovered", "scraped_at"]
    else:
        fieldnames = ["title", "url", "page_discovered", "scraped_at"]

    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        try:
            with open(output_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    u = row.get("url", "").strip()
                    if u:
                        seen_urls.add(u)
                        count += 1
            print(f"[Resume] Found existing CSV with {count} items. Resuming without duplicates...", flush=True)
        except Exception as e:
            print(f"[Warning] Could not read existing CSV '{output_path}': {e}", flush=True)
    else:
        try:
            with open(output_path, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
        except OSError as err:
            print(f"[Error] Failed to initialize CSV file '{output_path}': {err}", file=sys.stderr, flush=True)

    return seen_urls, count


def append_to_csv(entry: dict[str, str], filename: str, is_deep: bool):
    """Appends a single scraped record to the CSV file immediately and flushes to disk."""
    output_path = os.path.abspath(filename)
    if is_deep:
        fieldnames = ["title", "url", "file_size", "updated_date", "description", "page_discovered", "scraped_at"]
    else:
        fieldnames = ["title", "url", "page_discovered", "scraped_at"]

    try:
        with open(output_path, mode="a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writerow(entry)
            f.flush()
    except OSError as err:
        print(f"[Error] Failed to append record to CSV '{output_path}': {err}", file=sys.stderr, flush=True)


def save_to_csv(data: list[dict[str, str]], filename: str, is_deep: bool = False):
    """Fallback bulk save helper for backwards compatibility."""
    if not data:
        return
    output_path = os.path.abspath(filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fieldnames = ["title", "url", "file_size", "updated_date", "description", "page_discovered", "scraped_at"] if is_deep else ["title", "url", "page_discovered", "scraped_at"]
    try:
        with open(output_path, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(data)
    except OSError as err:
        print(f"[Error] Failed to write CSV file '{output_path}': {err}", file=sys.stderr, flush=True)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Universal web listing scraper for PSDLY and content websites."
    )
    parser.add_argument(
        "--url", "-u",
        type=str,
        default=DEFAULT_START_URL,
        help=f"Target starting webpage URL (default: {DEFAULT_START_URL})"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=DEFAULT_OUTPUT_CSV,
        help=f"Path to save destination CSV file (default: {DEFAULT_OUTPUT_CSV})"
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        default=False,
        help="Extract deep metadata (file size, updated date, description) from each item's detail page"
    )
    parser.add_argument(
        "--max-pages", "-m",
        type=int,
        default=0,
        help="Maximum pages to scrape (0 = all available pages, default: 0)"
    )
    parser.add_argument(
        "--delay", "-d",
        type=float,
        default=1.0,
        help="Delay in seconds between page requests to be polite (default: 1.0s)"
    )
    parser.add_argument(
        "--keyword", "-k",
        type=str,
        default="",
        help="Optional keyword filter (case-insensitive substring in titles)"
    )
    parser.add_argument(
        "--selector", "-s",
        type=str,
        default="",
        help="Optional custom CSS selector for link headings (e.g. 'article h2 a')"
    )
    return parser.parse_args()


def main():
    args = parse_arguments()

    print("=" * 80, flush=True)
    print(" UNIVERSAL WEB LISTING SCRAPER", flush=True)
    print("=" * 80, flush=True)
    print(f" Target URL      : {args.url}", flush=True)
    print(f" Output File     : {args.output}", flush=True)
    print(f" Deep Details    : {'Enabled (File Size, Date, Description)' if args.deep else 'Disabled (Fast Listing Mode)'}", flush=True)
    print(f" Max Pages       : {'All pages' if args.max_pages <= 0 else args.max_pages}", flush=True)
    print(f" Request Delay   : {args.delay}s", flush=True)
    if args.keyword:
        print(f" Keyword Filter  : '{args.keyword}'", flush=True)
    if args.selector:
        print(f" Custom Selector : '{args.selector}'", flush=True)
    print("=" * 80 + "\n", flush=True)

    session = requests.Session()
    session.headers.update(HEADERS)

    # Initialize CSV immediately and load existing URLs to prevent duplicate scraping
    seen_listing_urls, existing_count = init_csv(args.output, args.deep)
    total_new_scraped = 0

    current_url = args.url
    page_number = 1
    visited_page_urls = set()

    try:
        while current_url:
            if args.max_pages > 0 and page_number > args.max_pages:
                print(f"[Done] Reached configured page limit of {args.max_pages} pages.", flush=True)
                break

            if current_url in visited_page_urls:
                print(f"[Warning] Loop detected on URL: {current_url}. Stopping pagination.", flush=True)
                break

            visited_page_urls.add(current_url)
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [Page {page_number}] Fetching: {current_url}", flush=True)

            try:
                response = session.get(current_url, timeout=15)
                if response.status_code == 403:
                    print("[Error] HTTP 403 (Forbidden). The website may be blocking requests.", file=sys.stderr, flush=True)
                    break
                elif response.status_code == 429:
                    print("[Error] HTTP 429 (Too Many Requests). Rate limited.", file=sys.stderr, flush=True)
                    break
                elif response.status_code != 200:
                    print(f"[Error] Failed to load {current_url} (HTTP {response.status_code})", file=sys.stderr, flush=True)
                    break
            except requests.exceptions.RequestException as err:
                print(f"[Network Error] {err}", file=sys.stderr, flush=True)
                break

            soup = BeautifulSoup(response.text, "html.parser")
            page_listings = extract_listings(
                soup,
                current_url,
                custom_selector=args.selector,
                keyword_filter=args.keyword
            )

            scrape_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if not page_listings:
                print(f"   -> No matching listings found on Page {page_number}.", flush=True)
            else:
                page_new_count = 0
                for item in page_listings:
                    if item["url"] not in seen_listing_urls:
                        seen_listing_urls.add(item["url"])

                        entry = {
                            "title": item["title"],
                            "url": item["url"],
                            "page_discovered": page_number,
                            "scraped_at": scrape_timestamp
                        }

                        if args.deep:
                            print(f"      [Detail] {item['title'][:45]}... ", end="", flush=True)
                            details = extract_deep_details(session, item["url"])
                            entry["file_size"] = details["file_size"]
                            entry["updated_date"] = details["updated_date"]
                            entry["description"] = details["description"]
                            print(f"-> Size: {details['file_size']} | Updated: {details['updated_date']}", flush=True)
                            if args.delay > 0:
                                time.sleep(min(args.delay, 0.5))

                        # Live incremental write directly to disk
                        append_to_csv(entry, args.output, args.deep)
                        total_new_scraped += 1
                        page_new_count += 1

                total_items = existing_count + total_new_scraped
                print(f"   -> Page {page_number}: Saved {page_new_count} new items (Total saved in CSV: {total_items})", flush=True)

            # Check next page
            next_url = find_next_page_url(soup, current_url)
            if next_url:
                current_url = next_url
                page_number += 1
                if args.delay > 0:
                    time.sleep(args.delay)
            else:
                print("\n[Info] No next page link detected. Reached final page.", flush=True)
                current_url = None

    except KeyboardInterrupt:
        print("\n[Stopped] Scraping paused by user. All items up to this moment are already saved.", flush=True)
    finally:
        total_items = existing_count + total_new_scraped
        print(f"\n[DONE] Finished. Total listings in '{os.path.abspath(args.output)}': {total_items} ({total_new_scraped} added in this run)", flush=True)


if __name__ == "__main__":
    main()
