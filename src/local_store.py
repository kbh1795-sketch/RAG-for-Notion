from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping

REQUIRED_FIELDS = {'id', 'title', 'content', 'created_time', 'last_edited_time', 'source', 'url'}


class JsonlDocumentStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def write_documents(self, documents: Iterable[Mapping[str, object]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open('w', encoding='utf-8') as handle:
            for document in documents:
                self._validate(document)
                handle.write(json.dumps(document, ensure_ascii=False, sort_keys=True) + '\n')

    def read_documents(self) -> list[dict[str, object]]:
        if not self.path.exists():
            return []
        documents = []
        with self.path.open('r', encoding='utf-8') as handle:
            for line in handle:
                if line.strip():
                    value = json.loads(line)
                    self._validate(value)
                    documents.append(value)
        return documents

    @staticmethod
    def _validate(document: Mapping[str, object]) -> None:
        missing = REQUIRED_FIELDS.difference(document)
        if missing:
            raise ValueError(f'Document is missing required fields: {sorted(missing)}')
