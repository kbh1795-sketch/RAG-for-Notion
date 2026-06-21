# Previous Me

Previous Me is a research prototype for talking with a grounded persona reconstructed from your own Notion notes.

The project treats Notion as a personal memory source, retrieves relevant notes with transparent time-weighted ranking, and answers as a reflective "previous self" persona. Newer notes have more influence, while older notes remain available as lower-weight memory.

This is not a claim to recreate a person. It is a retrieval-augmented interface over records you choose to ingest.

## What It Does

- Ingest Notion pages or databases into a local JSONL store.
- Normalize notes into a simple document format.
- Rank notes by lexical relevance plus recency weight.
- Chat with a persona-style interface over retrieved memories.
- Use OpenAI for synthesis when `OPENAI_API_KEY` is available.
- Fall back to deterministic extractive answers when OpenAI is unavailable.
- Show source notes, relevance scores, recency weights, and evidence snippets.

## Project Structure

```text
src/
  notion_ingest.py
  notion_parser.py
  local_store.py
  time_decay.py
  retriever.py
  persona_chat.py
  web_app.py
  openai_answerer.py
  ask_openai.py
  ask.py
  chat.py
web/
  index.html
  styles.css
  app.js
tests/
examples/
docs/
scripts/
```

## Quick Start

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the web app with the sample data:

```powershell
python -m src.web_app --extractive-only
```

Then open:

```text
http://127.0.0.1:8765
```

On this Codex desktop runtime, you can also use:

```powershell
& ".\scripts\run_web.cmd" --extractive-only
```

## OpenAI Mode

Set your API key outside code:

```powershell
$env:OPENAI_API_KEY="sk-your-real-key"
$env:OPENAI_MODEL="gpt-5.2"
```

Run:

```powershell
python -m src.web_app
```

The app will use OpenAI for persona synthesis when the key and SDK are available. Otherwise it falls back to extractive mode.

## Notion Ingestion

Set your Notion key:

```powershell
$env:NOTION_API_KEY="secret_your_notion_integration_token"
```

Ingest pages:

```powershell
python -m src.notion_ingest --page-id YOUR_PAGE_ID --out data/notion_docs.jsonl
```

Ingest databases:

```powershell
python -m src.notion_ingest --database-id YOUR_DATABASE_ID --out data/notion_docs.jsonl
```

Run the app against your ingested memory store:

```powershell
python -m src.web_app --store data/notion_docs.jsonl --persona-name "Previous Me"
```

## CLI Usage

Transparent retrieval only:

```powershell
python -m src.rag_pipeline "planning idea priority" --store examples/sample_notion_docs.jsonl
```

Extractive persona chat:

```powershell
python -m src.chat --store examples/sample_notion_docs.jsonl
```

OpenAI-backed one-shot answer:

```powershell
python -m src.ask_openai "planning freshness urgency" --store examples/sample_notion_docs.jsonl
```

## Scoring

Recency uses `last_edited_time`, falling back to `created_time`:

```text
recency_weight = exp(-age_days / half_life_days)
```

Final retrieval score:

```text
final_score = alpha * relevance_score + beta * recency_weight
```

`alpha`, `beta`, and `half_life_days` are configurable in the retriever and CLI layers.

## Tests

```powershell
python -m unittest discover
```

The tests use mock data and fake OpenAI clients. They do not require real Notion or OpenAI credentials.

## Safety Notes

- Do not commit `.env`, `.env.local`, API keys, or ingested private Notion data.
- The app should cite retrieved notes and avoid unsupported claims.
- Fine-tuning is not used for personal facts; RAG is preferred because notes change over time.

## Current Limitations

- Notion block traversal is direct-child only.
- Lexical relevance is simple token overlap rather than BM25 or embeddings.
- Persona synthesis depends on the quality and coverage of the ingested notes.
- This is a local research prototype, not a hosted multi-user app.

## Roadmap

1. Add recursive Notion block traversal.
2. Add BM25 and optional embedding retrieval.
3. Add conversation memory and user-controlled persona settings.
4. Add a GitHub Actions test workflow.
5. Package the app for easier local installation.
