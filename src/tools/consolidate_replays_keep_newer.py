#!/usr/bin/env python3
"""Consolidate replay conflicts by keeping the newer file.

For every file in `replays/conflicts/`, compare the modification time with
`replays/<basename>`. If the conflict file is newer, replace the canonical
file in `replays/` with the conflict file and move the older one into
`replays/conflicts/` with an archival suffix. If the canonical file is
newer, keep it and archive the conflict file with an "old" suffix.

This script uses `git mv` when possible so history is preserved in the
repository. It is safe to run multiple times.
"""
from __future__ import annotations

import os
import sys
import shutil
import subprocess
import time
from pathlib import Path


REPLAYS_DIR = Path("replays")
CONFLICTS_DIR = REPLAYS_DIR / "conflicts"


def git_mv(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(["git", "mv", str(src), str(dest)], check=True)
    except subprocess.CalledProcessError:
        # fall back to filesystem move if git mv fails
        shutil.move(str(src), str(dest))


def archive_path(base: Path, tag: str) -> Path:
    ts = time.strftime("%Y%m%dT%H%M%S")
    return base.parent / f"{base.name}.{tag}.{ts}"


def main(dry_run: bool = False) -> int:
    if not REPLAYS_DIR.exists() or not CONFLICTS_DIR.exists():
        print("No conflicts directory found; nothing to do.")
        return 0

    moved = 0
    for p in sorted(CONFLICTS_DIR.iterdir()):
        if not p.is_file():
            continue
        dest = REPLAYS_DIR / p.name
        conflict_mtime = p.stat().st_mtime

        if not dest.exists():
            print(f"No canonical file for {p.name}; moving conflict -> {dest}")
            if not dry_run:
                git_mv(p, dest)
            moved += 1
            continue

        dest_mtime = dest.stat().st_mtime
        if conflict_mtime > dest_mtime:
            # conflict is newer: archive the old canonical and promote conflict
            archive_dest = archive_path(dest, "older")
            print(f"Conflict {p.name} is newer: archive {dest} -> {archive_dest} and promote {p} -> {dest}")
            if not dry_run:
                git_mv(dest, archive_dest)
                git_mv(p, dest)
            moved += 1
        else:
            # canonical is newer: archive the conflict as old
            archive_conf = archive_path(p, "old")
            print(f"Canonical {dest.name} is newer: archive conflict {p} -> {archive_conf}")
            if not dry_run:
                git_mv(p, archive_conf)
            moved += 1

    print(f"Processed {moved} conflict files.")
    return 0


if __name__ == '__main__':
    dry = False
    if len(sys.argv) > 1 and sys.argv[1] in ("--dry-run", "-n"):
        dry = True
    raise SystemExit(main(dry_run=dry))
