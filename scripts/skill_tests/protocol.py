"""Freeze visible inputs independently of evaluator criteria and execution state."""

import importlib.metadata
from pathlib import Path
import re
import shutil
import subprocess
import uuid

from .common import Invalid, digest, inside, inventory, json_bytes, load_yaml, read_json, verify_inventory, write_new
from .structure import local_packages, owned_files


PROFILES = [
    {"key": "sonnet", "client": "claude", "model": "claude-sonnet-5-5", "effort": "medium"},
    {"key": "luna", "client": "codex", "model": "gpt-6-luna", "effort": "medium"},
]
CORPUS = Path(__file__).parent / "cases"


def cases(root=CORPUS):
    result = {}
    for path in sorted(Path(root).glob("*/case.yaml")):
        case = load_yaml(path.read_text())
        required = {"id", "kind", "initial_live", "prompt", "criteria", "receipt"}
        if not isinstance(case, dict) or set(case) != required:
            raise Invalid(f"Invalid case fields: {path}")
        if not re.fullmatch(r"[a-z][a-z0-9-]*", case["id"]) or case["id"] != path.parent.name:
            raise Invalid(f"Invalid case ID: {path}")
        if case["kind"] not in {"application", "trigger", "near-miss", "held-out"}:
            raise Invalid("Invalid case kind")
        if type(case["initial_live"]) is not bool or not isinstance(case["prompt"], str) or not case["prompt"].strip():
            raise Invalid("Invalid live flag or prompt")
        if not isinstance(case["criteria"], dict) or not case["criteria"]:
            raise Invalid("Case requires evaluator criteria")
        for name, criterion in case["criteria"].items():
            if not re.fullmatch(r"[A-Z][0-9]+", name) or not isinstance(criterion, str) or not criterion.strip():
                raise Invalid("Invalid criterion")
        if not isinstance(case["receipt"], list):
            raise Invalid("Invalid receipt selectors")
        for selector in case["receipt"]:
            if set(selector) != {"path", "heading"} or not all(isinstance(x, str) and x for x in selector.values()):
                raise Invalid("Invalid receipt selector")
            inside(Path(root), selector["path"])
        visible = path.parent / "scenario"
        if not visible.is_dir() or not inventory(visible):
            raise Invalid("Case needs nonempty visible fixtures")
        case["fixtures"] = inventory(visible)
        result[case["id"]] = case
    if not result:
        raise Invalid("Empty corpus")
    return result


def schedule(case_ids, profiles, arms, repeats):
    if not case_ids or not profiles or not arms or repeats < 1:
        raise Invalid("Empty or invalid schedule")
    result = []
    for repeat in range(repeats):
        for case_index, case in enumerate(case_ids):
            rotation = (repeat + case_index) % len(profiles)
            for profile in profiles[rotation:] + profiles[:rotation]:
                ordered = arms if (repeat + case_index + profiles.index(profile)) % 2 == 0 else list(reversed(arms))
                for arm in ordered:
                    result.append({"id": f"run-{len(result)+1:03}", "case": case, "profile": profile["key"],
                                   "arm": arm, "repeat": repeat + 1})
    return result


def source_snapshot(repo, destination):
    files = owned_files(repo)
    packages = local_packages(repo, files)
    selected = [name for name in files if any(name.startswith(p + "/") for p in packages)]
    selected += [".codex/AGENTS.md", "AGENTS.md", "README.md"]
    destination.mkdir(parents=True)
    for name in selected:
        source = inside(repo, name)
        if source.is_symlink() or not source.is_file():
            raise Invalid(f"Snapshot source must be a regular owned file: {name}")
        target = inside(destination, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    for package in packages:
        alias = destination / ".agents/skills" / Path(package).name
        alias.parent.mkdir(parents=True, exist_ok=True)
        alias.symlink_to(f"../../{package}")
    (destination / "CLAUDE.md").write_text("@AGENTS.md\n")
    return inventory(destination)


def select_span(source, heading):
    lines = source.splitlines()
    matches = [i for i, line in enumerate(lines) if line == heading]
    if len(matches) != 1 or not heading.startswith("#"):
        raise Invalid(f"Expected unique heading: {heading}")
    start = matches[0]
    level = len(heading) - len(heading.lstrip("#"))
    end = next((i for i in range(start + 1, len(lines))
                if re.match(rf"^#{{1,{level}}} ", lines[i])), len(lines))
    return {"first_line": start + 1, "lines": lines[start:end]}


def code_fingerprint():
    return {p.name: digest(p.read_bytes()) for p in sorted(Path(__file__).parent.glob("*.py"))}


def prepare(repo, output, *, baseline=None, repeats=2, ceiling=12, case_ids=None, corpus=CORPUS):
    repo, output = Path(repo).resolve(), Path(output).absolute()
    if output.is_symlink() or output.resolve() != output:
        raise Invalid("Output must not traverse symlinks")
    if output.is_relative_to(Path.home()):
        raise Invalid("Live workspaces must be outside the real home instruction-discovery tree")
    all_cases = cases(corpus)
    selected = case_ids if case_ids is not None else [k for k, c in all_cases.items() if c["initial_live"]]
    if len(selected) != len(set(selected)) or any(x not in all_cases for x in selected):
        raise Invalid("Unknown or duplicate selected cases")
    clients = {}
    for name in {p["client"] for p in PROFILES}:
        executable = shutil.which(name)
        if executable is None:
            raise Invalid(f"Missing client: {name}")
        executable = str(Path(executable).resolve())
        version = subprocess.run([executable, "--version"], capture_output=True, text=True, check=True)
        clients[name] = {"executable": executable, "version": version.stdout.strip(),
                         "sha256": digest(Path(executable).read_bytes())}
    output.mkdir(mode=0o700)
    arms = {"current": source_snapshot(repo, output / "sources/current")}
    if baseline is not None:
        baseline = Path(baseline).resolve()
        # An explicitly supplied source snapshot, not a Git checkout or history mutation.
        if not (baseline / ".codex/AGENTS.md").is_file():
            raise Invalid("Baseline must be an explicit complete skill source snapshot")
        inventory(baseline)
        shutil.copytree(baseline, output / "sources/baseline", symlinks=True)
        arms["baseline"] = inventory(output / "sources/baseline")
    selected_cases = {}
    for key in selected:
        case = dict(all_cases[key])
        target = output / "fixtures" / key
        shutil.copytree(Path(corpus) / key / "scenario", target, symlinks=True)
        case["spans"] = {}
        for arm in arms:
            case["spans"][arm] = []
            for selector in case["receipt"]:
                name = selector["path"]
                source = inside(target, name.removeprefix("scenario/")) if name.startswith("scenario/") else inside(output / "sources" / arm, name)
                case["spans"][arm].append({"path": name, **select_span(source.read_text(), selector["heading"])})
        selected_cases[key] = case
    cells = schedule(selected, PROFILES, list(arms), repeats)
    if type(ceiling) is not int or ceiling < 1 or len(cells) > ceiling:
        raise Invalid("Schedule exceeds positive attempt ceiling")
    manifest = {"schema": 1, "round_id": str(uuid.uuid4()), "profiles": PROFILES, "clients": clients, "arms": arms,
                "cases": selected_cases, "schedule": cells, "ceiling": ceiling,
                "corpus": {k: {"kind": v["kind"], "selected": k in selected} for k, v in all_cases.items()},
                "code": code_fingerprint(), "dependencies": {
                    name: importlib.metadata.version(name) for name in ("PyYAML", "markdown-it-py", "pytest")}}
    write_new(output / "manifest.json", manifest)
    seal = digest(json_bytes(manifest))
    write_new(output / "manifest.sha256", (seal + "\n").encode())
    (output / "runs").mkdir(mode=0o700)
    return seal


def verify(output, expected_seal=None):
    output = Path(output).resolve()
    manifest = read_json(output / "manifest.json")
    seal = digest(json_bytes(manifest))
    if seal != (output / "manifest.sha256").read_text().strip() or (expected_seal and seal != expected_seal):
        raise Invalid("Manifest seal mismatch")
    if manifest["schema"] != 1 or manifest["code"] != code_fingerprint():
        raise Invalid("Executor changed after sealing")
    for name, version in manifest["dependencies"].items():
        if importlib.metadata.version(name) != version:
            raise Invalid("Dependency changed after sealing")
    for arm, expected in manifest["arms"].items():
        verify_inventory(output / "sources" / arm, expected)
    for key, case in manifest["cases"].items():
        verify_inventory(output / "fixtures" / key, case["fixtures"])
    return manifest
