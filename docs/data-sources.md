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
- The department is taken from the folder name.

## Reproduce

1. `git clone --depth 1 https://gitlab.com/gitlab-com/content-sites/handbook.git handbook-source`
2. `git -C handbook-source fetch --depth 1 origin 2c77a1f5b8c8a80cb7b5151ff11cfad84f98bfbb` then `git -C handbook-source checkout FETCH_HEAD` (needed only if the clone has moved on)
3. Copy the selected pages into `data/<department>/`.
