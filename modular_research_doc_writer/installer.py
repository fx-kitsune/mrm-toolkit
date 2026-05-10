"""Install the bundled ModularResearchDocWriter skill into a Codex skills folder."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path
from typing import Optional

DEFAULT_SKILL_NAME = "modular-research-doc-writer"
TOOLKIT_DIR_NAME = "mrm-toolkit"


def default_skills_dir() -> Path:
    """Return the default Codex skills directory for the current user."""
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "skills"
    return Path.home() / ".codex" / "skills"


def bundled_skill_dir() -> Path:
    """Return the filesystem path to the bundled skill directory."""
    return Path(__file__).resolve().parent / "skills" / DEFAULT_SKILL_NAME


def bundled_skill_file() -> Path:
    """Return the filesystem path to the bundled SKILL.md file."""
    return bundled_skill_dir() / "SKILL.md"


def source_toolkit_dir() -> Optional[Path]:
    """Return the source-checkout toolkit path when the package data has not been materialized."""
    for parent in Path(__file__).resolve().parents:
        candidate = parent / TOOLKIT_DIR_NAME
        if candidate.is_dir():
            return candidate
    return None


def copy_skill_tree(source_dir: Path, destination_dir: Path) -> None:
    """Copy the bundled skill directory contents to the destination."""
    for source_path in source_dir.iterdir():
        destination_path = destination_dir / source_path.name
        if source_path.is_dir():
            shutil.copytree(source_path, destination_path, dirs_exist_ok=True)
        else:
            shutil.copy2(source_path, destination_path)


def install_skill(target_dir: Path, skill_name: str = DEFAULT_SKILL_NAME, overwrite: bool = False) -> Path:
    """Copy the bundled skill directory to ``target_dir / skill_name``.

    The installed directory includes ``SKILL.md`` and, when available, the
    ``mrm-toolkit`` reference files used by the skill prompt.

    Args:
        target_dir: Parent directory that contains Codex skills.
        skill_name: Destination folder name for the skill.
        overwrite: Replace an existing destination directory when true.

    Returns:
        The installed SKILL.md path.
    """
    source_dir = bundled_skill_dir()
    source_file = source_dir / "SKILL.md"
    destination_dir = target_dir.expanduser().resolve() / skill_name
    destination = destination_dir / "SKILL.md"

    if not source_file.is_file():
        raise FileNotFoundError(f"Bundled skill file was not found: {source_file}")

    if destination_dir.exists():
        if not overwrite:
            raise FileExistsError(f"Skill already exists at {destination_dir}; pass --overwrite to replace it.")
        shutil.rmtree(destination_dir)

    destination_dir.mkdir(parents=True, exist_ok=True)
    copy_skill_tree(source_dir, destination_dir)

    destination_toolkit = destination_dir / TOOLKIT_DIR_NAME
    if not destination_toolkit.exists():
        toolkit_dir = source_toolkit_dir()
        if toolkit_dir is not None:
            shutil.copytree(toolkit_dir, destination_toolkit)

    return destination


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install the ModularResearchDocWriter Codex skill from the pip package."
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=default_skills_dir(),
        help="Parent skills directory. Defaults to $CODEX_HOME/skills or ~/.codex/skills.",
    )
    parser.add_argument(
        "--name",
        default=DEFAULT_SKILL_NAME,
        help=f"Destination skill folder name. Defaults to {DEFAULT_SKILL_NAME}.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing skill directory at the destination.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    destination = install_skill(args.target, skill_name=args.name, overwrite=args.overwrite)
    print(f"Installed ModularResearchDocWriter skill: {destination}")


if __name__ == "__main__":
    main()
