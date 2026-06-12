"""Goi Firecrawl Cloud de cao + trich xuat gia tho tu 1 nguon."""
import logging

from firecrawl import Firecrawl

import config

log = logging.getLogger("firecrawl")

_client: Firecrawl | None = None


def get_client() -> Firecrawl:
    global _client
    if _client is None:
        if not config.FIRECRAWL_API_KEY:
            raise RuntimeError("Thieu FIRECRAWL_API_KEY")
        _client = Firecrawl(api_key=config.FIRECRAWL_API_KEY)
    return _client


def scrape_source(source: dict, schema: dict, scrape_cfg: dict) -> list[dict]:
    """Tra ve danh sach dong gia tho (dict) tu 1 nguon."""
    json_format = {"type": "json", "schema": schema}
    if source.get("prompt"):
        json_format["prompt"] = source["prompt"]

    doc = get_client().scrape(
        source["url"],
        formats=[json_format],
        only_main_content=scrape_cfg.get("onlyMainContent", True),
        timeout=scrape_cfg.get("timeoutMs", 60000),
        max_age=scrape_cfg.get("maxAgeMs", 3600000),
    )
    data = getattr(doc, "json", None) or {}
    prices = data.get("prices", []) if isinstance(data, dict) else []
    return [p for p in prices if isinstance(p, dict)]
