#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_DRIVE_ROOT="/Users/oliviercloutier/Library/CloudStorage/GoogleDrive-oliviier.cloutier@gmail.com/Mon disque/Cockpit"
DRIVE_ROOT="$DEFAULT_DRIVE_ROOT"
STAMP="${COCKPIT_ARCHIVE_STAMP:-$(date +%F)}"
PRUNE=false

usage() {
  cat <<EOF
Usage: $0 [--repo-root PATH] [--drive-root PATH] [--stamp YYYY-MM-DD] [--prune]

Copies historical Cockpit archives to Google Drive, verifies the copy, writes a
manifest on Drive, and optionally prunes local sources after verification.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      REPO_ROOT="$2"
      shift 2
      ;;
    --drive-root)
      DRIVE_ROOT="$2"
      shift 2
      ;;
    --stamp)
      STAMP="$2"
      shift 2
      ;;
    --prune)
      PRUNE=true
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

ARCHIVE_ROOT="$DRIVE_ROOT/archive/repo-cleanup-$STAMP"
mkdir -p "$ARCHIVE_ROOT"

BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
SHA="$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
GENERATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
MANIFEST_TSV="$(mktemp)"
trap 'rm -f "$MANIFEST_TSV"' EXIT
printf 'label\tsource\tdestination\tsize_kb\tverified\tpruned\n' > "$MANIFEST_TSV"

size_kb() {
  du -sk "$1" 2>/dev/null | awk '{print $1}'
}

record_manifest() {
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "$5" "$6" >> "$MANIFEST_TSV"
}

copy_dir() {
  local label="$1"
  local rel="$2"
  local src="$REPO_ROOT/$rel"
  local dest="$ARCHIVE_ROOT/$label/$rel"
  local size

  [[ -d "$src" ]] || return 0
  mkdir -p "$(dirname "$dest")"
  rsync -a "$src/" "$dest/"
  diff -qr -x '.DS_Store' -x 'Icon?' "$src" "$dest" >/dev/null
  size="$(size_kb "$src")"
  if [[ "$PRUNE" == true ]]; then
    rm -rf "$src"
  fi
  record_manifest "$label" "$src" "$dest" "$size" "yes" "$PRUNE"
}

copy_file() {
  local label="$1"
  local rel="$2"
  local src="$REPO_ROOT/$rel"
  local dest="$ARCHIVE_ROOT/$label/$rel"
  local size

  [[ -f "$src" ]] || return 0
  mkdir -p "$(dirname "$dest")"
  cp -p "$src" "$dest"
  cmp -s "$src" "$dest"
  size="$(size_kb "$src")"
  if [[ "$PRUNE" == true ]]; then
    rm -f "$src"
  fi
  record_manifest "$label" "$src" "$dest" "$size" "yes" "$PRUNE"
}

copy_run_history() {
  local label="repo-runs-history"
  local runs_root="$REPO_ROOT/control/projects/cockpit/runs"
  [[ -d "$runs_root" ]] || return 0

  while IFS= read -r file; do
    local rel="${file#${REPO_ROOT}/}"
    copy_file "$label" "$rel"
  done < <(
    find "$runs_root" -maxdepth 1 -type f \( -name '*.md' -o -name 'WAVE*.ndjson' -o -name 'queue_recovery*.ndjson' \) | sort
  )
}

copy_dir "repo-docs-swarm" "docs/swarm_results"
copy_dir "repo-docs-reports" "docs/reports"
copy_dir "repo-control-archive" "control/projects/_archive"
copy_dir "repo-local-archive" "control/_archive_local"
copy_run_history
copy_file "repo-runtime-noise" "control/projects/cockpit/agents/registry.json"
copy_file "repo-runtime-noise" "control/projects/cockpit/runs/runtime.db"

MANIFEST_JSON="$ARCHIVE_ROOT/archive_manifest.json"
MANIFEST_MD="$ARCHIVE_ROOT/archive_manifest.md"
python3 - <<'PY' "$MANIFEST_TSV" "$MANIFEST_JSON" "$MANIFEST_MD" "$BRANCH" "$SHA" "$GENERATED_AT" "$ARCHIVE_ROOT"
from __future__ import annotations
import csv
import json
import sys
from pathlib import Path

tsv_path = Path(sys.argv[1])
json_path = Path(sys.argv[2])
md_path = Path(sys.argv[3])
branch = sys.argv[4]
sha = sys.argv[5]
generated_at = sys.argv[6]
archive_root = sys.argv[7]
rows = []
with tsv_path.open() as fh:
    reader = csv.DictReader(fh, delimiter='\t')
    for row in reader:
        rows.append(row)
json_path.write_text(json.dumps({
    'generated_at_utc': generated_at,
    'branch': branch,
    'commit': sha,
    'archive_root': archive_root,
    'entries': rows,
}, indent=2) + '\n')
lines = [
    '# Cockpit Archive Manifest',
    '',
    f'- generated_at_utc: `{generated_at}`',
    f'- branch: `{branch}`',
    f'- commit: `{sha}`',
    f'- archive_root: `{archive_root}`',
    '',
    '| label | source | destination | size_kb | verified | pruned |',
    '|---|---|---:|---:|---|---|',
]
for row in rows:
    lines.append(
        f"| `{row['label']}` | `{row['source']}` | `{row['destination']}` | `{row['size_kb']}` | `{row['verified']}` | `{row['pruned']}` |"
    )
md_path.write_text('\n'.join(lines) + '\n')
PY

echo "Archive ready: $ARCHIVE_ROOT"
echo "Manifest JSON: $MANIFEST_JSON"
echo "Manifest MD:   $MANIFEST_MD"
if [[ "$PRUNE" == true ]]; then
  echo "Local sources pruned after verification."
else
  echo "Dry retention mode: local sources kept."
fi
