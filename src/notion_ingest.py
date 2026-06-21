from __future__ import annotations

import argparse
import json
import os
from typing import Any, Mapping, Optional
from urllib.request import Request, urlopen

from .local_store import JsonlDocumentStore
from .notion_parser import normalize_notion_page

NOTION_VERSION = '2022-06-28'
BASE_URL = 'https://api.notion.com/v1'


class NotionClient:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv('NOTION_API_KEY')
        if not self.api_key:
            raise ValueError('NOTION_API_KEY is required')

    def retrieve_page(self, page_id: str) -> Mapping[str, Any]:
        return self._request('GET', f'/pages/{page_id}')

    def list_block_children(self, block_id: str) -> list[Mapping[str, Any]]:
        response = self._request('GET', f'/blocks/{block_id}/children')
        return [item for item in response.get('results', []) if isinstance(item, Mapping)]

    def _request(self, method: str, path: str) -> Mapping[str, Any]:
        request = Request(BASE_URL + path, method=method, headers={'Authorization': f'Bearer {self.api_key}', 'Notion-Version': NOTION_VERSION, 'Content-Type': 'application/json'})
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--page-id', action='append', default=[])
    parser.add_argument('--out', default='data/notion_docs.jsonl')
    args = parser.parse_args()
    client = NotionClient()
    documents = []
    for page_id in args.page_id:
        documents.append(normalize_notion_page(client.retrieve_page(page_id), client.list_block_children(page_id)))
    JsonlDocumentStore(args.out).write_documents(documents)
    print(f'Wrote {len(documents)} documents to {args.out}')


if __name__ == '__main__':
    main()
