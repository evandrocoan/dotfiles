#!/usr/bin/env python3
"""Expand Windows separators embedded in ZIP-extracted Linux filenames."""

import os
from pathlib import Path


BAD_SEPARATORS = ("\uf05c", "\\")


def replacement_path(source):
    """Return the nested target for an encoded filename, or None if unchanged."""
    source = Path(source)
    replacement = source.name
    for separator in BAD_SEPARATORS:
        replacement = replacement.replace(separator, "/")
    replacement = replacement.lstrip("/")
    parts = replacement.split("/")
    if len(parts) < 2:
        return None
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError(f"unsafe encoded path: {source.name!r}")
    return source.parent.joinpath(*parts)


def repair_paths(root=Path(".")):
    """Repair encoded paths below root and return the source/target pairs moved."""
    root = Path(root).resolve()
    repairs = []
    for current, directory_names, file_names in os.walk(root, topdown=False):
        for name in file_names + directory_names:
            source = Path(current) / name
            target = replacement_path(source)
            if target is None:
                continue
            repairs.append((source, target))

    targets = set()
    for source, target in repairs:
        if target in targets or os.path.lexists(target):
            raise FileExistsError(f"refusing to replace existing path: {target}")
        targets.add(target)
        try:
            relative_target = target.relative_to(root)
        except ValueError as error:
            raise ValueError(f"unsafe target outside repair root: {target}") from error
        parent = root
        for part in relative_target.parts[:-1]:
            parent /= part
            if parent.is_symlink():
                raise ValueError(f"unsafe symlink in target path: {parent}")
            if parent.exists() and not parent.is_dir():
                raise NotADirectoryError(
                    f"refusing target beneath non-directory path: {parent}"
                )

    moved = []
    for source, target in repairs:
        target.parent.mkdir(parents=True, exist_ok=True)
        source.rename(target)
        moved.append((source, target))
    return moved


def main():
    for _, target in repair_paths():
        print(f"moved to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
