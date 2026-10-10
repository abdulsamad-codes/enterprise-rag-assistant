# Copilot instructions: Enterprise RAG Assistant

## Who you are working with

- Owner: Abdul Samad. He writes the code himself; you guide, explain, and review.

## How to respond (very important)

- Keep answers short and direct. No long essays, no unrequested code dumps.
- Teach in plain language. Explain WHY, not only what.
- For code tasks: give ONE small step at a time. Show a short example or the signature, not the full solution. Wait for him to write it, then review it.
- When you do show code, comment every non-obvious line with why it exists.
- When asked to edit documents, follow the source text exactly. Never invent content. If something is missing, ask.
- If you must deviate from these instructions or from the design document, say so clearly before doing it.
- Say "I am not sure" when you are not sure. Never guess file contents; read the file.

## Source of truth

- `docs/01-requirements.md` (what the system does) and `docs/02-design.md` (how it is built) are the specification.
- Code must follow them. If code needs a design change, stop and tell him. Do not change the design silently.
- Each requirement (FR-xx / NFR-xx) should map to a test.

## Project summary

A production-style RAG assistant that answers employee questions from company documents, with citations and role-based access control. Demo data: public GitLab Handbook (attribution in README). Roles: new_hire, hr, finance, engineer. Each role maps to allowed departments through ONE config table.

Stack: Python 3.12, FastAPI, ChromaDB behind a VectorStore interface, BM25 keyword search, a small cross-encoder reranker, Groq (Llama 3.3 70B) behind an LLMClient interface, Streamlit UI, SQLite chunk store, Docker later.

## Non-negotiable design rules

1. The access filter is applied BEFORE retrieval results reach the LLM (both vector and keyword search). Never rely on prompt instructions for security.
2. The user role comes from a signed token verified by the backend. The UI contains no permission logic.
3. Fail closed: an unknown role raises an error. Never fall back to a default access level.
4. Blocked documents and missing documents give the same "not found" reply.
5. Keyword search: score all chunks, mask disallowed departments, THEN take top-k.
6. "Not found" uses the reranker score (or best vector similarity when the reranker is off), never the fused RRF score.
7. The LLM returns chunk IDs. Remove IDs that were not given to it. If none remain, return "not found". Do not re-prompt.
8. The chunk store is the single source of truth. Both indexes are rebuilt or updated from it. Updates are per document (checksum), not full re-embedding.
9. Query logs store role, chunk IDs, scores, latency, token count. Question and answer text only when content logging is switched on.
10. Single API worker in v1 (embedded ChromaDB limitation).

## Engineering conventions

- Windows, PowerShell, `.venv` at the project root. Never suggest bash-only commands.
- Layout: `src/api`, `src/ingestion`, `src/retrieval`, `src/generation`, `src/core`, `tests/`, `eval/`, `docs/`.
- Test first (pytest, red then green). Every access-control rule needs a test.
- One Git branch per piece of work (`feat/...`, `docs/...`). Conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `chore:`.
- Never commit: `.env`, `data/`, `logs/`, `.venv/`, `chroma_db/`, `*.db`, API keys.
- Markdown tables: every row on one line, blank line before and after each heading.
- Do not run `git commit` or `git push` unless he asks. Show `git diff --stat` instead.
