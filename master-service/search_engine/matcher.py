"""
Query matching system for resume search.

Finds candidate matches for search queries with fuzzy matching support.
"""

from __future__ import annotations

from search_engine.indexer import CandidateDocument, InvertedIndex
from search_engine.utils import find_fuzzy_matches, tokenize


class QueryMatcher:
    """Matches query tokens against indexed resumes."""

    def __init__(self, index: InvertedIndex, fuzzy_distance: int = 2):
        """
        Initialize matcher.

        Args:
            index: InvertedIndex instance
            fuzzy_distance: Max edit distance for fuzzy matching
        """
        self.index = index
        self.fuzzy_distance = fuzzy_distance

    def match_exact(self, tokens: list[str]) -> dict[str, set[int]]:
        """
        Find exact matches for query tokens.

        Returns:
            Dict mapping token -> set of candidate IDs
        """
        return self.index.lookup_multiple(tokens)

    def match_fuzzy(self, token: str) -> dict[str, set[int]]:
        """
        Find fuzzy matches for a single token.

        Returns:
            Dict mapping fuzzy_token -> set of candidate IDs
        """
        all_tokens = self.index.get_all_tokens()
        fuzzy_matches = find_fuzzy_matches(token, all_tokens, max_distance=self.fuzzy_distance)

        result = {}
        for fuzzy_token in fuzzy_matches:
            candidate_ids = self.index.lookup(fuzzy_token)
            if candidate_ids:
                result[fuzzy_token] = candidate_ids

        return result

    def find_candidates(self, query_tokens: list[str], allow_fuzzy: bool = True) -> dict[int, set[str]]:
        """
        Find all candidates matching any query token.

        Args:
            query_tokens: List of query tokens
            allow_fuzzy: Whether to include fuzzy matches

        Returns:
            Dict mapping candidate_id -> set of matched tokens
        """
        matched_candidates: dict[int, set[str]] = {}

        # Exact matches
        exact_matches = self.match_exact(query_tokens)
        for token, candidate_ids in exact_matches.items():
            for cand_id in candidate_ids:
                if cand_id not in matched_candidates:
                    matched_candidates[cand_id] = set()
                matched_candidates[cand_id].add(token)

        # Fuzzy matches
        if allow_fuzzy:
            for token in query_tokens:
                fuzzy_matches = self.match_fuzzy(token)
                for fuzzy_token, candidate_ids in fuzzy_matches.items():
                    for cand_id in candidate_ids:
                        if cand_id not in matched_candidates:
                            matched_candidates[cand_id] = set()
                        # Mark as fuzzy by prefixing with ~
                        matched_candidates[cand_id].add(f"~{fuzzy_token}")

        return matched_candidates

    def get_candidate_documents(self, candidate_ids: set[int]) -> dict[int, CandidateDocument]:
        """Get candidate documents by IDs."""
        docs = {}
        for cand_id in candidate_ids:
            if doc := self.index.get_document(cand_id):
                docs[cand_id] = doc
        return docs
