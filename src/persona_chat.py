from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from .local_store import JsonlDocumentStore
from .retriever import RetrievalResult, TimeWeightedRetriever, tokenize

SENTENCE_PATTERN = re.compile(r'(?<=[.!?。！？])\s+')
DEFAULT_PERSONA_NAME = 'Previous Me'


@dataclass(frozen=True)
class PersonaReply:
    message: str
    answer: str
    mode: str
    persona_name: str
    sources: list[dict[str, object]]

    def to_dict(self) -> dict[str, object]:
        return {'message': self.message, 'answer': self.answer, 'mode': self.mode, 'persona_name': self.persona_name, 'sources': self.sources}


def split_sentences(text: str) -> list[str]:
    compact = ' '.join(text.split())
    return [part.strip() for part in SENTENCE_PATTERN.split(compact) if part.strip()]


def evidence_sentences(query: str, document: Mapping[str, object], *, limit: int = 2) -> list[str]:
    candidates = split_sentences(str(document.get('content', ''))) or [str(document.get('content', ''))]
    query_tokens = set(tokenize(query))
    if not query_tokens:
        return candidates[:limit]
    ranked = sorted(candidates, key=lambda sentence: len(query_tokens.intersection(tokenize(sentence))), reverse=True)
    return [sentence for sentence in ranked if sentence][:limit]


def format_context(results: Sequence[RetrievalResult]) -> str:
    chunks = []
    for index, result in enumerate(results, start=1):
        doc = result.document
        chunks.append('\n'.join([
            f'[{index}] {doc.get("title", "")}',
            f'url: {doc.get("url", "")}',
            f'last_edited_time: {doc.get("last_edited_time", "")}',
            f'score: {result.score:.4f}',
            f'relevance_score: {result.relevance_score:.4f}',
            f'recency_weight: {result.recency_weight:.4f}',
            f'content: {doc.get("content", "")}',
        ]))
    return '\n\n'.join(chunks)


class PersonaChatEngine:
    def __init__(self, documents: Sequence[Mapping[str, object]], *, persona_name: str = DEFAULT_PERSONA_NAME, client: Optional[Any] = None, prefer_openai: bool = True) -> None:
        self.persona_name = persona_name
        self.client = client
        self.prefer_openai = prefer_openai
        self.retriever = TimeWeightedRetriever(documents)

    def chat(self, message: str, *, top_k: int = 5) -> PersonaReply:
        results = [result for result in self.retriever.search(message, top_k=top_k) if result.relevance_score > 0]
        sources = [self._source(message, result, i) for i, result in enumerate(results, start=1)]
        if not results:
            return PersonaReply(message, 'I could not find enough matching memory in the current Notion-derived store.', 'no-evidence', self.persona_name, [])
        if self.prefer_openai:
            try:
                return PersonaReply(message, self._openai_answer(message, results), 'openai', self.persona_name, sources)
            except Exception:
                pass
        lines = [f'I am answering from the records I found as {self.persona_name}.', 'The strongest memory signals are:']
        for source in sources:
            for evidence in source['evidence']:
                lines.append(f'- [{source["citation"]}] {evidence}')
        lines.append('This extractive fallback mirrors evidence rather than inventing a new memory.')
        return PersonaReply(message, '\n'.join(lines), 'extractive', self.persona_name, sources)

    def _openai_answer(self, message: str, results: Sequence[RetrievalResult]) -> str:
        client = self.client or self._make_client()
        response = client.responses.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-5.2'),
            instructions=f'You are {self.persona_name}, a grounded persona built from the user\'s Notion notes. Use only retrieved context. Cite sources as [1]. Answer in Korean by default.',
            input=f'User message:\n{message}\n\nRetrieved memory context:\n{format_context(results)}',
        )
        return str(response.output_text)

    @staticmethod
    def _make_client() -> Any:
        if not os.getenv('OPENAI_API_KEY'):
            raise RuntimeError('OPENAI_API_KEY is not set')
        from openai import OpenAI
        return OpenAI()

    @staticmethod
    def _source(message: str, result: RetrievalResult, citation: int) -> dict[str, object]:
        doc = result.document
        return {'citation': citation, 'title': doc.get('title', ''), 'score': result.score, 'relevance_score': result.relevance_score, 'recency_weight': result.recency_weight, 'last_edited_time': doc.get('last_edited_time', ''), 'url': doc.get('url', ''), 'evidence': evidence_sentences(message, doc)}


def build_persona_engine(*, store_path: str, persona_name: str = DEFAULT_PERSONA_NAME, prefer_openai: bool = True) -> PersonaChatEngine:
    documents = JsonlDocumentStore(store_path).read_documents()
    return PersonaChatEngine(documents, persona_name=persona_name, prefer_openai=prefer_openai)
