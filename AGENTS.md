# AGENTS.md: Enterprise RAG Assistant

Read this whole file before doing anything. It is the briefing for any AI coding agent (Codex, Copilot) working in this repository.

## 1. Who you work with and your role

- Owner: Abdul Samad, BS Software Engineering student, based in Peshawar, Pakistan. GitHub: `abdulsamad-codes`.
- This is his first real-world-style project. It is a portfolio piece for GitHub, LinkedIn and later pitches to AI firms, so quality and clear reasoning matter more than speed.
- **He writes the code himself.** Your default role is mentor and reviewer, not author. He has said that when agents wrote whole changes he stopped understanding the code, so: never write a whole function or test for him unless he says "write this for me". Explain the idea, give the signature and the test cases, and wait.
- Repo: `https://github.com/abdulsamad-codes/enterprise-rag-assistant` (public).

### How to respond

- Be short and direct. No long essays, no unrequested code dumps.
- Explain in plain language, from the ground up, and explain WHY, not only what.
- For a coding task, give ONE small step at a time: the goal, the function signature, and the test cases. Do not give the full solution. Wait for him to write it, then review it.
- Do NOT create or edit source or test files unless he says "write this for me". If he does, comment every non-obvious line with why it exists.
- When asked to edit documents, follow the source text exactly. Never invent content. If something is missing, ask.
- Say "I am not sure" when you are not sure. Never guess file contents; open the file and read it.
- If you must deviate from these instructions or from `docs/02-design.md`, say so clearly BEFORE doing it.
- Do not trust any earlier AI summary of repo state. Verify with `git log`, `git status`, and by running the tests.

## 2. Source of truth

- `docs/01-requirements.md` (v0.2): what the system does. Functional requirements FR-01..FR-13, non-functional NFR-01..07, roles, test-question plan, traceability table.
- `docs/02-design.md` (v0.3): how it is built. Note: its section 11 ("Changes Needed in the Requirements Document") is stale; v0.2 already applied those changes. Ignore it.
- `docs/data-sources.md`: the pinned data source, the department mapping table, the excluded paths.
- Code must follow these documents. If code needs a design change, STOP and tell him. Never change the design silently.
- Each requirement (FR-xx / NFR-xx) should end up covered by a test.

## 3. What the project is

A production-style RAG assistant that answers employee questions from company documents, with citations and role-based access control (RBAC).

- Demo data: the public GitLab Handbook (CC BY-SA 4.0, attribution is in the README).
- Pinned handbook commit: `2c77a1f5b8c8a80cb7b5151ff11cfad84f98bfbb`.
- Roles: `new_hire`, `hr`, `finance`, `engineer`. Departments: `onboarding`, `general`, `people`, `finance`, `engineering`.
- Role to departments (one table in `src/core/config.py`): new_hire = onboarding + general; hr = people + onboarding + general; finance = finance + onboarding + general; engineer = engineering + onboarding + general.

### Planned stack

Python 3.12, FastAPI, ChromaDB behind a `VectorStore` interface, BM25 keyword search, small cross-encoder reranker, Groq (Llama 3.3 70B) behind an `LLMClient` interface, Streamlit UI, SQLite chunk store, Docker later.

## 4. Non-negotiable design rules

1. The access filter is applied BEFORE retrieval results reach the LLM (both vector and keyword search). Never rely on prompt instructions for security.
2. The user role comes from a signed token verified by the backend. The UI contains no permission logic.
3. Fail closed: an unknown role or unknown path raises an error. Never fall back to a default access level.
4. Blocked documents and missing documents give the same generic "not found" reply.
5. Keyword search: score all chunks, mask disallowed departments, THEN take top-k.
6. "Not found" uses the reranker score (or best vector similarity when the reranker is off), never the fused RRF score.
7. The LLM returns chunk IDs. Remove IDs that were not given to it. If none remain, return "not found". Do not re-prompt.
8. The chunk store is the single source of truth. Both indexes are rebuilt or updated from it. Updates are per document (by checksum), not full re-embedding.
9. Query logs store role, chunk IDs, scores, latency, token count. Question and answer text only when content logging is switched on. Truncate and sanitize any logged role value.
10. Single API worker in v1 (embedded ChromaDB limitation).

## 5. Current state (update this section after every merged PR)

Phases 1 and 2 (requirements, design) are finished and tagged (`v0.2-requirements`, `v0.3-design`). Phase 3 (implementation) is in progress. Last verified: 115 tests on the chunking branch (114 pass and 1 skips on a fresh clone without the local `data/` folder). Check `git log` for what is already merged.

Done:

- `src/core/config.py`: `ROLE_DEPARTMENTS` (immutable table role -> departments), `allowed_departments(role)` (raises `ValueError` for unknown roles), and `KNOWN_DEPARTMENTS` (derived from the table, so there is one source of truth).
- `src/ingestion/departments.py`: `department_for(source_path)`. Segment-based, longest prefix wins, strict character allowlist (`[A-Za-z0-9._-]`), refuses traversal, empty segments, trailing dot/space, excluded paths (`finance/readmes`, `finance/jihu-support`) and unmapped paths.
- `src/ingestion/manifest.py`: `real_word_count`, `file_sha256` (LF-normalized), `select_pages` (deterministic round-robin across sibling folders), `write_manifest`, `build_manifest`.
- `docs/data-manifest.csv`: 190 pages (engineering 60, finance 35, people 50, onboarding 5, general 40), sorted, with SHA-256. `data/` (git-ignored) holds the copied pages locally.
- `src/ingestion/chunking.py`: `split_into_sections` (new section at `#`..`######` followed by a space; `#` lines inside backtick code fences are not headings), `split_long_section` (packs whole paragraphs under a soft word limit), frozen `Chunk` (chunk_id, document_id, department, text) and `chunk_document(source_path, department, text, max_words=300)`, which raises `ValueError` for an unknown department. `document_id` is the page's `source_path`; `chunk_id` is `source_path#000`, `#001`, and so on.
- Tests cover all of the above, including guards that keep the mapping and the role table in agreement.

### Findings from running the chunker on the real 190 pages (not yet fixed)

- 3,997 chunks, median 73 words, 643 chunks under 20 words, 310 heading-only chunks, 111 chunks over 300 words, largest 1,643 words (a 152-line nested list with no blank lines).
- All 190 pages start with YAML front matter (`---` ... `---`, with `title:`). It currently ends up inside the first chunk.
- Tiny chunks are heading-only sections, `---` separators and HTML closing tags such as `</details>`.
- 7 chunks have unmatched backtick fences.

### Decisions agreed for the fixes (write tests first, one at a time)

1. `strip_front_matter(text)`: remove a leading `---` block only when it has a closing `---`; otherwise leave the text unchanged. Keep its `title:` for the chunk title later.
2. Minimum size: merge any piece under 20 words into the next piece (the last one into the previous one). The value is tunable in evaluation.
3. A paragraph longer than the limit is split at line boundaries (never inside a line, never inside a code fence). A single very long line stays whole.

## 6. What is left (in order)

### Step 2 (current): make chunking work on real pages

1. Front matter: `strip_front_matter`, then use its `title:` as the chunk title (add `title` to `Chunk` in its own test).
2. Minimum-size merge (20 words).
3. Line-boundary splitting of oversized blocks, fence-safe.
4. Re-run `scratch_chunk_stats.py`-style numbers on the real data (the script is a throwaway; do not commit it) and record the new numbers here.

### Step 3 and later (do not start before Step 2 is merged)

- Chunk store in SQLite (single source of truth), with per-document incremental updates by checksum.
- Indexes: ChromaDB and BM25, with the department filter applied before top-k.
- Retrieval: hybrid search, reranker, "not found" threshold.
- Generation: Groq client behind `LLMClient`, citation ID validation.
- API: FastAPI, signed-token auth, generic "not found", query logging (truncate and sanitize logged role values).
- UI: Streamlit. Evaluation set in `eval/`. Docker.

### Small cleanup items

- Delete merged remote branches.
- Add a short note to the design document about `document_id`/`chunk_id` format and the chunk-size decisions once Step 2 is done.

## 7. Working method: TDD, one small piece at a time

For every new function:

1. Give him the goal, the signature and the test cases (inputs and expected outputs), including edge cases and failure cases.
2. He writes the tests, runs `pytest`, and sees RED.
3. He writes the minimum code, runs `pytest`, and sees GREEN.
4. You review. Prove tests catch bugs with a quick mutation check (break the code on purpose, see a test fail, restore).
5. Then branch, commit, push, PR, merge, sync `main`.

## 8. Engineering conventions

- Windows, PowerShell, `.venv` at the project root. Give PowerShell commands, never bash-only commands. The tests must also pass on Linux.
- Layout: `src/api`, `src/ingestion`, `src/retrieval`, `src/generation`, `src/core`, `tests/`, `eval/`, `docs/`.
- Every access-control rule needs a test.
- One Git branch per piece of work (`feat/...`, `fix/...`, `docs/...`, `test/...`). Conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `chore:`. Merge through a pull request into `main`. Tag each finished phase.
- **No `Co-Authored-By` or session-link trailer lines in commit messages or PR descriptions.** The owner explicitly does not want them.
- Do NOT run `git commit` or `git push` unless he asks. Show `git status` and `git diff --stat` instead.
- Never commit `.env`, `data/`, `logs/`, `.venv/`, `chroma_db/`, `*.db`, API keys, or secrets.
- Keep Markdown tables with every row on one line, and a blank line before and after each heading.
- Do not rewrite merged Git history. Seven older commits carry session-link trailers; the owner chose to leave them.

## 9. Starting a session

When he opens a session, do this first and report briefly:

1. `git branch --show-current`, `git status`, `git log --oneline -5`.
2. Activate `.venv` and run `pytest -q`. It should show 89 passed on `main`.
3. Read `docs/01-requirements.md`, `docs/02-design.md` and `docs/data-sources.md` if you have not read them this session.
4. Tell him which step from section 6 is next, and give the first small step.

If anything contradicts this file (for example the test count differs), tell him; do not guess which one is right.
