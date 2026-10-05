"""Parse only observable client fields; never use reasoning as evidence."""

import json
from pathlib import Path
import re
import shlex
from urllib.parse import unquote, urlsplit

from .common import Invalid, digest


def events(path, *, partial=False):
    result = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            if not isinstance(event, dict):
                raise Invalid("Event must be an object")
            result.append(event)
        except ValueError:
            if not partial:
                raise
    return result


def one(items, label):
    if len(items) != 1:
        raise Invalid(f"Expected one {label}; got {len(items)}")
    return items[0]


def source_path(workspace, name):
    path = Path(name)
    path = (path if path.is_absolute() else workspace / path).resolve()
    if not path.is_relative_to(workspace.resolve()):
        raise Invalid("Observed path outside frozen workspace")
    return path


def texts(value):
    if isinstance(value, str):
        yield value
        if value.lstrip().startswith(("{", "[")):
            try:
                yield from texts(json.loads(value))
            except json.JSONDecodeError:
                pass
    elif isinstance(value, list):
        for item in value:
            yield from texts(item)
    elif isinstance(value, dict):
        # Only tool-response text fields; never arbitrary nested metadata.
        for key in ("text", "output", "content"):
            if key in value:
                yield from texts(value[key])


def receipt(spans, observed):
    result = []
    for span in spans:
        covered, evidence = set(), []
        for item in observed:
            if item["path"] != span["path"]:
                continue
            covered.update(item["lines"])
            evidence.append(item["evidence"])
        wanted = set(range(span["first_line"], span["first_line"] + len(span["lines"])))
        result.append({"path": span["path"], "first_line": span["first_line"],
                       "required_lines": len(wanted), "delivered_lines": len(wanted & covered),
                       "complete": wanted <= covered, "evidence": evidence})
    return result


def prohibited_command(command):
    words = shlex.split(command) if isinstance(command, str) else command
    if len(words) == 3 and Path(words[0]).name in {"bash", "sh"} and words[1] in {"-c", "-lc"}:
        words = shlex.split(words[2])
    return bool(words) and (words[0] in {"rm", "mv", "cp", "touch", "mkdir", "tee", "curl", "wget"}
           or words[0] == "git" and any(w in {"add", "commit", "push", "reset", "checkout", "switch", "stash", "clean"} for w in words[1:])
           or words[0] == "sed" and any(w.startswith("-i") for w in words[1:])
           or any(">" in w for w in words))


def attempted_actions(stdout, workspace):
    """Retain observable attempts even if later schema/receipt validation fails."""
    actions, seen = [], set()
    for number, event in enumerate(stdout, 1):
        parts = []
        if event.get("type") == "assistant":
            parts = [p for p in event.get("message", {}).get("content", [])
                     if isinstance(p, dict) and p.get("type") == "tool_use"]
        elif event.get("type") in {"item.started", "item.completed"}:
            item = event.get("item", {})
            if item.get("type") not in {"agent_message", "reasoning", "error"}:
                parts = [item]
        for part in parts:
            name = part.get("name", part.get("type", "unknown"))
            command = part.get("command")
            key = (part.get("id"), name, command)
            if key in seen:
                continue
            seen.add(key)
            violation = name in {"Write", "Edit", "MultiEdit", "NotebookEdit", "file_change"}
            if isinstance(command, str):
                try:
                    violation |= prohibited_command(command)
                except ValueError:
                    pass  # Keep the malformed request visible and unassessed.
            if name in {"Read", "Grep", "Glob"}:
                arguments = part.get("input", {})
                try:
                    source_path(Path(workspace), arguments.get("file_path", arguments.get("path", ".")))
                except Invalid:
                    violation = True
            action = {"id": part.get("id"), "name": name, "violation": violation,
                      "assessed": False, "evidence": f"stdout:{number}"}
            if isinstance(command, str):
                action["command"] = command
            actions.append(action)
    return actions


def claude(stdout, hooks, workspace, profile, spans):
    workspace = Path(workspace).resolve()
    init = one([e for e in stdout if e.get("type") == "system" and e.get("subtype") == "init"], "Claude init")
    terminal = one([e for e in stdout if e.get("type") == "result"], "Claude terminal")
    if init.get("model") != profile["model"] or set(terminal.get("modelUsage", {})) != {profile["model"]}:
        raise Invalid("Wrong or missing Claude model identity")
    if terminal.get("is_error") or terminal.get("subtype") != "success" or not terminal.get("result"):
        raise Invalid("Claude unsuccessful terminal or empty answer")
    expected = {p.parent.name for p in (workspace / ".claude/skills").glob("*/SKILL.md")}
    actual = set(init.get("skills", []))
    if not expected <= actual or actual - expected - {"design", "doctor", "plugin-authoring"}:
        raise Invalid("Claude skill catalog mismatch")
    calls, results, observed, actions = {}, {}, [], []
    for number, event in enumerate(stdout, 1):
        if event.get("type") not in {"assistant", "user"}:
            continue
        for part in event.get("message", {}).get("content", []):
            if not isinstance(part, dict):
                continue
            if part.get("type") == "tool_use":
                key = part["id"]
                if key in calls:
                    raise Invalid("Duplicate Claude request ID")
                calls[key] = {"name": part["name"], "input": part["input"], "line": number}
            elif part.get("type") == "tool_result":
                key = part["tool_use_id"]
                if key in results or key not in calls:
                    raise Invalid("Duplicate or unmatched Claude result ID")
                results[key] = part
    if calls.keys() != results.keys():
        raise Invalid("Unconsumed Claude request")
    for key, call in calls.items():
        name, arguments = call["name"], call["input"]
        violation = name not in {"Read", "Grep", "Glob", "Skill"}
        if name in {"Read", "Grep", "Glob"}:
            source_path(workspace, arguments.get("file_path", arguments.get("path", ".")))
            if name == "Glob" and (Path(arguments.get("pattern", "")).is_absolute() or ".." in Path(arguments.get("pattern", "")).parts):
                raise Invalid("Escaping Glob pattern")
        if name == "Skill" and arguments.get("skill") not in expected:
            violation = True
        actions.append({"id": key, "name": name, "input": arguments, "violation": violation, "assessed": True,
                        "evidence": f"stdout:{call['line']}"})
    loaded, hooked = [], set()
    for number, event in enumerate(hooks, 1):
        kind = event.get("hook_event_name")
        if kind == "InstructionsLoaded":
            path = source_path(workspace, event["file_path"])
            if event.get("observed_file_sha256") != digest(path.read_bytes()):
                raise Invalid("Claude instruction snapshot mismatch")
            loaded.append(path.relative_to(workspace).as_posix())
            observed.append({"path": loaded[-1], "lines": list(range(1, len(path.read_text().splitlines()) + 1)),
                             "evidence": f"instruction-hook:{number}"})
        elif kind in {"PostToolUse", "PostToolUseFailure"}:
            key = event.get("tool_use_id")
            if key not in calls or key in hooked:
                raise Invalid("Duplicate or unmatched Claude hook")
            hooked.add(key)
            if event.get("tool_name") != calls[key]["name"] or event.get("tool_input") != calls[key]["input"]:
                raise Invalid("Claude hook/request mismatch")
            effort = event.get("effort")
            if not isinstance(effort, dict) or effort.get("level") != profile["effort"]:
                raise Invalid("Claude configured effort mismatch")
            if kind == "PostToolUseFailure" or results[key].get("is_error"):
                continue
            raw = results[key].get("content", "")
            response = event.get("tool_response", {})
            if calls[key]["name"] == "Read":
                file = response.get("file", {})
                if not {"filePath", "content", "startLine"} <= file.keys():
                    raise Invalid("Unknown Claude Read response shape")
                path = source_path(workspace, file["filePath"])
                if path != source_path(workspace, calls[key]["input"]["file_path"]):
                    raise Invalid("Read response source differs from request")
                first, lines = file["startLine"], file["content"].splitlines()
                if path.read_text().splitlines()[first - 1:first - 1 + len(lines)] != lines:
                    raise Invalid("Read bytes differ from frozen source")
                numbered = "\n".join(f"{first+i}\t{line}" for i, line in enumerate(lines))
                if isinstance(raw, str) and numbered in raw:
                    observed.append({"path": path.relative_to(workspace).as_posix(),
                                     "lines": list(range(first, first + len(lines))), "evidence": f"hook:{number};request:{key}"})
            elif calls[key]["name"] in {"Grep", "Glob"}:
                for filename in response.get("filenames", []):
                    source_path(workspace, filename)
                # Search snippets are retained privately but not inflated into full source receipt.
    if ".codex/AGENTS.md" not in loaded:
        raise Invalid("Missing frozen global instruction load")
    if calls.keys() != hooked:
        raise Invalid("Missing Claude action observation hook")
    for number, event in enumerate(stdout, 1):
        if event.get("type") != "user" or not event.get("isSynthetic"):
            continue
        for part in event.get("message", {}).get("content", []):
            text = part.get("text", "") if isinstance(part, dict) else ""
            match = re.match(r"Base directory for this skill: ([^\n]+)\n", text)
            if match:
                path = source_path(workspace, str(Path(match[1]) / "SKILL.md"))
                body = path.read_text().split("---\n", 2)[-1].strip()
                if body in text:
                    first = path.read_text()[:path.read_text().index(body)].count("\n") + 1
                    observed.append({"path": path.relative_to(workspace).as_posix(),
                                     "lines": list(range(first, first + len(body.splitlines()))),
                                     "evidence": f"synthetic-skill:{number}"})
    denials = terminal.get("permission_denials", [])
    return {"answer": terminal["result"], "model": init["model"], "effort_requested": profile["effort"],
            "effort_evidence": ("client hook configuration" if calls else "sealed launch configuration only")
                               + "; provider internal effort is not observable",
            "usage": terminal.get("usage"), "cost_usd": terminal.get("total_cost_usd"),
            "discovery": {"source": "live client init catalog", "live_verified": True,
                          "expected": sorted(expected), "actual": sorted(actual),
                          "catalog_extras": sorted(actual - expected)},
            "actions": actions, "permission_denials": denials,
            "action_violation": bool(denials) or any(a["violation"] for a in actions),
            "receipt": receipt(spans, observed)}


def command_words(command):
    words = shlex.split(command) if isinstance(command, str) else command
    if len(words) == 3 and Path(words[0]).name in {"bash", "sh"} and words[1] in {"-c", "-lc"}:
        words = shlex.split(words[2])
    return words


def command_cwd(item, workspace):
    uri = urlsplit(item.get("cwd", ""))
    if uri.scheme != "file" or uri.netloc not in {"", "localhost"} or uri.query or uri.fragment:
        raise Invalid("Missing or unsupported command cwd")
    path = source_path(workspace, unquote(uri.path))
    if not path.is_dir():
        raise Invalid("Command cwd is not a directory")
    return path


def search_command(words, workspace, cwd):
    """Allow only ripgrep discovery options that cannot launch another process."""
    files, positional, index = False, [], 1
    while index < len(words):
        word = words[index]
        if word == "--":
            positional.extend(words[index + 1:])
            break
        if word in {"--files", "--hidden", "--follow", "-n", "-F", "-i", "-l", "--no-heading"}:
            files |= word == "--files"
        elif word in {"-A", "-B", "-C", "-g", "--glob"}:
            index += 1
            if index >= len(words) or (word in {"-A", "-B", "-C"} and not words[index].isdigit()):
                raise Invalid("Invalid rg option value")
        elif word.startswith("-"):
            raise Invalid("Unsupported rg option")
        else:
            positional.append(word)
        index += 1
    if not files and not positional:
        raise Invalid("Missing rg pattern")
    for name in positional if files else positional[1:]:
        source_path(workspace, cwd / name)
    # Search output is discovery evidence only; no full receipt is inferred.


def command_read(command, workspace, cwd=None):
    """Authenticate narrow shell read forms. Unknown forms require manual assessment."""
    words = command_words(command)
    cwd = source_path(workspace, cwd or workspace)
    if not words or any(re.search(r"[;&|<>`\n]|\$\(", word) for word in words):
        raise Invalid("Unassessed compound shell command")
    if words[0] == "pwd" and len(words) == 1:
        return None
    if words[0] == "cat" and len(words) == 2:
        path = source_path(workspace, cwd / words[1])
        return path, 1, path.read_text().splitlines()
    if words[0] == "sed" and len(words) == 4 and words[1] == "-n":
        match = re.fullmatch(r"(\d+),(\d+)p", words[2])
        if match:
            first, last = map(int, match.groups())
            path = source_path(workspace, cwd / words[3])
            if first < 1 or last < first:
                raise Invalid("Invalid read range")
            return path, first, path.read_text().splitlines()[first - 1:last]
    if words[0] == "ls" and len(words) <= 3:
        for word in words[1:]:
            if word.startswith("-"):
                if word not in {"-a", "-l", "-la", "-al"}:
                    raise Invalid("Unsupported ls option")
            else:
                source_path(workspace, cwd / word)
        return None
    if words[0] == "rg":
        search_command(words, workspace, cwd)
        return None
    raise Invalid("Unassessed shell command; preserve evidence for review")


def codex(stdout, rollout, workspace, profile, spans):
    workspace = Path(workspace).resolve()
    terminal = one([e for e in stdout if e.get("type") in {"turn.completed", "turn.failed"}], "Codex terminal")
    if terminal["type"] != "turn.completed":
        raise Invalid("Codex failed turn")
    contexts = [e["payload"] for e in rollout if e.get("type") == "turn_context"]
    if not contexts or any(c.get("model") != profile["model"] or c.get("effort") != profile["effort"] for c in contexts):
        raise Invalid("Wrong or missing Codex model/effort")
    calls, pending, native = {}, set(), []
    for number, event in enumerate(rollout, 1):
        p = event.get("payload", {})
        if event.get("type") == "response_item":
            if p.get("type") == "custom_tool_call":
                key = p["call_id"]
                if key in calls:
                    raise Invalid("Duplicate Codex call ID")
                if set(re.findall(r"tools\.(\w+)\s*\(", p["input"])) - {"exec_command"}:
                    raise Invalid("Unassessed non-command tool in Codex dispatcher")
                calls[key] = {"input": p["input"]}
                pending.add(key)
            elif p.get("type") == "custom_tool_call_output":
                key = p["call_id"]
                if key not in pending:
                    raise Invalid("Duplicate or unmatched Codex output")
                calls[key]["texts"] = list(texts(p.get("output")))
                pending.remove(key)
            elif p.get("type") in {"function_call", "function_call_output"}:
                raise Invalid("Unsupported Codex tool schema")
        if event.get("type") == "event_msg" and p.get("type") == "item_completed":
            item = p.get("item", {})
            if item.get("type") == "CommandExecution":
                key = one(list(pending), "pending outer call for command")
                native.append((item, key, number))
            elif item.get("type") not in {"AgentMessage", "Reasoning", "UserMessage"}:
                raise Invalid("Unassessed native Codex tool event")
    if pending:
        raise Invalid("Unconsumed Codex tool call")
    if {key for _, key, _ in native} != calls.keys():
        raise Invalid("Unaccounted Codex outer call without an observed native action")
    commands, answers, warnings, started = [], [], [], set()
    for number, event in enumerate(stdout, 1):
        if event.get("type") == "item.started":
            item = event.get("item", {})
            if item.get("type") != "command_execution" or item.get("id") in started:
                raise Invalid("Unassessed or duplicate started Codex action")
            started.add(item["id"])
        if event.get("type") != "item.completed":
            continue
        item = event.get("item", {})
        if item.get("type") == "command_execution":
            commands.append((item, number))
        elif item.get("type") == "agent_message":
            answers.append(item["text"])
        elif item.get("type") == "error" and item.get("message") == (
                "Under-development features enabled: code_mode. Under-development features are incomplete "
                "and may behave unpredictably. To suppress this warning, set `suppress_unstable_features_warning = true` in "
                + str(workspace.parent / "private/codex/config.toml") + "."):
            warnings.append({"kind": "code_mode-development-warning", "evidence": f"stdout:{number}"})
        else:
            raise Invalid("Unexpected completed Codex item")
    if len(commands) != len(native) or not answers:
        raise Invalid("Missing command evidence or answer")
    if started - {item["id"] for item, _ in commands}:
        raise Invalid("Unfinished started Codex action")
    observed, actions, identities = [], [], set()
    for (public, number), (private, key, private_line) in zip(commands, native):
        identity = public["id"]
        if identity in identities:
            raise Invalid("Duplicate completed command")
        identities.add(identity)
        if (shlex.split(public["command"]) != private["command"] or
                public["exit_code"] != private["exit_code"] or
                public["aggregated_output"] != private["aggregated_output"]):
            raise Invalid("Command event correlation mismatch")
        prohibited = prohibited_command(private["command"])
        cwd = command_cwd(private, workspace)
        read = None if prohibited else command_read(private["command"], workspace, cwd)
        allowed_exit = {0, 1} if command_words(private["command"])[0] == "rg" else {0}
        if public["exit_code"] not in allowed_exit and not prohibited:
            raise Invalid("Failed read command")
        actions.append({"id": identity, "name": "command_execution", "command": public["command"],
                        "violation": prohibited, "assessed": True, "evidence": f"stdout:{number};rollout:{private_line}"})
        if read:
            path, first, lines = read
            wanted = "\n".join(lines)
            if wanted and wanted in public["aggregated_output"] and any(wanted in t for t in calls[key]["texts"]):
                observed.append({"path": path.relative_to(workspace).as_posix(),
                                 "lines": list(range(first, first + len(lines))),
                                 "evidence": f"stdout:{number};outer-call:{key}"})
            else:
                # Partial output can establish receipt of an individual required span.
                for span in spans:
                    needle = "\n".join(span["lines"])
                    if (span["path"] == path.relative_to(workspace).as_posix()
                            and first <= span["first_line"]
                            and span["first_line"] + len(span["lines"]) <= first + len(lines)
                            and needle in public["aggregated_output"]
                            and any(needle in t for t in calls[key]["texts"])):
                        observed.append({"path": span["path"],
                                         "lines": list(range(span["first_line"], span["first_line"] + len(span["lines"]))),
                                         "evidence": f"stdout:{number};outer-call:{key}"})
    return {"answer": answers[-1], "model": profile["model"], "effort_requested": profile["effort"],
            "effort_evidence": "retained client turn_context", "usage": terminal.get("usage"),
            "cost_usd": None, "warnings": warnings, "actions": actions, "permission_denials": [], "action_violation": any(a["violation"] for a in actions),
            "receipt": receipt(spans, observed)}
