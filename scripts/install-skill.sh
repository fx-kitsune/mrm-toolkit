#!/usr/bin/env sh
set -eu

usage() {
  cat <<'USAGE'
Install the ModularResearchDocWriter Codex skill via pip.

Usage:
  scripts/install-skill.sh [SKILLS_DIR] [PIP_SOURCE] [TOOLKIT_DIR]

Arguments:
  SKILLS_DIR   Parent folder for installed skills.
               Default: $CODEX_HOME/skills, or ~/.codex/skills when CODEX_HOME is unset.
  PIP_SOURCE   pip install source for this package.
               Default: repository root that contains this script.
  TOOLKIT_DIR  Per-user MRM toolkit folder.
               Default: $MRM_TOOLKIT_HOME, or ~/.mrm-toolkit when unset.

Examples:
  scripts/install-skill.sh
  scripts/install-skill.sh "$HOME/.codex/skills" .
  scripts/install-skill.sh /tmp/codex-skills git+https://github.com/<owner>/<repo>.git

Environment:
  PYTHON       Python executable to use. Default: python3, then python.
  PIP_TARGET   Temporary pip --target folder. Default: a new folder under TMPDIR.
  MRM_TOOLKIT_HOME
               Default toolkit folder when TOOLKIT_DIR is omitted.
  OVERWRITE    Set to 1/true/yes to replace an existing skill directory.
USAGE
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ -n "${PYTHON:-}" ]; then
  PYTHON_BIN=$PYTHON
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
else
  echo "ERROR: Python is required but was not found." >&2
  exit 1
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

DEFAULT_SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
SKILLS_DIR=${1:-$DEFAULT_SKILLS_DIR}
PIP_SOURCE=${2:-$REPO_ROOT}
TOOLKIT_DIR=${3:-${MRM_TOOLKIT_HOME:-$HOME/.mrm-toolkit}}

if [ -z "${PIP_TARGET:-}" ]; then
  TMP_BASE=${TMPDIR:-/tmp}
  PIP_TARGET=$(mktemp -d "$TMP_BASE/mrm-skill-pip.XXXXXX")
  CLEAN_PIP_TARGET=1
else
  mkdir -p "$PIP_TARGET"
  CLEAN_PIP_TARGET=0
fi

cleanup() {
  if [ "$CLEAN_PIP_TARGET" = "1" ]; then
    rm -rf "$PIP_TARGET"
  fi
}
trap cleanup EXIT INT TERM

echo "Installing Python package from '$PIP_SOURCE' into temporary pip target '$PIP_TARGET'..."
"$PYTHON_BIN" -m pip install "$PIP_SOURCE" --target "$PIP_TARGET" --upgrade

set -- --target "$SKILLS_DIR" --toolkit-target "$TOOLKIT_DIR"
case "${OVERWRITE:-}" in
  1|true|TRUE|yes|YES) set -- "$@" --overwrite ;;
esac

echo "Installing Codex skill into '$SKILLS_DIR' and MRM toolkit into '$TOOLKIT_DIR'..."
PYTHONPATH="$PIP_TARGET${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m modular_research_doc_writer.installer "$@"
