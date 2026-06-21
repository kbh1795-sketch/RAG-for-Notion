# RAG-for-Notion: Previous Me

A minimal research prototype for chatting with a grounded persona reconstructed from your own Notion notes.

The app treats Notion as a personal memory source, retrieves relevant notes with transparent time-weighted ranking, and answers as a reflective previous-self persona. Newer notes have stronger influence, while older notes remain available as lower-weight memory.

This is not a claim to recreate a person. It is a retrieval-augmented interface over records you choose to ingest.

## Features

- Notion-style document normalization
- JSONL local memory store
- relevance + recency retrieval
- persona chat engine
- local web chat UI
- optional OpenAI synthesis via `OPENAI_API_KEY`
- extractive fallback when OpenAI is unavailable

## Quick Start

```powershell
python -m pip install -r requirements.txt
python -m src.web_app --extractive-only
```

Open:

```text
http://127.0.0.1:8765
```

Ask:

```text
planning freshness urgency
```

## OpenAI Mode

```powershell
$env:OPENAI_API_KEY="sk-your-real-key"
$env:OPENAI_MODEL="gpt-5.2"
python -m src.web_app
```

## Notion Data

For the MVP, the app reads normalized JSONL documents:

```json
{"id":"...","title":"...","content":"...","created_time":"...","last_edited_time":"...","source":"notion","url":"..."}
```

The prototype includes `examples/sample_notion_docs.jsonl`. Real Notion ingestion can be extended in `src/notion_ingest.py`.

## Scoring

```text
recency_weight = exp(-age_days / half_life_days)
final_score = alpha * relevance_score + beta * recency_weight
```

`last_edited_time` is primary. `created_time` is the fallback.

## Tests

```powershell
python -m unittest discover
```

## Safety

Do not commit `.env`, `.env.local`, API keys, or private exported Notion data.
