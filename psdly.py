"""
Universal Web Listing Scraper (psdly.py)
Crawls and extracts article/course titles, links, and metadata from PSDLY
or any listing/blog website across paginated pages into a CSV file.

Features:
- Configurable target URL (--url)
- Configurable destination CSV file (--output)
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

    # Priority 2: Standard WordPress theme article title selectors
    if not candidates:
        candidates = soup.select(
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

    # Keyword filter lowercase
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


def save_to_csv(data: list[dict[str, str]], filename: str):
    """Saves the extracted listings to a CSV file using UTF-8-sig encoding."""
    if not data:
        print("[Warning] No records collected. CSV file was not created.", flush=True)
        return

    output_path = os.path.abspath(filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        with open(output_path, mode="w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=["title", "url", "page_discovered", "scraped_at"]
            )
            writer.writeheader()
            writer.writerows(data)

        print(f"\n[DONE] Successfully saved {len(data)} listings to:\n -> {output_path}", flush=True)
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
        "--max-pages", "-m",
        type=int,
        default=0,
        help="Maximum pages to scrape (0 = all available pages, default: 0)"
    )
    parser.add_argument(
        "--delay", "-d",
        type=float,
        default=1.5,
        help="Delay in seconds between page requests to be polite (default: 1.5s)"
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
    print(f" Max Pages       : {'All pages' if args.max_pages <= 0 else args.max_pages}", flush=True)
    print(f" Request Delay   : {args.delay}s", flush=True)
    if args.keyword:
        print(f" Keyword Filter  : '{args.keyword}'", flush=True)
    if args.selector:
        print(f" Custom Selector : '{args.selector}'", flush=True)
    print("=" * 80 + "\n", flush=True)

    session = requests.Session()
    session.headers.update(HEADERS)

    current_url = args.url
    page_number = 1
    seen_listing_urls = set()
    visited_page_urls = set()
    all_courses = []

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
                new_count = 0
                for item in page_listings:
                    if item["url"] not in seen_listing_urls:
                        seen_listing_urls.add(item["url"])
                        all_courses.append({
                            "title": item["title"],
                            "url": item["url"],
                            "page_discovered": page_number,
                            "scraped_at": scrape_timestamp
                        })
                        new_count += 1

                print(f"   -> Page {page_number}: Found {len(page_listings)} items ({new_count} new, {len(all_courses)} total unique)", flush=True)

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
        print("\n[Stopped] Scraping paused by user. Saving collected entries...", flush=True)
    finally:
        save_to_csv(all_courses, args.output)


if __name__ == "__main__":
    main()
