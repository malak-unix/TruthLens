from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.config import get_settings


def extract_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower().replace("www.", "")


def clean_text(value: str) -> str:
    return " ".join((value or "").split())


def extract_article_from_url(url: str) -> dict:
    settings = get_settings()

    result = {
        "url": url,
        "domain": extract_domain(url),
        "title": "",
        "meta_description": "",
        "text": "",
        "author": "",
        "published_at": "",
        "status": "not_fetched",
        "error": None,
    }

    headers = {
        "User-Agent": "TruthLens/1.0 (+hackathon credibility monitor)"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        result["status"] = "failed"
        result["error"] = str(exc)
        return result

    soup = BeautifulSoup(response.text, "html.parser")

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    meta_description = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        meta_description = meta_tag["content"].strip()

    author = ""
    for attrs in (
        {"name": "author"},
        {"property": "author"},
        {"property": "article:author"},
    ):
        author_tag = soup.find("meta", attrs=attrs)
        if author_tag and author_tag.get("content"):
            author = author_tag["content"].strip()
            break

    published_at = ""
    for attrs in (
        {"property": "article:published_time"},
        {"property": "og:published_time"},
        {"name": "pubdate"},
        {"name": "publishdate"},
        {"name": "timestamp"},
        {"name": "date"},
    ):
        published_tag = soup.find("meta", attrs=attrs)
        if published_tag and published_tag.get("content"):
            published_at = published_tag["content"].strip()
            break

    paragraphs = []
    for p in soup.find_all("p"):
        text = clean_text(p.get_text(" ", strip=True))
        if len(text.split()) >= 8:
            paragraphs.append(text)

    article_text = " ".join(paragraphs[:12])

    result["title"] = clean_text(title)
    result["meta_description"] = clean_text(meta_description)
    result["text"] = clean_text(article_text)
    result["author"] = clean_text(author)
    result["published_at"] = clean_text(published_at)
    result["status"] = "ok"

    return result
