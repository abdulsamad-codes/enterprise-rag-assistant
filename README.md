# Enterprise RAG Assistant

A production-style assistant that answers employee questions from company documents with citations and role-based access control.

## Status

Phase 3: implementation in progress

## Planned stack

Python, FastAPI, ChromaDB, BM25, reranker, Groq, Streamlit, Docker

## Setup and tests

Use Python 3.12 and PowerShell from the project root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
```

## Documentation

- [Requirements](docs/01-requirements.md)
- [Design](docs/02-design.md)
- [Data sources](docs/data-sources.md)

## Attribution

Demo documents come from the public [GitLab Handbook](https://handbook.gitlab.com), licensed under the [Creative Commons Attribution-ShareAlike 4.0 International license](https://creativecommons.org/licenses/by-sa/4.0/).
