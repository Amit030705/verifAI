"""
Fast recruiter search engine for resume matching.

Provides inverted index-based search with fuzzy matching and ranking.
Completely isolated from existing backend code.
"""

from search_engine.service import SearchService, SearchResult, SearchQuery

__all__ = ["SearchService", "SearchResult", "SearchQuery"]
