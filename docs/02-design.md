# Design Document: Enterprise RAG Assistant

**Author:** Abdul Samad | **Version:** 0.3 (draft) | **Depends on:** `01-requirements.md` v0.1

---

## 1. Design Goals

Derived from the requirements. Every design decision below serves one of these:

| Goal                                                     | Comes from           |
| -------------------------------------------------------- | -------------------- |
| Answers come only from documents the user's role may see | FR-05, NFR-03        |
| Every answer is traceable to a source                    | FR-04                |
| The system says "not found" instead of guessing          | FR-06                |
| Quality and safety can be measured repeatedly            | FR-08, FR-09, NFR-02 |
| Components can be replaced later (database, LLM)         | Maintainability      |

## 2. Architecture Overview

```
                    ┌────────────────────────────┐
                    │  Streamlit UI (thin client)│
                    │  login form + chat box     │
                    └─────────────┬──────────────┘
                                  │  HTTPS + Bearer token
                    ┌─────────────▼──────────────┐
                    │        FastAPI backend     │
                    │  auth middleware (role     │
                    │  comes from the token only)│
                    └─────────────┬──────────────┘
                                  │
        ┌─────────────────────────▼─────────────────────────┐
        │                    RAG pipeline                   │
        │  access filter → hybrid search → rerank →         │
        │  threshold check → LLM → citations                │
        └───────┬──────────────────┬──────────────┬─────────┘
                │                  │              │
        ┌───────▼──────┐   ┌───────▼─────┐  ┌─────▼──────┐
        │ VectorStore  │   │ Keyword     │  │ LLM client │
        │ (ChromaDB)   │   │ index (BM25)│  │ (Groq)     │
        └───────▲──────┘   └──────▲──────┘  └────────────┘
                │                 │
        ┌───────┴─────────────────┴──────┐        ┌──────────────┐
        │ Chunk store (single source of  │        │ Query log    │
        │ truth: all chunks + metadata)  │        │ (async)      │
        └───────▲────────────────────────┘        └──────────────┘
                │
        Ingestion CLI: documents → parse → chunk → tag → embed
```

## 3. Data Flows

### 3.1 Ingestion (run from the command line)

```
Documents (.md / .pdf)
   ↓ parse text
   ↓ split into chunks at headings (with size limit)
   ↓ attach metadata (department, title, section/page, checksum)
   ↓ save every chunk to the CHUNK STORE        ← single source of truth
   ↓ build vector index (ChromaDB) from the chunk store
   ↓ build keyword index (BM25) from the same chunk store
```

Both indexes are **derived** from the chunk store, never edited separately. Updates are **per document, not a full rebuild**:

1. Compare each file's checksum with the chunk store. Only new or changed files are re-parsed and re-embedded.
2. For a changed or deleted document, delete its chunks by `document_id` from the chunk store and the vector index, then add the new chunks.
3. The keyword index (BM25) cannot be edited in place, so it is rebuilt from the chunk store after each ingestion run. This takes seconds because it needs no embeddings. The expensive step (embedding) is always incremental.

At startup the system compares chunk counts and checksums across the three places and **refuses to start** if they disagree. Ingestion runs offline, never while the API is serving.

### 3.2 Question answering

```
1. Request arrives with a token → backend reads the ROLE from the token
2. Role → allowed departments (from one config table)
3. Vector search  (top 20) ┐  both restricted to allowed departments
   Keyword search (top 20) ┘  BEFORE ranking, not after (see 4.7)
4. Merge the two lists (reciprocal rank fusion) → keep the best 10
5. Reranker re-scores those 10 → keep the top 5
6. Is the best score above the threshold? (reranker score; best vector
   similarity if the reranker is switched off, see 4.9)
      NO  → return "not found" (the LLM is never called)
      YES → continue
7. LLM gets: instructions + the 5 chunks (each with an ID) + the question.
   It may also reply "insufficient context" (second safety net, see 4.3)
8. LLM returns the answer + the chunk IDs it used
9. Citation check (see 4.8): invalid IDs removed; if no valid citation
   remains → "not found"
10. Log asynchronously (after the response is sent)
```

## 4. Key Design Decisions

### 4.1 Access control happens before the LLM

The department filter is applied **inside both searches**. A chunk the role may not see is never retrieved, so it can never reach the LLM or the user. We do not rely on prompt instructions like "do not reveal Finance data", because prompts can be bypassed.

### 4.2 The role comes from the server, not the browser

The UI sends a login request; the backend checks credentials and returns a signed token containing the role. Every later request carries that token. The UI never sends "I am HR" as a plain value, because anyone could change it. The UI contains **no** permission logic. Tokens expire after 30 minutes, which limits how long a user whose access was removed could keep using the system.

### 4.3 "Not found" is decided in two layers

Vector search always returns *something*, even for an unrelated question. So "zero results" almost never happens. We use two layers instead:

1. **Reranker threshold (permissive).** If the best reranker score is below the threshold, we stop before calling the LLM. The threshold is set low on purpose, so it only catches clearly unrelated questions.
2. **LLM safety net.** The prompt tells the LLM to reply "insufficient context" when the chunks do not contain the answer. This catches the borderline cases without us tuning a harsh number.

The threshold is calibrated on the test set, and we report **both** error rates: false refusals (answerable question refused) and false answers (unanswerable question answered). We do not assume one number fits every question length; the evaluation will show whether it does. If long questions are refused too often, we adjust then, with data.

### 4.4 Blocked and missing look identical

If a user asks about a document their role cannot see, the reply is the same "not found" message as for a document that does not exist. A different message would reveal that the restricted document exists.

### 4.5 Swappable components

The database and the LLM sit behind small interfaces:

```
VectorStore:  add_chunks(...)  search(query, departments, k)  delete_document(id)
LLMClient:    generate(prompt) → text
```

ChromaDB and Groq are the first implementations. Moving to `pgvector` or Qdrant, or from Groq to Claude, means writing one new class and changing one config line.

### 4.6 Retrieved text is data, not instructions

Chunks are placed in the prompt inside a clearly marked "documents" section, and the system instruction says to treat them as reference material only. After generation, the system checks that every citation points to a chunk that was actually retrieved (FR-10).

### 4.7 Keyword search filters BEFORE ranking

A keyword index scores every chunk. If we took the global top 20 and then removed chunks the user may not see, an Engineer asking a broad question could lose all 20 slots to Finance chunks and get nothing back. So the order is fixed:

```
score all chunks → hide chunks outside the allowed departments → take top 20
```

At our size (a few thousand chunks) this is fast. The vector search does the same through ChromaDB's metadata filter. This ordering is covered by a dedicated test (an Engineer asking a Finance-flavoured question must still get Engineering results, and never Finance ones).

### 4.8 What happens when a citation is invalid

The LLM returns chunk IDs, not free text. The system checks each ID against the chunks that were actually given to the LLM:

```
All IDs valid            → return answer + citations
Some IDs invalid         → remove those IDs, keep the valid ones, log the event
No valid ID remains      → return "not found" (we do not show an answer with no source)
```

We do not re-prompt the LLM, to keep cost and latency predictable. Whether the remaining answer is really supported by the chunks is measured offline by the faithfulness score in the evaluation (NFR-02).

### 4.9 Pipeline stages are configurable

Every stage takes a list of scored chunks and returns a list of scored chunks. A config file chooses:

| Setting               | Options                                   |
| --------------------- | ----------------------------------------- |
| Retrieval mode        | vector only, or hybrid (vector + keyword) |
| Reranker              | on or off                                 |
| Candidate counts      | how many chunks each stage keeps          |
| "Not found" threshold | one value**per configuration**      |

The "not found" check must use a score that means something on its own: the reranker score when the reranker is on, otherwise the best vector similarity. (Fused rank scores from RRF only order the candidates, so they are never used for this check.) Because the score type changes with the configuration, each configuration has its own calibrated threshold, stored next to it in the config.

This also gives us the evaluation experiments for free: vector-only, then hybrid, then hybrid plus reranker, by changing config and nothing else. The fusion method is a swappable function. The default is RRF, because keyword and vector scores are on different scales, and the reranker re-scores the candidates afterwards. We try other fusion methods only if the evaluation shows missed answers at that step.

Per-client configuration files are possible later. Multi-tenant hosting is not part of v1.

### 4.10 Logging and privacy

By default the query log stores only: role, chunk IDs, scores, latency, and token count. The question and answer text are stored only when content logging is switched on. It is on while developing and off by default for any client deployment. Log files are excluded from Git, and a retention period is documented in the README. Automatic masking of personal data is a v2 item (section 12).

## 5. Data Model

Every chunk carries:

| Field          | Example                     | Purpose                               |
| -------------- | --------------------------- | ------------------------------------- |
| chunk_id       | `time-off-004`            | Unique ID, used in logs and citations |
| document_id    | `time-off`                | Which document it came from           |
| title          | `Time Off Policy`         | Shown in citations                    |
| department     | `People`                  | Used by the access filter             |
| section / page | `Requesting leave` / 4    | Shown in citations                    |
| source_path    | `data/people/time-off.md` | Traceability                          |
| checksum       | `a8f5f1...`               | Detects changed documents             |
| text           | `...`                     | The content itself                    |

**Access rule lives in one place:** a config table maps role → allowed departments (from Requirements section 3). Chunks store only their department. We deliberately do not store an "allowed roles" list on every chunk, because then there would be two places to keep consistent.

## 6. API Design

| Endpoint             | Purpose                                                    | Auth           |
| -------------------- | ---------------------------------------------------------- | -------------- |
| `POST /auth/login` | Check credentials, return a token                          | None           |
| `POST /ask`        | Body:`{question}`. Returns answer, citations, found flag | Token required |
| `GET /health`      | Service status and index consistency check                 | None           |

Ingestion and evaluation are command-line scripts, not API endpoints, so there is no remote way to change documents.

## 7. Evaluation and Logging Design

- **Query log** (FR-08): role, retrieved chunk IDs and scores, final chunk IDs, latency, token count. Question and answer text are included only when content logging is on (see 4.10). Written asynchronously so it does not slow the answer.
- **Evaluation runner** (FR-09): reads `eval/questions.csv`, calls the system as each test role, and scores the results. Because LLM-based scoring makes many calls, the runner limits how many run at once and retries with increasing delays when the provider returns a rate-limit error. Results are cached so a crashed run can resume.
- **Baseline comparison:** we measure vector-only search first, then hybrid, then hybrid plus reranker. These before/after numbers are the main portfolio evidence.

## 8. Decision Log (technology choices and known risks)

| Component      | Choice                   | Reason                                         | Known risk                                                                                       | Mitigation                                                                                                                                                              |
| -------------- | ------------------------ | ---------------------------------------------- | ------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Vector DB      | ChromaDB                 | Already known; supports metadata filters       | Embedded mode is weak under many concurrent users and can lock if several worker processes write | v1 runs a single API worker; ingestion runs offline, never while serving; engine sits behind the`VectorStore` interface; migration path to pgvector/Qdrant documented |
| Keyword search | BM25                     | Catches exact terms that meaning search misses | Two indexes can fall out of sync, and a stale keyword index could leak restricted text           | Single chunk store, both indexes rebuilt from it, department filter applied in both, startup consistency check                                                          |
| Reranker       | Small cross-encoder, CPU | Measurable quality gain                        | Adds roughly 150-400 ms per query (estimate, to be measured)                                     | Candidate cap of 10 (configurable); measured against the 8-second target; skip step if it exceeds a timeout                                                             |
| LLM            | Groq, free tier          | Free, fast, already used                       | Rate limits can crash evaluation runs                                                            | Concurrency cap, retry with backoff, result caching; LLM behind an interface                                                                                            |
| UI             | Streamlit                | Fast to build                                  | Re-runs the script on every action; session state is fragile                                     | UI holds only the token; all permission checks are in the backend                                                                                                       |
| Embeddings     | Local bge-small          | Free; no data leaves the machine               | Lower quality than large hosted models                                                           | Measured in evaluation; replaceable                                                                                                                                     |

## 9. Planned Project Structure

```
src/
  api/          FastAPI app, auth, routes
  ingestion/    parsing, chunking, tagging, index building
  retrieval/    vector store interface, BM25, fusion, reranker
  generation/   LLM interface, prompt building, citation check
  core/         config (role→department table), logging, models
tests/
eval/           questions.csv, runner, results
docs/
```

## 10. Requirements Coverage

| Requirement   | Where it is addressed               |
| ------------- | ----------------------------------- |
| FR-01, FR-02  | 3.1 Ingestion, section 5            |
| FR-03, FR-04  | 3.2 steps 7-8                       |
| FR-05, NFR-03 | 4.1, 4.2                            |
| FR-06         | 3.2 step 6, 4.3, 4.4                |
| FR-07         | Section 6                           |
| FR-08, FR-09  | Section 7                           |
| FR-10         | 4.6                                 |
| NFR-01        | Reranker cap and timeout, section 8 |
| NFR-04        | Token count in the log              |
| NFR-06        | Docker (Phase 4)                    |

## 11. Changes Needed in the Requirements Document

- Section 2 (out of scope): replace "simple role selector or basic login" with **basic login with a signed token**, since 4.2 requires it.
- Add **FR-11:** The system shall authenticate users and determine their role from a signed token.
- Add **FR-12:** The system shall give the same "not found" reply for restricted and non-existent documents.
- Add **FR-13:** The system shall verify that every citation refers to a chunk supplied to the LLM, remove invalid citations, and return "not found" if none remain.
- Change **FR-08:** query logging shall store content (question and answer text) only when content logging is switched on; by default it stores role, chunk IDs, scores, latency, and token count.

## 12. Known Limitations and Version 2 Roadmap

These are real enterprise needs that this version deliberately does not build. Each is documented so a client conversation can address it honestly.

| Limitation in v1                                                                                | Why it is acceptable now                                                 | Version 2 direction                                                                  |
| ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| Access is by department only (no per-project or per-person grants)                              | Matches the 4 simulated roles; keeps the access rule in one table        | Replace`department` with a list of access groups on each chunk                     |
| Revoked users keep access until their token expires (30 min)                                    | Short expiry limits the window; no real identity system exists in a demo | Check entitlements against the company identity system (SSO/AD) on every request     |
| Documents are updated by an offline ingestion script, and the service is restarted to load them | Document set is static for the demo                                      | Background ingestion worker with a job queue, and an incremental update path         |
| Single API worker                                                                               | Avoids embedded-database write locks                                     | Move to pgvector or Qdrant, then scale workers                                       |
| No re-check of answer grounding at request time                                                 | Faithfulness is measured offline                                         | Optional second-pass verification for high-risk clients                              |
| No automatic masking of personal data in logs                                                   | Demo data is public; content logging is off by default for clients       | Redaction step before logs are written, plus encryption and a retention schedule     |
| One configuration for the whole deployment                                                      | Enough to run the evaluation experiments                                 | Per-client configuration and a pipeline engine that composes stages from that config |
