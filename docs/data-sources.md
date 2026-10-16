# Data Sources

## GitLab Handbook

- Source: https://gitlab.com/gitlab-com/content-sites/handbook
- Website: https://handbook.gitlab.com
- License: CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
- Pinned commit: 2c77a1f5b8c8a80cb7b5151ff11cfad84f98bfbb
- Commit date: Fri Oct 9 16:35:17 2026 -0700
- Downloaded on: 2026-10-11

## How the data is used

- Selected Markdown pages are copied unmodified into `data/<department>/<original handbook structure>`.
- `data/` is excluded from Git, so the files are not stored in this repository.
- The department comes from the mapping table below. The longest matching path wins, so a file-level row overrides its folder. Any path not listed is refused.

## Department Mapping

| Folder or path prefix                              | Department    |
| -------------------------------------------------- | ------------- |
| `people-group/general-onboarding`                  | `onboarding`  |
| `people-group/general-onboarding/tanewki-tips.md`  | `people`      |
| `people-group/general-onboarding/_index.md`        | `people`      |
| `people-group`                                     | `people`      |
| `people-policies`                                  | `people`      |
| `total-rewards`                                    | `people`      |
| `hiring`                                           | `people`      |
| `labor-and-employment-notices`                     | `people`      |
| `finance`                                          | `finance`     |
| `engineering`                                      | `engineering` |
| `eta/corporate-it/end-user-services/onboarding101` | `onboarding`  |
| `company`                                          | `general`     |
| `about`                                            | `general`     |
| `values`                                           | `general`     |
| `communication`                                    | `general`     |
| `leadership`                                       | `general`     |
| `tools-and-tips`                                   | `general`     |

> Pages inside `onboarding` that mention payroll, benefits, equity or compensation are mapped to `people` with a per-file row, so access follows content, not just folder.

## Dataset Selection

- Selected pages must contain at least 150 real words after front matter, link-only lines, and template lines are excluded.
- Targets are engineering 60, finance 35, people 50, onboarding 5, and general 40 (190 pages total).
- Selection uses deterministic round-robin across sibling folders at every depth. Direct files form their own group. Groups and files are sorted by source path; exhausted groups leave the rotation. This spreads the sample across topics while filling each department's quota. The final manifest is sorted by source path.
- The selected pages are recorded in `docs/data-manifest.csv` with `source_path`, `department`, and `sha256` columns.
- The SHA-256 value fingerprints the page after CRLF line endings are normalized to LF.
- Tests always validate the committed manifest's columns, unique sorted paths, department mappings, counts, and hash format. When `data/` exists, they also check every selected file's existence, hash, and 150-word minimum; only these local-file checks are skipped when `data/` is absent.

## Path rules

Paths must be relative and use forward slashes. Each segment permits only ASCII letters, digits, `.`, `_`, and `-`; empty segments, `.` and `..`, and segments ending in a dot or space are refused. Mapping is case-sensitive; excluded prefixes are checked case-insensitively.

## Excluded paths

These are refused even though their parent folder is mapped.

| Path prefix            | Reason                                    |
| ---------------------- | ----------------------------------------- |
| `finance/readmes`      | Personal pages about individual employees |
| `finance/jihu-support` | Software process content, not finance     |

## Reproduce

1. `git clone --depth 1 https://gitlab.com/gitlab-com/content-sites/handbook.git handbook-source`
2. `git -C handbook-source fetch --depth 1 origin 2c77a1f5b8c8a80cb7b5151ff11cfad84f98bfbb` then `git -C handbook-source checkout FETCH_HEAD` (needed only if the clone has moved on)
3. From the assistant project root, regenerate the manifest with `.\.venv\Scripts\python.exe -c "from pathlib import Path; from src.ingestion.manifest import build_manifest; build_manifest(Path('../handbook-source/content/handbook'), Path('docs/data-manifest.csv'))"`.
4. Copy each manifest page unmodified into `data/<department>/<source_path>`, then run `pytest -q` to verify the copied dataset.
