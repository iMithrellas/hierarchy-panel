# Changelog

## [Unreleased]

### Changed

- Rename the plugin to Hierarchy Timeline and describe datasource-agnostic record hierarchies, observed lifetimes, and relationships from compatible Grafana DataFrames.
- Use record and group terminology in public controls, details, navigation, and documentation; keep Jira-compatible input defaults and serialized option/export keys.
- Rename the isolated development project, fixture source, dashboard, and unsigned-plugin allowlist; refresh screenshots from the real playground.

### Breaking

- Plugin ID/package name is now `imithrellas-hierarchy-panel`. Saved dashboard panel `type` values must change from `imithrellas-jira-panel`; installation directories and unsigned-plugin allowlists must use the new ID. Existing dashboard options remain valid. The source repository remains `https://github.com/iMithrellas/jira-panel`; this rename does not imply signing approval.

### Added

- Configurable incoming field mappings and source-identity fields with Jira defaults.
- Grafana field formatting, bar colors, key-field data links, and per-row record URLs.
- Custom scalar metadata in record details and CSV/JSON exports.
- Explicit completed-branch collapse policies and undirected relationship support.
- Bounded validation diagnostics identifying the query, frame, row, field, and reason.

### Fixed

- Stable root ordering and unique rows, matches, and exports for overlapping root selections.
- Faster numeric sorting for large, unsorted query results.
- Preserve scrolling and valid search navigation across query refreshes.
- Keep short panels contained and manage keyboard focus when record details open or dismiss.
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
