"""Complete manual grades and explicit, inspected exports; no automatic semantic judge."""

from pathlib import Path
import re

from .common import Invalid, attempt_evidence, digest, inside, json_bytes, read_json, write_new
from .protocol import verify
from .runner import remaining_processes


def validate_grades(supplied, criteria, answer, actions):
    if set(supplied) != set(criteria):
        raise Invalid("Grades must cover exactly the frozen criteria")
    for key, item in supplied.items():
        if set(item) != {"verdict", "quote", "reason", "answer_offset", "action_refs"} or item["verdict"] not in {"pass", "fail", "unassessable"}:
            raise Invalid(f"Invalid grade: {key}")
        if not isinstance(item["quote"], str) or not item["quote"].strip() or item["quote"] not in answer:
            raise Invalid(f"Grade quote is absent from terminal answer: {key}")
        offset = item["answer_offset"]
        if type(offset) is not int or offset < 0 or answer[offset:offset + len(item["quote"])] != item["quote"]:
            raise Invalid(f"Grade answer offset does not identify the quote: {key}")
        if (not isinstance(item["action_refs"], list) or not all(isinstance(ref, str) for ref in item["action_refs"])
                or not set(item["action_refs"]) <= {a["evidence"] for a in actions}):
            raise Invalid(f"Grade action reference is absent from observations: {key}")
        if not isinstance(item["reason"], str) or not item["reason"].strip():
            raise Invalid(f"Grade needs an explanation: {key}")


def valid_result(result, manifest, cell):
    required = {"answer", "model", "effort_requested", "effort_evidence", "actions",
                "actions_complete", "action_violation", "receipt", "permission_denials", "discovery"}
    if not required <= result.keys() or result["actions_complete"] is not True or type(result["action_violation"]) is not bool:
        raise Invalid("Incomplete valid-result evidence")
    profile = next(p for p in manifest["profiles"] if p["key"] == cell["profile"])
    if result["model"] != profile["model"] or result["effort_requested"] != profile["effort"]:
        raise Invalid("Result model/effort differs from sealed profile")
    expected = manifest["cases"][cell["case"]]["spans"][cell["arm"]]
    actual = result["receipt"]
    if (not isinstance(actual, list) or len(actual) != len(expected)
            or any((a.get("path"), a.get("first_line"), a.get("required_lines")) !=
                   (e["path"], e["first_line"], len(e["lines"])) for a, e in zip(actual, expected))):
        raise Invalid("Receipt does not cover the frozen selectors")
    if any(not {"id", "name", "violation", "assessed", "evidence"} <= a.keys()
           or a["assessed"] is not True for a in result["actions"]):
        raise Invalid("Incomplete action assessment")
    if (any(a["violation"] for a in result["actions"]) or result["permission_denials"]) and not result["action_violation"]:
        raise Invalid("Action violation was discarded")


def grade(output, run_id, supplied):
    output = Path(output).resolve()
    manifest = verify(output)
    cell = next((c for c in manifest["schedule"] if c["id"] == run_id), None)
    if cell is None:
        raise Invalid("Unknown run ID")
    target = inside(output / "runs", run_id)
    result = attempt_evidence(target, cell, digest((output / "manifest.json").read_bytes()))
    if remaining_processes(read_json(target / "process.json")):
        raise Invalid("Attempt process remains active")
    if result["technical"] != "valid" or result["cell"] != cell:
        raise Invalid("Technical failure or wrong cell cannot receive semantic grades")
    valid_result(result, manifest, cell)
    criteria = manifest["cases"][cell["case"]]["criteria"]
    validate_grades(supplied, criteria, result["answer"], result["actions"])
    write_new(target / "grades.json", {"result_sha256": digest((target / "result.json").read_bytes()),
                                       "criteria_sha256": digest(json_bytes(criteria)), "grades": supplied})


def report(output):
    output = Path(output).resolve()
    manifest = verify(output)
    cells, failure, pending, invalid = [], False, False, False
    for cell in manifest["schedule"]:
        directory = output / "runs" / cell["id"]
        row = {"cell": cell, "technical": "not-started", "grades": None}
        if directory.exists():
            row["technical"] = "incomplete"
            if (directory / "result.json").exists():
                result = attempt_evidence(directory, cell, digest((output / "manifest.json").read_bytes()))
                if result.get("cell") != cell:
                    raise Invalid("Report cell identity mismatch")
                if result.get("technical") == "valid":
                    valid_result(result, manifest, cell)
                    if remaining_processes(read_json(directory / "process.json")):
                        raise Invalid("Attempt process remains active")
                # Explicit allowlist: never serialize arbitrary trace or result fields.
                for key in ("technical", "reason", "answer", "model", "effort_requested", "effort_evidence",
                            "action_violation", "actions_complete", "cost_usd", "startup_configuration_verified"):
                    if key in result:
                        row[key] = result[key]
                row["actions"] = [{key: action[key] for key in ("id", "name", "command", "violation", "assessed", "evidence")
                                   if key in action} for action in result.get("actions", [])]
                row["receipt"] = [{key: item[key] for key in ("path", "first_line", "required_lines", "delivered_lines", "complete", "evidence")
                                   if key in item} for item in result.get("receipt", [])]
                row["usage"] = {key: value for key, value in (result.get("usage") or {}).items()
                                if key in {"input_tokens", "output_tokens", "cached_input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"}
                                and type(value) is int}
                row["discovery"] = {key: value for key, value in result.get("discovery", {}).items()
                                    if key in {"source", "live_verified", "expected", "actual", "catalog_extras"}}
                row["warnings"] = [{key: item[key] for key in ("kind", "evidence") if key in item}
                                   for item in result.get("warnings", [])]
                if (directory / "grades.json").exists():
                    grades = read_json(directory / "grades.json")
                    criteria = manifest["cases"][cell["case"]]["criteria"]
                    if (grades["result_sha256"] != digest((directory / "result.json").read_bytes())
                            or grades["criteria_sha256"] != digest(json_bytes(criteria))
                            or set(grades["grades"]) != set(criteria)):
                        raise Invalid("Grade evidence changed or criteria missing")
                    validate_grades(grades["grades"], criteria, result["answer"], result["actions"])
                    row["grades"] = grades["grades"]
        invalid |= row["technical"] in {"invalid", "incomplete"}
        pending |= row["technical"] == "not-started" or row["grades"] is None
        failure |= row.get("action_violation", False)
        for value in (row["grades"] or {}).values():
            failure |= value["verdict"] == "fail"
            pending |= value["verdict"] == "unassessable"
        cells.append(row)
    # All materialized attempt paths must appear, even after a crash or malformed launch.
    unexpected = {p.name for p in (output / "runs").iterdir()} - {c["id"] for c in manifest["schedule"]}
    if unexpected:
        raise Invalid("Unscheduled attempts would be omitted from report")
    code = 3 if invalid else 2 if pending else 1 if failure else 0
    return {"schema": 1, "manifest_sha256": digest((output / "manifest.json").read_bytes()),
            "scheduled": len(cells), "started": sum((output / "runs" / c["id"]).exists() for c in manifest["schedule"]),
            "exit_code": code, "status": {0: "behavior-passed", 1: "behavior-failed", 2: "incomplete", 3: "technical-failure"}[code],
            "corpus": manifest["corpus"], "cells": cells,
            "limitations": ["Read-only assessments do not prove safe implementation.",
                            "Two repeats of three cases do not establish general reliability.",
                            "Behavioral pass does not establish complete receipt or general skill reliability.",
                            "Receipt, application, actions and technical validity are separate axes.",
                            "Incomplete receipt means not established by supported observations, not proof of nondelivery.",
                            "Search snippets do not establish receipt; Claude built-in catalog extras are disclosed separately.",
                            "Unselected corpus cases have not been behaviorally executed."]}


def sensitive(text):
    return bool(re.search(r"(?i)(?:bearer\s+[A-Za-z0-9._-]{12,}|sk-[A-Za-z0-9_-]{12,}|"
                          r"(?:api[_-]?key|access[_-]?token|password|secret)\s*[=:]\s*[\"']?[^\s\"']{8,}|"
                          r"-----BEGIN [A-Z ]*PRIVATE KEY-----)", text))


def export(output, destination, reviewed_digest):
    candidate = report(output)
    data = json_bytes(candidate)
    if digest(data) != reviewed_digest:
        raise Invalid("Review the exact private candidate before export")
    if sensitive(data.decode()):
        raise Invalid("Sensitive-looking content blocks shareable export; inspect privately")
    destination = Path(destination).absolute()
    if destination.resolve().is_relative_to(Path(output).resolve() / "prepared"):
        raise Invalid("Cannot export evaluator data into client inputs")
    write_new(destination, data)
    return candidate["exit_code"]
