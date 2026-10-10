# Requirements Document: Enterprise RAG Assistant

**Author:** Abdul Samad | **Version:** 0.1 (draft) | **Status:** Requirements drafted with AI assistance; to be reviewed against course material (Software Requirements Engineering)

---

## 1. Problem Statement

Employees in large organizations keep policies, procedures, and team information in hundreds of separate documents. Finding a correct answer is slow, people often read outdated or wrong pages, and it is unclear which source is authoritative. Some documents are also sensitive and must only be visible to certain roles. Today, employees either search manually or interrupt colleagues, which wastes time and spreads inconsistent answers.

This project builds an assistant that answers employee questions in plain language, **only from approved company documents**, shows **where each answer came from**, and **respects who is allowed to see what**.

## 2. Scope

**In scope**

- Ingest company documents (Markdown and text-based PDF) from a local data folder
- Answer natural-language questions using only those documents
- Show citations (document and section/page) with every answer
- Role-based access: each user role sees answers only from its allowed departments
- Say "not found" instead of guessing when the documents do not contain the answer
- A REST API and a simple chat interface
- A repeatable evaluation of answer quality and access-control safety
- A deployed live demo

**Out of scope (v1)**

- Voice input/output, multi-language support, mobile app
- Fine-tuning or training models
- Editing or creating documents through the assistant
- Real-time sync with live company systems
- Enterprise login (SSO); v1 uses a simple role selector or basic login
- Multi-company (multi-tenant) support

## 3. User Roles

The demo company is "Acme Corp"; its documents come from the public GitLab Handbook (attribution in README). The role-to-department split below is a **simulated access layer** created for this project; the handbook itself is public.

| Role     | Can access                       | Cannot access                             |
| -------- | -------------------------------- | ----------------------------------------- |
| New Hire | Onboarding, General company info | People/HR internals, Finance, Engineering |
| HR       | People/HR, Onboarding, General   | Finance, Engineering                      |
| Finance  | Finance, Onboarding, General     | People/HR, Engineering                    |
| Engineer | Engineering, Onboarding, General | People/HR, Finance                        |

## 4. Functional Requirements

| ID | Requirement |
| --- | --- |
| FR-01 | The system shall ingest Markdown and text-based PDF files from a configured data folder. |
| FR-02 | The system shall tag every document with a department and source metadata at ingestion. |
| FR-03 | The system shall answer a natural-language question using only content retrieved from the documents. |
| FR-04 | The system shall include at least one citation (document title and section or page) in every answer. |
| FR-05 | The system shall retrieve only from documents the asking user's role is permitted to access. |
| FR-06 | The system shall reply that the answer was not found when retrieved evidence is insufficient, instead of guessing. |
| FR-07 | The system shall expose a REST API for asking questions and a simple chat interface. |
| FR-08 | The system shall log each query with role, retrieved chunk IDs, scores, latency, and token count. Question and answer text shall be stored only when content logging is switched on. |
| FR-09 | The system shall provide an evaluation script that runs the test question set and reports scores. |
| FR-10 | The system shall not follow instructions inside a user question or document that attempt to override access rules or system behavior. |
| FR-11 | The system shall authenticate users and determine their role from a signed token. |
| FR-12 | The system shall give the same "not found" reply for restricted and non-existent documents. |
| FR-13 | The system shall verify that every citation refers to a chunk supplied to the LLM, remove invalid citations, and return "not found" if none remain. |## 5. Non-Functional Requirements

Targets are **initial and provisional**. They will be revised after the first baseline measurement.

| ID     | Requirement      | Target                                                                                                 |
| ------ | ---------------- | ------------------------------------------------------------------------------------------------------ |
| NFR-01 | Response time    | 95% of answers within 8 seconds                                                                        |
| NFR-02 | Answer quality   | Faithfulness (answer supported by sources) of at least 0.85; correct on at least 75% of test questions |
| NFR-03 | Access control   | 0 leaks across all access-control test questions                                                       |
| NFR-04 | Cost             | Average LLM cost of at most USD 0.02 per question                                                      |
| NFR-05 | Supported files  | Markdown, text-based PDF (scanned PDFs are a stretch goal)                                             |
| NFR-06 | Reproducibility  | Setup from README in under 30 minutes using Docker                                                     |
| NFR-07 | Security hygiene | No API keys or secrets committed to the repository                                                     |

## 6. Test Questions (acceptance set)

Stored in `eval/questions.csv`. Target: 30 questions with columns `id, role, question, expected_answer, source_doc, should_refuse`.

| Category                     | Count | Purpose                                    |
| ---------------------------- | ----- | ------------------------------------------ |
| Simple factual               | 12    | Basic retrieval and answer correctness     |
| Multi-section or table       | 6     | Retrieval across several chunks            |
| Access control (must refuse) | 6     | Proves role restrictions (NFR-03)          |
| Not in documents             | 6     | Proves the system says "not found" (FR-06) |

Questions and expected answers are written **from real handbook pages**, after the data is downloaded and a version is pinned.

## 7. Assumptions and Open Items

- No real client was interviewed; requirements are inferred from typical enterprise document-search problems. A real stakeholder interview is planned later for the case study.
- Role-to-department mapping is simulated.
- NFR targets are starting guesses, to be tuned after the first evaluation run.
- Handbook version (date or commit) to be pinned at download time.

## 8. Traceability (requirement to how it will be verified)

| Requirement    | Verified by                              |
| -------------- | ---------------------------------------- |
| FR-03, FR-04   | Factual and multi-section test questions |
| FR-05, NFR-03  | Access-control test questions            |
| FR-06          | Not-in-documents test questions          |
| FR-10          | Prompt-injection test cases              |
| NFR-01, NFR-04 | Query logs (FR-08)                       |
| NFR-02         | Evaluation script (FR-09)                |
