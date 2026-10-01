import asyncio
from typing import List, Dict, Any
from app.services.search.base import SearchProvider

class MockSearchProvider(SearchProvider):
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        await asyncio.sleep(0.05)
        q_lower = query.lower()
        if "hackathon" in q_lower or "ai" in q_lower:
            return [
                {
                    "title": "[MOCK DATA] Global AI Builders Hackathon 2026",
                    "url": "https://hackathons.example.com/global-ai-builders-2026",
                    "domain": "hackathons.example.com",
                    "snippet": "[MOCK DATA] Annual hackathon celebrating autonomous agents. Prize pool: $100,000. Registration closes November 15, 2026. Teams up to 4."
                },
                {
                    "title": "[MOCK DATA] Frontier Intelligence Challenge",
                    "url": "https://ai-frontier.example.org/challenge",
                    "domain": "ai-frontier.example.org",
                    "snippet": "[MOCK DATA] Build next-gen reasoning systems. $50,000 cash prizes and compute credits. Deadline: December 1, 2026."
                },
                {
                    "title": "[MOCK DATA] Open Agent Innovation Sprint",
                    "url": "https://devpost.example.com/open-agent-sprint",
                    "domain": "devpost.example.com",
                    "snippet": "[MOCK DATA] Open-source agent workflows. Prizes include $25,000 plus incubator fast-track interviews. Accepting applications until December 20, 2026."
                }
            ][:max_results]
        return [
            {
                "title": f"[MOCK DATA] Search Result for '{query}'",
                "url": f"https://example.com/search?q={query.replace(' ', '+')}",
                "domain": "example.com",
                "snippet": f"[MOCK DATA] Comprehensive details, benchmarks, and information regarding '{query}'."
            }
        ][:max_results]
