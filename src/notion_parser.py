from __future__ import annotations

from typing import Any, Iterable, Mapping


def _plain_text(items: Iterable[Mapping[str, Any]]) -> str:
    return ''.join(str(item.get('plain_text', '')) for item in items)


def extract_title_from_properties(properties: Mapping[str, Any]) -> str:
    for value in properties.values():
        if value.get('type') == 'title':
            title = _plain_text(value.get('title', []))
            if title:
                return title
    return 'Untitled'


def extract_text_from_blocks(blocks: Iterable[Mapping[str, Any]]) -> str:
    parts = []
    for block in blocks:
        block_type = block.get('type')
        body = block.get(block_type, {}) if isinstance(block_type, str) else {}
        rich_text = body.get('rich_text', []) if isinstance(body, Mapping) else []
        text = _plain_text(rich_text) if isinstance(rich_text, list) else ''
        if text:
            parts.append(text)
    return '\n'.join(parts)


def normalize_notion_page(page: Mapping[str, Any], blocks: Iterable[Mapping[str, Any]] = ()) -> dict[str, str]:
    properties = page.get('properties', {})
    return {
        'id': str(page.get('id', '')),
        'title': extract_title_from_properties(properties) if isinstance(properties, Mapping) else 'Untitled',
        'content': extract_text_from_blocks(blocks),
        'created_time': str(page.get('created_time', '')),
        'last_edited_time': str(page.get('last_edited_time', '')),
        'source': 'notion',
        'url': str(page.get('url', '')),
    }
