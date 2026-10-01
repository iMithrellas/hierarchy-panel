# Hierarchy Timeline

A datasource-agnostic Grafana panel for exploring **record hierarchies, observed
lifetimes and relationships** from compatible Grafana DataFrames. Plugin ID:
`imithrellas-hierarchy-panel`. Built and tested against
Grafana **13.0.1**, using public plugin APIs, React 18 and TypeScript. The repository's
development stack is isolated from other Grafana instances. Jira observations in
VictoriaLogs are an included example, not a required datasource or schema. This
panel requires structured observations matching the contract below; it does not
turn arbitrary unstructured data into a hierarchy or act as a planned-date Gantt.

## Features

- Parent-subtree focus or all-group browsing, including cross-group descendants.
- Expand/collapse and virtualized fixed-height rows. Only visible rows plus overscan are mounted.
- Search by key, summary, assignee, status, type, or discovered custom fields such as company, with an `All fields` default and a field selector. Group filters retain ancestor context.
- Creation-to-resolution bars for resolved records; creation-to-last-observation bars for open records.
- Descendant rollups on parent rows: child count, resolved child count, and stale child count.
- Colored relationship lines anchored to record bars, with explicit directed or undirected semantics and hover labels for relationship types.
- A `Hide arrows` / `Show arrows` control for decluttering the timeline without changing relationship data.
- Status-category or Grafana field colors, stale-observation markers, custom-field details, and per-row record URLs or Grafana data links.
- Configurable input fields and source identity, with Jira defaults for existing queries.
- Local zoom, pan and fit-to-records. Collapsing rows does not change the fitted time extent.
- Large-tree controls: expand through a selected depth, collapse resolved branches, and navigate search matches.
- CSV and JSON export of the complete current filtered tree, including collapsed descendants, rollups, and custom metadata.
- Missing parents remain visible as roots. Cyclic relationships are broken with a warning.
- Light/dark Grafana themes, keyboard-operable controls, and horizontal scrolling on narrow screens.

The timeline does **not** represent planned dates, status transitions, dependencies,
or state changes that happened after the last observation. Parent bars show the
parent record's own lifetime, not a synthetic roll-up of its children.
Relationship arrows are drawn when both endpoints are present and visible in the
selected hierarchy. Links to records outside the query or collapsed branches are
listed only from the selected record's details until those endpoints are visible.

## Run The Playground

Requirements: Node 22+, npm, Docker with Compose. Run these commands from the repository root:

```sh
npm ci
npm run build
docker compose --env-file /dev/null -p hierarchy-timeline-dev -f docker-compose.dev.yml up -d --wait
npm run seed
```

Use npm (`npm ci`) for installation and package scripts. The package override maps
Grafana UI's transitive Git-only `react-data-grid` dependency to registry release
`7.0.0-beta.61`, the current registry line compatible with the Grafana UI dependency.

The build uses Grafana/React as external runtime modules, not bundled copies of
these SDK dependencies. Do not remove the `react-data-grid` override unless the
Grafana SDK releases a registry-resolvable dependency.

Keep the explicit `yaml` 2 development dependency: it satisfies Vite's optional
peer used by Vitest and keeps lockfile generation compatible with CI's npm 10
and local npm 12. Otherwise npm 12 omits that peer while npm 10 requires it for
`npm ci` when the transitive YAML 1 dependency is present.

Open **Hierarchy Timeline - Development** at `http://127.0.0.1:3300/d/hierarchy-timeline-dev`, in
the **Operations** folder. Grafana is loopback-only on port 3300; VictoriaLogs is
loopback-only on 19428. These services have separate storage and never load the
repository `.env`, contact Jira, or connect to the existing Grafana instance.

The fixture contains 3,832 synthetic records. Enter `PM-100` for a small cross-project
tree, `PM-200` for maintenance work, or `PM-300` for 3,757 records. Clear Parent to
see all trees, including missing-parent examples. No real Jira data is seeded.

Anonymous viewing is enabled. For editing, the deliberately development-only
login is `hierarchy-timeline-dev` / `hierarchy-timeline-development-only`. **Do not expose this
stack through a public interface, proxy or tunnel.** See [development notes](https://github.com/iMithrellas/jira-panel/blob/main/dev/README.md)
for ports, fixture details, and stop/reset commands.

Development builds stamp `dist/plugin.json` with a bundle-content hash in
`info.version`, so changed code gets a new Grafana plugin cache key. After
rebuilding (including `npm run dev` watch compilations), restart the development
Grafana to pick up the new metadata, then reload the browser page. Grafana's
dashboard **Refresh** button only reruns queries; it does not reload plugin code.
See the [rebuild commands](https://github.com/iMithrellas/jira-panel/blob/main/dev/README.md#commands).
Build `dist/` before starting Compose, so Docker does not create it as root.

## Query Contract

Provide one or more observations for each record. The panel selects the newest
observation for each mapped key (`issue_key` by default) within a source namespace, so every observation
must be a complete current-state record rather than a partial update. How these
records are collected and delivered to Grafana is outside the scope of this plugin.

The panel accepts compatible flat table DataFrames from any datasource, or logs frames with a
per-row `labels` object or JSON string. Direct fields take precedence over fields
inside `labels`. The development dashboard uses VictoriaLogs as an example and
passes its native frames directly; no Extract fields transformation is required.
The following Jira-compatible names are defaults, not mandatory Jira fields; use **Field mappings** in panel options to
select different incoming names without rewriting the query.

| Field | Meaning |
| --- | --- |
| `issue_key` | Required record identity |
| `app`, `instance`, `environment` | Optional source namespace; retain through queries and transformations when used |
| `created_at` | Required ISO 8601 creation time, or numeric epoch milliseconds |
| `sync_ts` | Observation time; falls back to `_time` or Grafana's `Time` field when absent or null |
| `is_resolved` | Required boolean or string `"true"` / `"false"`; not inferred from status |
| `resolved_at` | Required valid timestamp if resolved; ignored if open/reopened |
| `parent_key` | Actual parent record key; absent or empty for roots |
| `project_key`, `summary`, `issue_type` | Group filtering and display metadata |
| `status`, `status_category` | Label and color (`new`, `indeterminate`, `done`) |
| `assignee`, `priority` | Search/detail metadata |
| `issue_links` | Optional normalized relationships: `target_key`, canonical `type`, current-side `display`, and `direction` |

At least one observation timestamp is required. Use numeric epoch milliseconds,
`YYYY-MM-DD` dates (UTC midnight), or ISO timestamps with seconds and an explicit
timezone (`Z`, `+00:00`, or Jira-style `+0000` offsets). Numeric strings and
timezone-free date-times are rejected. A supplied empty or invalid timestamp is
rejected rather than replaced by another time field. Dates must be representable and satisfy
`created_at <= end <= observation time`, where end is `resolved_at` for resolved
records and the observation time otherwise.

Identity, namespace and the listed display fields must be strings when supplied;
optional fields can be absent or null. `issue_links` accepts an array or
JSON-encoded array of links with nonempty string `target_key` and `type`,
`direction` equal to `inward`, `outward`, or `undirected`, and optional string `display`.
Absent, null or empty-string links mean no relationships. Malformed contract
fields or links exclude the row with a visible warning. Rows with valid identities,
namespaces and observation times are deduplicated before full validation, so a
malformed newest row does not silently restore stale record state. Equal
observation timestamps retain the first row received. Additional custom fields
remain available according to the [search-field rules](#custom-search-fields).
Expand **Validation details** in the warning area to see the query refId, frame,
one-based row number, record key when available, offending incoming field, and reason.
Samples are limited to 20 excluded rows; the total invalid-row count includes all
excluded rows. Diagnostics refer to the DataFrames after Grafana transformations.

A minimal table row needs no exporter metadata or source namespace:

```json
{
  "issue_key": "OPS-42",
  "created_at": "2026-09-01T10:00:00Z",
  "sync_ts": "2026-09-15T12:00:00Z",
  "is_resolved": false
}
```

Without namespace fields, all rows share one source. Supply them when combining
sources or tenants that might have identical record keys.

### Field And Source Mapping

**Field mappings** provides selectors for the key, parent, group (`project` mapping), summary, type,
status, status category, assignee, priority, creation time, observation time,
resolution time, resolution flag, and relationship array. Selectors list incoming
table fields and keys discovered inside `labels`; names can also be entered manually.
Names are case-sensitive and refer to incoming names, not Grafana display-name
overrides. A blank mapping restores its Jira default. Nested objects must be
flattened into columns or labels keys before mapping.

For example, these two generic table rows represent an open parent and a closed
child. They need no Jira fields, exporter, or integration:

```json
[
  {"id": "run-1", "group": "batch", "title": "Import run", "started_at": "2026-09-01T10:00:00Z", "observed_at": "2026-09-01T12:00:00Z", "closed": false, "record_url": "https://records.example/runs/run-1"},
  {"id": "step-1", "parent_id": "run-1", "group": "batch", "title": "Validate input", "started_at": "2026-09-01T10:05:00Z", "observed_at": "2026-09-01T12:00:00Z", "ended_at": "2026-09-01T10:15:00Z", "closed": true, "record_url": "https://records.example/steps/step-1"}
]
```

Use these panel options (or configure Grafana data links on `id` instead of
`issueUrlField`):

```json
{
  "fieldMappings": {
    "key": "id",
    "parent": "parent_id",
    "project": "group",
    "summary": "title",
    "created": "started_at",
    "observed": "observed_at",
    "resolved": "ended_at",
    "isResolved": "closed",
    "links": "relations"
  },
  "issueUrlField": "record_url"
}
```

Mappings change names, not value semantics: identities remain strings, timestamps
follow the timestamp contract, and the resolution flag remains explicit. The
default `sync_ts` mapping retains the `_time` / `Time` fallback. A custom observation
mapping such as `observed_at` is authoritative and does not fall back to another
timestamp when absent or invalid.

**Source identity fields** is an ordered, comma-separated list. Blank retains the
optional `app`, `instance`, and `environment` namespace. If configured, every listed
field must contain a nonempty string on every row; missing source identity excludes
the row instead of merging it with another site's records. Source values are kept
exactly as supplied. Deduplication, parents, and relationships use this same identity.

### Relationship Direction

Use `outward` for a relationship originating at the current record, `inward` for
its reverse-side representation, and `undirected` when neither endpoint is the
origin. Reciprocal representations of the same undirected type produce one line
without an arrowhead. Directed and undirected relationships are distinct.

```json
{"target_key": "OPS-43", "type": "relates to", "direction": "undirected"}
```

The panel does not infer direction or dependency semantics from a type name.
Existing `inward` / `outward` records continue to render as directed relationships.

### Example Observation Query

Example LogsQL for Jira observations stored in VictoriaLogs; replace the selector with labels
that identify your data:

```logsql
{app="jira-data", instance="example", environment="production"} kind:="issue_state"
| stats by (app, instance, environment, issue_key) row_max(_time) as row
| unpack_json from row
| fields _time, sync_ts, app, instance, environment, issue_key, project_key, summary, issue_type, parent_key, issue_links, created_at, resolved_at, is_resolved, status, status_category, priority, assignee
| sort by (issue_key)
| limit 10001
```

Use the VictoriaLogs **instant/logs** query type (`queryType: "instant"`), not a
time-series aggregation. Set the query and datasource line limits to at least
`maxIssues + 1`. The example pairs `maxLines: 10001` with panel `maxIssues: 10000`.
The extra row allows the panel to warn that a tree may be incomplete. A lower
datasource limit cannot be detected reliably by the panel. Development pins
datasource version **0.26.3**, verified to pass the 10,001-row limit through.

Include the parent and **every descendant group** in the query. Filtering to the
parent's group before fetching would discard cross-group children. Use the
panel's group filters to preserve ancestor context. For very large datasets,
scope the query to a complete set of relevant groups rather than silently
truncating. The panel caps displayed records at 50,000 even if configured higher.

The example query uses the time picker for **observations**, not creation dates;
your own query controls its time semantics. For observation queries choose a lookback
longer than the sync interval plus the duration of a full sync and any expected
outages. The development panel overrides this to 30 days; it then fits the full
lifetimes of the returned records. Local timeline zoom never changes the query.
Absolute Grafana time ranges disable relative panel overrides.

## Panel Options

| Option | Default | Purpose |
| --- | --- | --- |
| Parent record | Empty | Initial root key, supports dashboard variables; empty shows all trees |
| Jira base URL | Empty | Optional Jira integration: fallback `/browse/<key>` links; allows HTTP(S) and Jira context paths only |
| Record URL field | Empty | Complete HTTP(S) record URL from each row; supports multiple sites |
| Color by field | Empty | Use a flat field's Grafana display color; empty uses status categories |
| Field mappings | Jira-compatible field names | Map incoming fields to record semantics; `project` maps the group |
| Source identity fields | Empty | Empty uses optional `app`, `instance`, `environment`; configured fields are required |
| Initially expanded levels | 2 | Expand the root and its direct children on initial display |
| Stale after (hours) | 24 | Mark each record whose last observation is older than this threshold |
| Maximum records | 10,000 | Cap with a visible warning when an extra record is returned |
| Row height | 36px | Fixed row size used for virtualization |
| Record column width | 420px | Width of the hierarchy column; bounded to retain a timeline |
| Searchable fields | Empty | Comma-separated incoming field names; empty enables built-in and discovered fields |
| Additional detail and export fields | Empty | Custom-field allowlist for details and `custom_fields` exports; empty discovers all eligible fields |
| Collapse completed policy | Resolved parent or all descendants resolved | Choose the condition used by **Collapse completed** |

### Custom Search Fields

Additional fields returned by the query are retained from each record's latest
observation. Text, finite numbers, booleans, and non-empty arrays of those values
are automatically available in **Search in**. For example, a `company` column with
the value `Acme` adds **Company** to the selector and matches an **All fields**
search for `Acme`. Fields are discovered across the returned records, even when
some records lack them. Matching is case-insensitive substring search; arrays
match if any element matches. Nested objects and arrays containing objects or nulls
are excluded; flatten the desired values into named columns in your query.

The existing five fields retain their friendly names. Other fields, including
`project_key` and `priority`, are discovered automatically. Source namespace,
record kind, parent/link data, lifecycle timestamps and flags, status category,
known log-frame metadata (`labels`, `Line`, `Time`, `time`, `ts`, `id`), and names
beginning with `_` are excluded from search discovery.
Configured source fields and mapped structural fields are also excluded. Explicitly
mapped built-in search fields remain searchable even when their incoming name is
normally excluded, such as mapping the record key to `id`.

To restrict both the selector and **All fields**, set **Searchable fields** to
incoming names such as `issue_key, summary, company`. Names are case-sensitive;
use `issue_key` and `issue_type` rather than their display labels. Only eligible
fields are enabled; a list with no available names searches no fields. If a
selected field disappears after a refresh or settings change, the selector falls
back to **All fields**. Historical values are never searched.
When field mappings are configured, use those incoming names instead; for example,
use `id` when the key is mapped to `id`. Search uses raw values, not Grafana value
mapping labels or formatted numbers.

Retain custom fields through query projections and Grafana transformations. For
example, add `company` to the `| fields` list in the VictoriaLogs query above.

### Details, Formatting And Exports

The details drawer includes **Additional fields** from the latest observation.
Eligible custom values follow the scalar/array rules above; mapped contract fields
and source identity fields are already represented separately. **Additional detail
and export fields** restricts these custom values using incoming field names,
independently of the searchable-field allowlist.

For flat table fields, Grafana field overrides provide display names, units,
decimals and value mappings in details. Summary and status text also use the native
display processor. **Color by field** uses that field's Grafana color scheme,
thresholds or value-mapping color for the record bar, with the status-category color
as a fallback (`new`, `indeterminate`, `done`). Fields nested inside `labels` use plain display values; extract them
into flat fields to apply Grafana overrides.

Exports retain the backward-compatible canonical columns (`issue_key`, `project_key`,
`issue_type`, `is_resolved`, etc.) and add a `custom_fields` object with
the selected custom values. JSON preserves numbers, booleans and scalar arrays;
CSV stores `custom_fields` as a JSON-encoded cell, like relationship data. Nesting
prevents custom names such as `depth` or `source` from replacing calculated columns.
Exported values remain raw even when a display override changes their appearance.

### Record Navigation

Record details use the first configured link source in this order:

1. **Grafana data links on the mapped key field.** Link variables use the frame and
   row of the latest selected observation. For example, `${__data.fields.record_url}`
   can read a different URL for each site. Link titles, navigation targets and
   Grafana click handlers are preserved. Configure these links on a flat key field.
2. **Record URL field.** Read a complete URL directly from the row or its `labels`,
    such as `https://records.example/runs/run-1`.
3. **Jira base URL (optional integration).** Append `/browse/<encoded-key>` to the configured base URL,
   including any Jira context path. Dashboard variables are supported.

Links allow HTTP(S) without embedded credentials; Grafana data links also allow
root-relative URLs such as `/d/example`. A configured URL field or data-link source
with invalid or missing links produces a detail warning rather than falling back
to another site's base URL. Use per-row URLs or data links when combining Jira sites.

### Hierarchy Controls

Toolbar changes are local, not saved dashboard settings. Configure the initial
Parent in panel options to persist it, or use a dashboard variable there. The
**Depth** control expands all branches through that level. **Collapse completed**
uses the configured policy:

- **Resolved parent or all descendants resolved** (default): preserves the original
  behavior, including collapsing resolved parents with open descendants.
- **Resolved parent**: only the parent's own resolution flag determines collapse.
- **Parent and all descendants resolved**: retains branches containing any open work.

Rollups continue to show descendant counts regardless of the policy. Search match
arrows jump through matching records and open their details. **CSV** and **JSON**
export the complete current filtered tree, including rows hidden by collapse, with
`child_count`, `child_done_count` and `child_stale_count` fields. Manually
entering a key matches that key in all returned source namespaces. **Focus subtree**
in a record's details retains its source identity. Relationships never cross source
namespaces. A single panel has one Jira base URL; scope to a single Jira site when
using only that fallback, or configure per-row URLs or Grafana data links.
CSV prefixes potentially executable spreadsheet text with an apostrophe and stores
structured link cells as JSON; JSON export preserves the original text values.

## Validation

Release-helper tests require Python 3.9+.

```sh
npm run build
npm test
python3 -m unittest discover -s .github/scripts -v
npx playwright install chromium
npm run test:e2e
```

Browser tests require the running, seeded development stack. They exercise the
real Grafana plugin loader and VictoriaLogs query, hierarchy controls, rollups,
downloads, reopened records, multi-group ancestor context, thousands of virtualized
rows, mobile details, light/dark rendering and query-independent zoom. Images are written to
the ignored `test-results/` directory. Unit tests cover malformed rows, deduplication,
source isolation, missing/cyclic parents, a 10,000-level tree, rollups, exports,
time clipping and URL safety.
Additional coverage exercises field/source mapping, bounded validation diagnostics,
custom metadata, collapse policies, undirected links, and native Grafana formatting
and data links using the selected observation's row context.

The pinned Grafana 13.0.1 development SDK has upstream transitive dependency audit
advisories. It is externalized from the plugin bundle; the host supplies Grafana,
React and Emotion. Keep the host Grafana patched before production use and review
`npm audit` when updating the SDK. Do not apply force upgrades blindly against a
different host API version. No development test server is exposed by the build.

## Deployment And Limits

`npm run build` produces `dist/module.js`, `plugin.json`, the logo, documentation,
license and changelog.
Install the **contents of `dist/`** in a Grafana plugin directory named
`imithrellas-hierarchy-panel`. On a self-hosted development instance, allow only that unsigned
ID via `GF_PLUGINS_ALLOW_LOADING_UNSIGNED_PLUGINS=imithrellas-hierarchy-panel` and restart
Grafana. Production distribution requires your approved signing/install process;
this repository does not include a signing key or a signed release.

## Public Releases

Public release builds use the exact version in `package.json` rather than the
development cache suffix. The release workflow runs on tags matching `v*` and
creates a public GitHub prerelease with the plugin archive and SHA1 checksum,
even for the initial unsigned submission. Use the public asset URLs
`https://github.com/iMithrellas/jira-panel/releases/download/v<version>/imithrellas-hierarchy-panel-<version>.zip`
and the same URL with `.sha1` appended when submitting to Grafana. After Grafana
approves signing, configure the `GRAFANA_ACCESS_POLICY_TOKEN` repository secret
and rerun the workflow for the same tag. The run signs the plugin, requires the
archive to contain a PGP clear-signed `MANIFEST.txt` with a complete signature
block, and strictly verifies its public Grafana signature and signed file contents
before uploading. The signed ZIP and SHA1 replace the existing
assets while the GitHub release remains a prerelease and not-latest. Before
promotion, the workflow anonymously downloads both public assets and verifies
they byte-match the signed local build and checksum. Only then does a separate
step mark the release stable/latest. Unsigned runs remain prereleases and cannot
become stable/latest. Every run checks the archived plugin version against the
tag. Before packaging, an unsigned run checks the tag's existing GitHub release
using the workflow token and refuses to proceed if a published stable release
already exists; only a definitive 404 is treated as a first submission. The
workflow serializes runs for the same tag and generates a GitHub build provenance
attestation for each archive. The package action is referenced by
immutable commit; this avoids the build-plugin wrapper's nested mutable
`package-plugin@main` reference. The workflow runs an additional explicit
version-pinned Grafana validator check on the archive. The upstream packaging
action also runs its own validator via `@latest`. The policy token is passed as
a masked action input/environment value and is never printed by the workflow.
If asset replacement or public verification fails, the release remains a
prerelease and is not promoted. Keep it that way; rerun the workflow for the same
tag with the signing secret configured to replace and re-verify both assets. If
promotion fails after verification, the checked assets remain on the prerelease;
rerunning the signed workflow repeats verification and promotion. An unsigned
rerun is intentionally blocked once a stable release exists; restore/configure
the signing secret and use a signed rerun for any repair. Do not manually mark a
prerelease stable until its ZIP and SHA1 have been checked.

For a local release build:

```sh
GRAFANA_PLUGIN_RELEASE=true npm run build
```

The resulting `dist/` contains the files packaged by the release workflow. Do not
commit `dist/`, dependency directories, test results, or release archives.

Run `npm run validate:release` to build a release ZIP and SHA1 in `release/` and
validate both the archive and source with `@grafana/plugin-validator@0.49.5`.
CI runs this check before tags are created; the packaging action also validates
with the latest validator, followed by the pinned source-aware release check.
Unsigned local builds can pass validation with an unsigned-plugin warning; they
are not signed or eligible for automatic stable-release promotion.

The frontend uses the Webpack build configuration from
`@grafana/create-plugin@7.11.0`. Keep its generated Webpack, bundler and ESLint
files under `.config/` unchanged; project-specific metadata/cache hashing lives
in the root `webpack.config.ts`, following Grafana's
[configuration extension guidance](https://grafana.com/developers/plugin-tools/how-to-guides/extend-configurations#extend-the-webpack-config).
The `.config/.cprc.json` records the scaffold version, and `.swcrc` retains the
automatic React JSX runtime used by the panel.

The name and ID change does not grant community signing approval. Source and
release URLs remain under `https://github.com/iMithrellas/jira-panel`; the GitHub
repository has not been renamed.

### Migration From Jira Hierarchy

Install the new plugin in `imithrellas-hierarchy-panel` and update your
unsigned-plugin allowlist if using an unsigned development build. In saved
dashboard JSON, change each affected panel's `type` from
`imithrellas-jira-panel` to `imithrellas-hierarchy-panel`, then reload it.
Grafana does not automatically migrate plugin IDs. Existing dashboard options,
including `maxIssues`, `jiraBaseUrl`, `issueUrlField`, and `fieldMappings`, remain
valid; the input and export contracts are unchanged. Keep a dashboard backup and
only remove the old plugin installation after migrating all affected panels.

Add a Hierarchy Timeline panel using a compatible datasource and a query matching the contract above.
Any new dashboard for this project should live in **Operations**. The development
dashboard is not directly portable without changing its datasource UID, demo
source selector and Jira URL. Existing shared dashboards were not modified.

This is a latest-observation view, not an authoritative current-membership database.
Deleted, moved, permission-hidden or query-excluded records can remain visible until
they fall outside the query window. A partially failed sync can leave observation
times mixed across records. Freshness is shown per record; no completeness claim
is inferred from the newest timestamp. Missing or invalid rows and known cap
truncation are explicitly reported, but unseen data cannot be reconstructed.

The `core-traces-panel` and `grafana-gantt-panel` projects inspired the layout and
interactions. Their source was not copied. The panel does
not import Grafana-internal TraceView modules, encode records as spans, or require a
trace backend.
