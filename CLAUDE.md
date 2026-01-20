# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered Marketing Research Automation Tool using Google Gemini API with RAG. See README.md for full user documentation.

## Quick Commands

```bash
conda activate marketing-research
python cli.py --mode ingest --docs sample_docs/*.txt
python cli.py --mode research --query "query" --id research_id
python cli.py --mode update --query "query" --id research_id
python cli.py --mode diff --id research_id --old 1 --new 2
```

## Architecture

- `cli.py` → `MarketingResearchAgent` (core/agent.py)
- RAG: Documents → RecursiveCharacterTextSplitter → HuggingFace Embeddings → Chroma DB
- Research: Query → RAG Retrieval → Prompt Template (config.yaml) → Gemini API → JSON Versioning
- Diff: Embedding-based cosine distance comparison

## Key Implementation Details

**Embeddings**: Uses `paraphrase-multilingual-MiniLM-L12-v2` for Korean language support

**Version Storage**: `research_history/{research_id}.json` with structure:
```json
{
  "versions": [{
    "version": 1,
    "timestamp": "ISO8601",
    "query": "...",
    "findings": "...",
    "sources": [...],
    "delta": "..."
  }]
}
```

**Prompt Templates**: Defined in `config.yaml` with placeholders `{rag_context}`, `{query}`, `{previous_research}`

**Environment**: Requires `GEMINI_API_KEY` and optional `GEMINI_MODEL` in `.env`
