# Data Sources

## GitLab Handbook

- Source: https://gitlab.com/gitlab-com/content-sites/handbook
- Website: https://handbook.gitlab.com
- License: CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
- Pinned commit: 2c77a1f5b8c8a80cb7b5151ff11cfad84f98bfbb
- Commit date: Fri Oct 9 16:35:17 2026 -0700
- Downloaded on: 2026-10-11

## How the data is used

- Selected Markdown pages are copied unmodified into `data/<department>/`.
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
- The selected pages are recorded in `docs/data-manifest.csv` with `source_path`, `department`, and `sha256` columns.
- The SHA-256 value fingerprints the page after CRLF line endings are normalized to LF.

## Excluded paths

These are refused even though their parent folder is mapped.

| Path prefix            | Reason                                    |
| ---------------------- | ----------------------------------------- |
| `finance/readmes`      | Personal pages about individual employees |
| `finance/jihu-support` | Software process content, not finance     |

## Reproduce

1. `git clone --depth 1 https://gitlab.com/gitlab-com/content-sites/handbook.git handbook-source`
2. `git -C handbook-source fetch --depth 1 origin 2c77a1f5b8c8a80cb7b5151ff11cfad84f98bfbb` then `git -C handbook-source checkout FETCH_HEAD` (needed only if the clone has moved on)
3. Copy the selected pages into `data/<department>/`.
