"""GitHub releases fetcher for key open-source AI and dev tools."""
import logging
from datetime import datetime, timezone
from typing import List
import httpx
from dateutil import parser as date_parser

from .base import BaseFetcher, RawItem
from config.sources_loader import GitHubConfig

logger = logging.getLogger(__name__)


class GitHubFetcher(BaseFetcher):
    name = "GitHubFetcher"

    def __init__(self, config: GitHubConfig):
        self.config = config

    async def fetch(self) -> List[RawItem]:
        if not self.config.enabled:
            return []

        items: List[RawItem] = []
        async with httpx.AsyncClient(timeout=12.0, headers={"User-Agent": "DevResearchBriefing/1.0"}) as client:
            for repo in self.config.repositories:
                try:
                    url = f"https://api.github.com/repos/{repo}/releases/latest"
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        continue

                    data = resp.json()
                    tag_name = data.get("tag_name", "")
                    release_name = data.get("name") or tag_name
                    body = data.get("body", "")
                    html_url = data.get("html_url", f"https://github.com/{repo}/releases")

                    pub_str = data.get("published_at")
                    pub_date = None
                    if pub_str:
                        try:
                            pub_date = date_parser.parse(pub_str)
                            if pub_date.tzinfo is None:
                                pub_date = pub_date.replace(tzinfo=timezone.utc)
                            # Only include fresh releases from the last 72 hours
                            if (datetime.now(timezone.utc) - pub_date).total_seconds() > 72 * 3600:
                                logger.debug(f"Skipping older release for {repo} ({pub_str})")
                                continue
                        except Exception:
                            pass

                    clean_body = " ".join(body.split()[:150]) if body else "New open source release."

                    items.append(
                        RawItem(
                            title=f"{repo} Release: {release_name}",
                            url=html_url,
                            source_name="GitHub Releases",
                            category="software_cloud",
                            content=body[:2000],
                            summary=f"Latest release for {repo} ({tag_name}): {clean_body}",
                            published_at=pub_date or datetime.now(timezone.utc),
                            author=data.get("author", {}).get("login"),
                            extra={"repo": repo, "tag": tag_name}
                        )
                    )
                except Exception as e:
                    logger.warning(f"Failed fetching GitHub release for {repo}: {e}")
        return items
