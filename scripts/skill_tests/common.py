"""Strict input, immutable evidence, and filesystem boundaries."""

import hashlib
import json
import os
from pathlib import Path
import stat

import yaml


class Invalid(ValueError):
    """An input or observation cannot support the requested claim."""


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, (str, int, float, bool, type(None))):
            raise Invalid("Non-scalar mapping key")
        if key in result:
            raise Invalid(f"Duplicate mapping key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def load_yaml(text):
    try:
        return yaml.load(text, Loader=UniqueLoader)
    except yaml.YAMLError as error:
        raise Invalid(f"Invalid YAML: {error}") from error


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise Invalid(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        return json.loads(Path(path).read_text(), object_pairs_hook=pairs)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise Invalid(f"Invalid JSON: {path}") from error


def write_new(path, value):
    """Exclusive durable creation, including the containing directory entry."""
    path = Path(path)
    data = value if isinstance(value, bytes) else json_bytes(value)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def attempt_evidence(directory, cell, manifest_seal):
    """Bind all completed attempt records to the same sealed round and cell."""
    reservation = read_json(directory / "reservation.json")
    result = read_json(directory / "result.json")
    terminal = read_json(directory / "terminal.json")
    for value in (reservation, result, terminal):
        if value.get("manifest") != manifest_seal or value.get("cell") != cell:
            raise Invalid("Attempt manifest or cell identity mismatch")
    if result.get("technical") == "valid" and terminal.get("exit") != 0:
        raise Invalid("Valid result contradicts terminal exit")
    return result


def inside(root, relative):
    root = Path(root).resolve()
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise Invalid(f"Expected a nonescaping relative path: {relative}")
    target = root / relative
    if not target.resolve().is_relative_to(root):
        raise Invalid(f"Path escapes declared root: {relative}")
    return target


def inventory(root):
    """Include dotfiles and directories; inspect link boundaries before reading."""
    root = Path(root).resolve()
    result = {}
    for directory, directories, files in os.walk(root, followlinks=False):
        for name in sorted(directories + files):
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                if not path.resolve().is_relative_to(root):
                    raise Invalid(f"Escaping symlink: {relative}")
                if not path.exists():
                    raise Invalid(f"Broken symlink: {relative}")
                result[relative] = {"symlink": os.readlink(path)}
            elif stat.S_ISDIR(mode):
                result[relative] = {"directory": True}
            elif stat.S_ISREG(mode):
                result[relative] = {"sha256": digest(path.read_bytes())}
            else:
                raise Invalid(f"Special file: {relative}")
    return result


def verify_inventory(root, expected):
    actual = inventory(root)
    if actual != expected:
        raise Invalid("Inventory mismatch: " + json.dumps({
            "added": sorted(actual.keys() - expected.keys()),
            "removed": sorted(expected.keys() - actual.keys()),
            "changed": sorted(p for p in actual.keys() & expected.keys()
                              if actual[p] != expected[p]),
        }))
