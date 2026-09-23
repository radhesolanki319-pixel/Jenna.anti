#!/usr/bin/env python3
# =============================================================================
# Jenna AI — Real World Access Module
# Async functions for weather, news, web search, time, and URL status.
# No mandatory API keys — uses free / open endpoints.
# =============================================================================

import asyncio
import json
import re
import socket
import subprocess
from datetime import datetime, timezone, timedelta
from urllib.parse import quote_plus

# ---------------------------------------------------------------------------
# IST timezone helper
# ---------------------------------------------------------------------------
IST = timezone(timedelta(hours=5, minutes=30))


def _ist_now() -> datetime:
    return datetime.now(IST)


# ---------------------------------------------------------------------------
# Low-level async HTTP GET (curl-based, no extra deps)
# ---------------------------------------------------------------------------
async def _get(url: str, timeout: int = 15) -> tuple[int, str]:
    """
    Async GET via curl subprocess.
    Returns (http_status_code, body_text).
    Returns (-1, error_message) on failure.
    """
    cmd = [
        "curl", "-sL",
        "-w", "\n__STATUS__:%{http_code}",
        "--max-time", str(timeout),
        "--connect-timeout", "8",
        "-A", "JennaAI/2.0",
        url,
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout + 5)
        text = stdout.decode("utf-8", errors="replace")

        # Parse status code appended by -w
        status = -1
        body   = text
        if "__STATUS__:" in text:
            parts  = text.rsplit("__STATUS__:", 1)
            body   = parts[0].strip()
            try:
                status = int(parts[1].strip())
            except ValueError:
                pass
        return status, body
    except Exception as exc:
        return -1, str(exc)


# ---------------------------------------------------------------------------
# 1. Weather
# ---------------------------------------------------------------------------
async def get_weather(city: str = "auto") -> dict:
    """
    Fetch current weather using wttr.in (no API key needed).

    Args:
        city: City name, or 'auto' to auto-detect from IP.

    Returns:
        {"success": True, "data": {...}} or {"success": False, "error": "..."}
    """
    location = "" if city.lower() == "auto" else quote_plus(city)
    url = f"https://wttr.in/{location}?format=j1"

    status, body = await _get(url)
    if status != 200 or not body:
        return {"success": False, "error": f"HTTP {status}: {body[:200]}"}

    try:
        raw = json.loads(body)
        current = raw["current_condition"][0]
        area    = raw.get("nearest_area", [{}])[0]
        city_name = (
            area.get("areaName", [{}])[0].get("value", "Unknown")
        )
        country = area.get("country", [{}])[0].get("value", "")

        data = {
            "city":           city_name,
            "country":        country,
            "temp_c":         int(current["temp_C"]),
            "temp_f":         int(current["temp_F"]),
            "feels_like_c":   int(current["FeelsLikeC"]),
            "humidity_pct":   int(current["humidity"]),
            "description":    current["weatherDesc"][0]["value"],
            "wind_kmph":      int(current["windspeedKmph"]),
            "wind_dir":       current["winddir16Point"],
            "visibility_km":  int(current["visibility"]),
            "uv_index":       int(current.get("uvIndex", 0)),
            "cloud_cover_pct":int(current["cloudcover"]),
        }
        return {"success": True, "data": data}
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        return {"success": False, "error": f"Parse error: {exc}", "raw": body[:500]}


# ---------------------------------------------------------------------------
# 2. News
# ---------------------------------------------------------------------------
async def get_news(topic: str = "india tech") -> dict:
    """
    Fetch top news headlines using GNews.io free tier (no key) or
    falls back to the RSS-over-JSON trick from Google News.

    Args:
        topic: Search topic / keywords.

    Returns:
        {"success": True, "articles": [...]} or {"success": False, "error": "..."}
    """
    # Primary: GNews (no-key endpoint, limited to 10 articles/day on free tier)
    encoded = quote_plus(topic)
    url = f"https://gnews.io/api/v4/search?q={encoded}&lang=en&country=in&max=5&apikey=free"

    status, body = await _get(url, timeout=12)
    if status == 200:
        try:
            raw      = json.loads(body)
            articles = raw.get("articles", [])
            if articles:
                cleaned = [
                    {
                        "title":       a.get("title", ""),
                        "description": a.get("description", ""),
                        "url":         a.get("url", ""),
                        "source":      a.get("source", {}).get("name", ""),
                        "published":   a.get("publishedAt", ""),
                    }
                    for a in articles
                ]
                return {"success": True, "source": "gnews", "articles": cleaned}
        except Exception:
            pass  # fall through to backup

    # Fallback: Google News RSS (no key, public)
    rss_url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
    status2, body2 = await _get(rss_url, timeout=12)
    if status2 == 200 and body2:
        # Simple regex parse of RSS <item> blocks
        items = re.findall(r"<item>(.*?)</item>", body2, re.DOTALL)
        articles = []
        for item in items[:5]:
            title = re.search(r"<title><!\[CDATA\[(.*?)\]\]></title>", item)
            link  = re.search(r"<link>(.*?)</link>",                   item)
            pub   = re.search(r"<pubDate>(.*?)</pubDate>",             item)
            articles.append({
                "title":       title.group(1) if title else "",
                "url":         link.group(1)  if link  else "",
                "published":   pub.group(1)   if pub   else "",
                "description": "",
                "source":      "Google News",
            })
        if articles:
            return {"success": True, "source": "google_rss", "articles": articles}

    return {
        "success": False,
        "error": f"Both GNews and Google RSS failed. HTTP {status}/{status2}",
    }


# ---------------------------------------------------------------------------
# 3. Web Search (DuckDuckGo Instant Answer API)
# ---------------------------------------------------------------------------
async def search_web(query: str) -> dict:
    """
    Query the DuckDuckGo Instant Answer API.

    Args:
        query: Search query string.

    Returns:
        {"success": True, "data": {...}} or {"success": False, "error": "..."}
    """
    encoded = quote_plus(query)
    url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_redirect=1&no_html=1"

    status, body = await _get(url)
    if status != 200 or not body:
        return {"success": False, "error": f"HTTP {status}: {body[:200]}"}

    try:
        raw = json.loads(body)
        # DuckDuckGo returns empty string for missing fields, not None
        data = {
            "abstract":        raw.get("Abstract", ""),
            "abstract_source": raw.get("AbstractSource", ""),
            "abstract_url":    raw.get("AbstractURL", ""),
            "answer":          raw.get("Answer", ""),
            "answer_type":     raw.get("AnswerType", ""),
            "definition":      raw.get("Definition", ""),
            "definition_url":  raw.get("DefinitionURL", ""),
            "type":            raw.get("Type", ""),
            "entity":          raw.get("Entity", ""),
            "image":           raw.get("Image", ""),
            "related_topics":  [
                {
                    "text": t.get("Text", ""),
                    "url":  t.get("FirstURL", ""),
                }
                for t in raw.get("RelatedTopics", [])[:5]
                if isinstance(t, dict) and t.get("Text")
            ],
        }
        # Determine if we got a meaningful result
        has_content = any([
            data["abstract"], data["answer"], data["definition"],
            data["related_topics"],
        ])
        if not has_content:
            return {
                "success": False,
                "error":   "No instant answer available for this query",
                "data":    data,
            }
        return {"success": True, "query": query, "data": data}
    except (json.JSONDecodeError, KeyError) as exc:
        return {"success": False, "error": f"Parse error: {exc}", "raw": body[:500]}


# ---------------------------------------------------------------------------
# 4. Current IST time & date
# ---------------------------------------------------------------------------
async def get_time_date() -> dict:
    """
    Return the current IST time and date with rich formatting.

    Returns:
        {"success": True, "data": {...}}
    """
    now = _ist_now()
    return {
        "success": True,
        "data": {
            "datetime_iso":    now.isoformat(),
            "date":            now.strftime("%A, %d %B %Y"),
            "time_12h":        now.strftime("%I:%M:%S %p"),
            "time_24h":        now.strftime("%H:%M:%S"),
            "day_of_week":     now.strftime("%A"),
            "day_of_month":    now.day,
            "month":           now.strftime("%B"),
            "year":            now.year,
            "week_number":     now.isocalendar()[1],
            "timezone":        "Asia/Kolkata (IST, UTC+5:30)",
            "unix_timestamp":  int(now.timestamp()),
        },
    }


# ---------------------------------------------------------------------------
# 5. URL Status Checker
# ---------------------------------------------------------------------------
async def check_url_status(url: str) -> dict:
    """
    Check whether a URL/website is reachable and return HTTP status.

    Args:
        url: Full URL (with scheme) to check.

    Returns:
        {"success": True, "data": {...}} or {"success": False, "error": "..."}
    """
    cmd = [
        "curl", "-sL", "-o", "/dev/null",
        "-w", "%{http_code}|%{time_total}|%{url_effective}",
        "--max-time", "15",
        "--connect-timeout", "8",
        url,
    ]
    start = asyncio.get_event_loop().time()
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=20)
        elapsed = asyncio.get_event_loop().time() - start
        output  = stdout.decode("utf-8", errors="replace").strip()

        parts       = output.split("|")
        status_code = int(parts[0]) if parts[0].isdigit() else -1
        time_total  = float(parts[1]) if len(parts) > 1 else elapsed
        final_url   = parts[2] if len(parts) > 2 else url

        is_up = 200 <= status_code < 400

        return {
            "success": True,
            "data": {
                "url":           url,
                "final_url":     final_url,
                "status_code":   status_code,
                "is_up":         is_up,
                "response_ms":   round(time_total * 1000),
                "status_text":   "UP ✅" if is_up else f"DOWN ❌ ({status_code})",
            },
        }
    except asyncio.TimeoutError:
        return {"success": False, "error": "Request timed out", "url": url}
    except Exception as exc:
        return {"success": False, "error": str(exc), "url": url}


# ---------------------------------------------------------------------------
# Convenience: run all checks at once
# ---------------------------------------------------------------------------
async def full_status_report(city: str = "auto") -> dict:
    """Run weather + time check concurrently and return a combined report."""
    weather, time_info = await asyncio.gather(
        get_weather(city),
        get_time_date(),
    )
    return {"weather": weather, "time": time_info}


# ---------------------------------------------------------------------------
# CLI self-test
# ---------------------------------------------------------------------------
async def _self_test():
    import pprint
    pp = pprint.PrettyPrinter(indent=2)

    print("\n=== get_time_date ===")
    pp.pprint(await get_time_date())

    print("\n=== get_weather(auto) ===")
    pp.pprint(await get_weather("auto"))

    print("\n=== search_web('What is Python') ===")
    pp.pprint(await search_web("What is Python programming language"))

    print("\n=== get_news('india technology') ===")
    pp.pprint(await get_news("india technology"))

    print("\n=== check_url_status('https://google.com') ===")
    pp.pprint(await check_url_status("https://google.com"))

    print("\n=== check_url_status('https://definitely-does-not-exist-xyz.com') ===")
    pp.pprint(await check_url_status("https://definitely-does-not-exist-xyz.com"))


if __name__ == "__main__":
    asyncio.run(_self_test())
