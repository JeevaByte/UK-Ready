"""
gov.uk document scraper for UKReady's RAG knowledge base.

Scrapes the official gov.uk visa guidance pages that are relevant to
the four supported visa types. Each page is fetched, cleaned, and
returned as a structured dict ready for chunking and embedding.

Design decisions:
- Rate limiting: 1 request/second to be a good citizen to gov.uk
- Robust HTML parsing: gov.uk uses consistent .govuk-* CSS classes
- Last-modified tracking: stored with each chunk so citations are accurate
- No JavaScript rendering needed: gov.uk pages are fully server-rendered
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# The 10 gov.uk URLs to scrape for the MVP knowledge base.
# Covers all four visa types: Graduate, Skilled Worker, Student, ILR.
GOV_UK_URLS: list[str] = [
    "https://www.gov.uk/graduate-visa",
    "https://www.gov.uk/skilled-worker-visa",
    "https://www.gov.uk/student-visa",
    "https://www.gov.uk/indefinite-leave-to-remain",
    "https://www.gov.uk/skilled-worker-visa/your-job",
    "https://www.gov.uk/skilled-worker-visa/your-salary",
    "https://www.gov.uk/graduate-visa/what-you-can-do",
    "https://www.gov.uk/check-uk-visa",
    "https://www.gov.uk/legal-right-work-uk",
    "https://www.gov.uk/skilled-worker-visa/switch-to-this-visa",
]

# Rate limit: seconds between requests to gov.uk
REQUEST_DELAY_SECONDS = 1.0

# Request timeout in seconds
REQUEST_TIMEOUT = 15

# Browser-like headers to avoid being blocked
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; UKReadyBot/1.0; "
        "+https://github.com/jeevabyte/uk-ready) "
        "UKReady open source project for UK skilled migrants"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-GB,en;q=0.9",
}


@dataclass
class ScrapedPage:
    """A scraped gov.uk page, ready for chunking."""

    url: str
    title: str
    content: str  # Clean text, HTML stripped
    last_scraped: str  # ISO datetime string


def _extract_text(soup: BeautifulSoup) -> str:
    """
    Extract readable text from a gov.uk page.

    gov.uk uses consistent markup:
    - Main content is in .govuk-govspeak or .gem-c-govspeak
    - Section headers in h2, h3 elements
    - Body text in p, li elements

    We preserve section headers in the extracted text so they can be
    included in chunks for context (e.g. "Working hours" heading tells
    the embedder what section a chunk is from).
    """
    # Try primary content selectors in order of preference
    content_selectors = [
        ".govuk-govspeak",
        ".gem-c-govspeak",
        ".govuk-grid-column-two-thirds",
        "main",
        "#content",
    ]

    content_div = None
    for selector in content_selectors:
        content_div = soup.select_one(selector)
        if content_div:
            break

    if not content_div:
        # Fall back to the whole body if no main content found
        content_div = soup.find("body")

    if not content_div:
        return ""

    # Remove navigation, breadcrumbs, and footer elements that aren't content
    for tag in content_div.select(  # type: ignore[union-attr]
        "nav, .gem-c-breadcrumbs, .govuk-breadcrumbs, "
        ".gem-c-related-navigation, footer, .govuk-footer, "
        ".gem-c-print-link, script, style"
    ):
        tag.decompose()

    # Extract text with section structure preserved
    parts: list[str] = []
    for element in content_div.find_all(["h1", "h2", "h3", "h4", "p", "li"]):  # type: ignore[union-attr]
        text = element.get_text(separator=" ", strip=True)
        if not text:
            continue

        tag_name = element.name
        if tag_name in ("h1", "h2"):
            # Section headers get visual separation to help chunking
            parts.append(f"\n\n## {text}\n")
        elif tag_name in ("h3", "h4"):
            parts.append(f"\n### {text}\n")
        elif tag_name == "li":
            parts.append(f"- {text}")
        else:
            parts.append(text)

    return "\n".join(parts).strip()


def scrape_page(url: str) -> ScrapedPage | None:
    """
    Scrape a single gov.uk page and return structured content.

    Args:
        url: The gov.uk URL to scrape.

    Returns:
        ScrapedPage if successful, None if the page could not be fetched.
    """
    logger.info("Scraping page", extra={"url": url})

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Failed to fetch page", extra={"url": url, "error": str(exc)})
        return None

    soup = BeautifulSoup(response.text, "lxml")

    # Extract page title
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else url

    # Extract main content
    content = _extract_text(soup)

    if not content:
        logger.warning("No content extracted from page", extra={"url": url})
        return None

    scraped_at = datetime.now(UTC).isoformat()

    logger.info(
        "Page scraped successfully",
        extra={"url": url, "title": title, "content_length": len(content)},
    )

    return ScrapedPage(
        url=url,
        title=title,
        content=content,
        last_scraped=scraped_at,
    )


def scrape_all_pages(
    urls: list[str] | None = None,
    delay_seconds: float = REQUEST_DELAY_SECONDS,
) -> list[ScrapedPage]:
    """
    Scrape all gov.uk URLs in the knowledge base.

    Args:
        urls: List of URLs to scrape. Defaults to GOV_UK_URLS.
        delay_seconds: Pause between requests (rate limiting).

    Returns:
        List of successfully scraped pages (failed pages are skipped with a warning).
    """
    urls = urls or GOV_UK_URLS
    pages: list[ScrapedPage] = []
    failed_urls: list[str] = []

    logger.info("Starting gov.uk scrape", extra={"total_urls": len(urls)})

    for i, url in enumerate(urls):
        page = scrape_page(url)
        if page:
            pages.append(page)
        else:
            failed_urls.append(url)

        # Rate limit — don't hammer gov.uk
        if i < len(urls) - 1:
            time.sleep(delay_seconds)

    logger.info(
        "Scrape complete",
        extra={
            "success_count": len(pages),
            "failed_count": len(failed_urls),
            "failed_urls": failed_urls,
        },
    )

    return pages
