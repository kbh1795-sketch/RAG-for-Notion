from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from .persona_chat import build_persona_engine

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEB_ROOT = PROJECT_ROOT / 'web'


class Handler(BaseHTTPRequestHandler):
    engine = None

    def do_GET(self) -> None:
        path = unquote(self.path.split('?', 1)[0])
        if path == '/':
            path = '/index.html'
        target = (WEB_ROOT / path.lstrip('/')).resolve()
        if WEB_ROOT.resolve() not in target.parents or not target.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content = target.read_bytes()
        content_type = {'html': 'text/html; charset=utf-8', 'css': 'text/css; charset=utf-8', 'js': 'application/javascript; charset=utf-8'}.get(target.suffix.lstrip('.'), 'application/octet-stream')
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:
        if self.path != '/api/chat':
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        length = int(self.headers.get('Content-Length', '0'))
        payload = json.loads(self.rfile.read(length).decode('utf-8') or '{}')
        message = str(payload.get('message', '')).strip()
        if not message:
            self._json({'error': 'message is required'}, HTTPStatus.BAD_REQUEST)
            return
        self._json(self.engine.chat(message).to_dict())

    def log_message(self, format: str, *args) -> None:
        return

    def _json(self, payload: dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--store', default='examples/sample_notion_docs.jsonl')
    parser.add_argument('--persona-name', default='Previous Me')
    parser.add_argument('--extractive-only', action='store_true')
    args = parser.parse_args()
    Handler.engine = build_persona_engine(store_path=args.store, persona_name=args.persona_name, prefer_openai=not args.extractive_only)
    print(f'Persona chat running at http://{args.host}:{args.port}')
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == '__main__':
    main()
