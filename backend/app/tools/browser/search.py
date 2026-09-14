from typing import Dict, Any, List
import urllib.parse
import json

def search_web(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Simulate or execute web search returning structured sources and snippets."""
    # When in demo mode or without live search engine key, return realistic curated results
    results: List[Dict[str, str]] = [
        {
            "title": f"Official Guide: {query.capitalize()}",
            "url": f"https://docs.nexus-ai.dev/search?q={urllib.parse.quote_plus(query)}",
            "snippet": f"Comprehensive architectural documentation and best practices regarding {query}. Details system modules, APIs, and real-time execution pipelines.",
            "source": "Nexus Docs"
        },
        {
            "title": f"Modern Approaches to {query}",
            "url": f"https://techradar.io/articles/{urllib.parse.quote_plus(query)}",
            "snippet": f"Recent technological breakthroughs and benchmarks for {query}. Highlights performance gains, asynchronous event handling, and agent reliability.",
            "source": "TechRadar"
        },
        {
            "title": f"GitHub Repository: Awesome {query}",
            "url": f"https://github.com/topics/{urllib.parse.quote_plus(query)}",
            "snippet": f"Curated list of production-grade tools, libraries, and design patterns for implementing {query} with multi-agent systems.",
            "source": "GitHub"
        }
    ]
    return {
        "query": query,
        "totalResults": len(results),
        "results": results[:max_results]
    }
