# Changelog

## [Unreleased]

### Added

- Configurable incoming field mappings and source-identity fields with Jira defaults.
- Grafana field formatting, bar colors, key-field data links, and per-row ticket URLs.
- Custom scalar metadata in ticket details and CSV/JSON exports.
- Explicit completed-branch collapse policies and undirected relationship support.
- Bounded validation diagnostics identifying the query, frame, row, field, and reason.

### Fixed

- Stable root ordering and unique rows, matches, and exports for overlapping root selections.
- Faster numeric sorting for large, unsorted query results.
- Preserve scrolling and valid search navigation across query refreshes.
- Keep short panels contained and manage keyboard focus when ticket details open or dismiss.
- Show datasource errors without top-level messages instead of an empty explanation.
- Accept Jira timestamps with compact timezone offsets.
- Install the signing tool and require verified public signatures before release uploads.
- Serialize same-tag releases, validate archive paths and identities, and run release regressions in CI.
- Patch vulnerable `brace-expansion` and `fast-uri` transitive dependencies.
- Keep clean installs compatible with Node 22's npm 10 and newer npm versions.

## [0.1.0] - 2026-09-17

### Added

- Virtualized Jira hierarchy and observed-lifetime timeline panel.
- Parent-tree navigation, filtering, relationship arrows, rollups, exports, and Jira links.
- Dynamic search across built-in and scalar custom fields returned by the datasource.
- VictoriaLogs-backed development fixture with synthetic data and browser coverage.
