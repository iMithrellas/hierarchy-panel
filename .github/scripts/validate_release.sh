#!/usr/bin/env bash
set -euo pipefail

# Run from the repository root after a GRAFANA_PLUGIN_RELEASE=true build.
PLUGIN_ID=$(node -p "require('./dist/plugin.json').id")
PLUGIN_VERSION=$(node -p "require('./dist/plugin.json').info.version")
PACKAGE_VERSION=$(node -p "require('./package.json').version")
if [ "$PLUGIN_VERSION" != "$PACKAGE_VERSION" ]; then
  echo 'Expected a release build; run npm run validate:release.' >&2
  exit 1
fi

# Match package-plugin's top-level plugin directory, ZIP name and checksum.
# Use a fresh staging directory so a previous archive cannot leave stale entries.
mkdir -p release
STAGING=$(mktemp -d "$PWD/release/package.XXXXXX")
trap 'rm -rf "$STAGING"' EXIT
ARCHIVE="$PLUGIN_ID-$PLUGIN_VERSION.zip"
cp -R dist "$STAGING/$PLUGIN_ID"
(cd "$STAGING" && zip -q -r "$ARCHIVE" "$PLUGIN_ID")
cp "$STAGING/$ARCHIVE" "release/$ARCHIVE"
sha1sum "release/$ARCHIVE" | cut -f1 -d' ' > "release/$ARCHIVE.sha1"
python3 .github/scripts/verify_release_archive.py "release/$ARCHIVE" "$PLUGIN_ID" "v$PACKAGE_VERSION" false

# Source validation is essential: archive-only validation misses build tooling.
npx --yes @grafana/plugin-validator@0.49.5 -sourceCodeUri file://./ "release/$ARCHIVE"
