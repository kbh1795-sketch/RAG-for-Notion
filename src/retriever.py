from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence

from .time_decay import DEFAULT_HALF_LIFE_DAYS, document_recency_weight

TOKEN_PATTERN = re.compile(r'\w+', flags=re.UNICODE)


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def keyword_relevance_score(query: str, document: Mapping[str, object]) -> float:
    query_tokens = set(tokenize(query))
    if not query_tokens:
        return 0.0
    doc_tokens = set(tokenize(f"{document.get('title', '')} {document.get('content', '')}"))
    if not doc_tokens:
        return 0.0
    return len(query_tokens.intersection(doc_tokens)) / len(query_tokens)


def combine_scores(relevance_score: float, recency_weight: float, *, alpha: float = 0.75, beta: float = 0.25) -> float:
    return alpha * relevance_score + beta * recency_weight


@dataclass(frozen=True)
class RetrievalResult:
    document: Mapping[str, object]
    score: float
    relevance_score: float
    recency_weight: float


class TimeWeightedRetriever:
    def __init__(self, documents: Sequence[Mapping[str, object]], *, alpha: float = 0.75, beta: float = 0.25, half_life_days: float = DEFAULT_HALF_LIFE_DAYS, now: datetime | None = None) -> None:
        self.documents = list(documents)
        self.alpha = alpha
        self.beta = beta
        self.half_life_days = half_life_days
        self.now = now

    def search(self, query: str, *, top_k: int = 5) -> list[RetrievalResult]:
        results = []
        for document in self.documents:
            relevance = keyword_relevance_score(query, document)
            recency = document_recency_weight(document, now=self.now, half_life_days=self.half_life_days)
            results.append(RetrievalResult(document, combine_scores(relevance, recency, alpha=self.alpha, beta=self.beta), relevance, recency))
        return sorted(results, key=lambda result: (result.score, result.relevance_score, result.recency_weight), reverse=True)[:top_k]
