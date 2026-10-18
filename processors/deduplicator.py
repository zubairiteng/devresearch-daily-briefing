"""Deduplication engine based on canonical URL normalization and title similarity."""
import re
import urllib.parse
from typing import List, Set
from fetchers.base import RawItem


def normalize_url(url: str) -> str:
    """Strip query tracking parameters and fragment, normalize scheme and trailing slash."""
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url.strip())
        # Filter tracking params
        tracking_params = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
            "ref", "ref_src", "fbclid", "gclid", "msclkid", "source"
        }
        query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
        clean_pairs = [(k, v) for k, v in query_pairs if k.lower() not in tracking_params]
        new_query = urllib.parse.urlencode(clean_pairs)

        # Normalize path
        path = parsed.path.rstrip("/")
        if not path:
            path = ""

        clean_url = urllib.parse.urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            "",  # params
            new_query,
            ""   # fragment
        ))
        return clean_url
    except Exception:
        return url.strip()


STOPWORDS = {
    "a", "an", "the", "by", "with", "for", "of", "and", "or", "in", "on", "at", "to", "from", "is"
}


def stem_word(w: str) -> str:
    """Basic rule-based suffix normalization for titles without heavy dependencies."""
    w = w.lower()
    if w.endswith("ing") and len(w) > 5:
        return w[:-3]
    if w.endswith("ed") and len(w) > 4:
        return w[:-2]
    if w.endswith("es") and len(w) > 4:
        return w[:-2]
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        return w[:-1]
    return w


def normalize_title(title: str) -> str:
    """Normalize title for fuzzy similarity comparison."""
    if not title:
        return ""
    # Strip prefixes like 'Show HN:', 'Ask HN:', '[P]', '[R]'
    text = re.sub(r"^(\[.*?\]|Show HN:|Ask HN:|Tell HN:)\s*", "", title, flags=re.IGNORECASE)
    # Remove punctuation and non-alphanumeric
    text = re.sub(r"[^\w\s]", " ", text)
    # Lowercase, filter stopwords, and stem
    tokens = [stem_word(t) for t in text.lower().split() if t not in STOPWORDS]
    return " ".join(tokens)


def compute_title_similarity(t1: str, t2: str) -> float:
    """Compute token Jaccard similarity between two normalized titles."""
    norm1 = normalize_title(t1)
    norm2 = normalize_title(t2)
    if not norm1 or not norm2:
        return 0.0
    if norm1 == norm2:
        return 1.0

    tokens1: Set[str] = set(norm1.split())
    tokens2: Set[str] = set(norm2.split())
    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    return len(intersection) / len(union)


def deduplicate_news(items: List[RawItem], similarity_threshold: float = 0.65) -> List[RawItem]:
    """Deduplicate raw items by normalized URL and title similarity."""
    unique_items: List[RawItem] = []
    seen_urls: Set[str] = set()

    for item in items:
        clean_url = normalize_url(item.url)
        if clean_url in seen_urls:
            continue

        # Check title similarity against already accepted items
        is_duplicate = False
        for accepted in unique_items:
            sim = compute_title_similarity(item.title, accepted.title)
            if sim >= similarity_threshold:
                # Duplicate detected: merge sources and extra info if applicable
                if item.source_name not in accepted.source_name:
                    accepted.source_name = f"{accepted.source_name}, {item.source_name}"
                # Keep the longer, richer content
                if len(item.content) > len(accepted.content):
                    accepted.content = item.content
                    accepted.summary = item.summary
                is_duplicate = True
                break

        if not is_duplicate:
            item.url = clean_url
            unique_items.append(item)
            seen_urls.add(clean_url)

    return unique_items
