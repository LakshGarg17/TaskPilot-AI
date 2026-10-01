import socket
import ipaddress
import urllib.parse
from typing import Any, Dict, Optional
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, HttpUrl
from app.agents.tools.base import BaseTool, ToolResult

class WebExtractInput(BaseModel):
    url: str = Field(..., description="The HTTP or HTTPS URL to extract content from")

def is_ssrf_safe(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme.lower() not in ("http", "https"):
        return False
    hostname = parsed.hostname
    if not hostname:
        return False

    # Block localhost by name
    if hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0", "local"):
        return False

    try:
        # Resolve hostname to IP addresses
        addr_info = socket.getaddrinfo(hostname, None)
        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
        return True
    except Exception:
        # If hostname resolution fails, consider unsafe
        return False

class WebExtractTool(BaseTool):
    name = "web_extract"
    description = "Fetches a web page and extracts clean readable text with strict SSRF protection."
    risk_level = "LOW"
    input_schema = WebExtractInput

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any] = None) -> ToolResult:
        validated = self.validate_inputs(inputs)
        url = validated.url.strip()

        if not is_ssrf_safe(url):
            return ToolResult(
                ok=False,
                error="Access to private, loopback, or link-local network addresses is blocked for security (SSRF prevention).",
                summary=f"Blocked potentially unsafe URL: {url}"
            )

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TaskPilot-Agent/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                res = await client.get(url, headers=headers)
                if res.status_code != 200:
                    return ToolResult(
                        ok=False,
                        error=f"HTTP status {res.status_code} while fetching {url}",
                        summary=f"Failed to fetch {url}"
                    )

                # Cap size at 1 MB
                content = res.content[:1024 * 1024]
                soup = BeautifulSoup(content, "html.parser")

                # Remove scripts, styles, navs
                for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                    tag.decompose()

                text = soup.get_text(separator="\n", strip=True)
                # Trim excessive whitespace
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                clean_text = "\n".join(lines[:300])  # Cap at first 300 paragraphs

                domain = urllib.parse.urlparse(url).netloc
                title = soup.title.string.strip() if soup.title and soup.title.string else domain

                sources = [{"title": title, "url": url, "domain": domain}]
                return ToolResult(
                    ok=True,
                    data={"text": clean_text, "title": title, "url": url},
                    sources=sources,
                    summary=f"Extracted {len(clean_text)} characters from {title}"
                )

        except Exception as e:
            return ToolResult(
                ok=False,
                error=f"Error extracting web content: {str(e)}",
                summary=f"Failed to extract content from {url}"
            )
