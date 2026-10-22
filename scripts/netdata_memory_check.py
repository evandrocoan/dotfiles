#!/usr/bin/env python3
"""Notify from Netdata swap history and its anonymous-memory capacity counters."""
import argparse
import fcntl
import html
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request


def capacity(cgroup):
    stat = dict(line.split() for line in (cgroup / "memory.stat").read_text().splitlines())
    demand = int(stat["anon"]) + int((cgroup / "memory.swap.current").read_text())
    high = (cgroup / "memory.high").read_text().strip()
    limit = None if high == "max" else int(high)
    if demand < 0 or (limit is not None and limit <= 0):
        raise ValueError("invalid capacity counters")
    return {"anonymous_plus_swap_bytes": demand,
            "demand_ratio": demand / limit if limit is not None else None,
            "limit_status": "unlimited" if limit is None else "bounded"}


class LocalAPI:
    def __init__(self, base):
        parsed = urllib.parse.urlsplit(base)
        if (parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "localhost", "::1")
                or parsed.username or parsed.password or parsed.path not in ("", "/")
                or parsed.query or parsed.fragment):
            raise ValueError("Netdata URL must be a loopback HTTP origin")
        self.base = base.rstrip("/")
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def get(self, version, parameters):
        url = self.base + f"/api/{version}/data?" + urllib.parse.urlencode(parameters)
        with self.opener.open(url, timeout=3) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError("Netdata response exceeds size limit")
        result = json.loads(raw)
        if not isinstance(result, dict):
            raise ValueError("invalid Netdata response")
        return result


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def series(document, identifier, before, *, v2=False):
    result = document["result"] if v2 else document
    labels = document["view"]["dimensions"]["ids"] if v2 else result["labels"][1:]
    if len(labels) != len(set(labels)) or identifier not in labels:
        raise ValueError(f"missing or duplicate series: {identifier}")
    column = labels.index(identifier) + 1
    data = result["data"]
    if len(data) != 12:
        raise ValueError("incomplete historical window")
    rows = {}
    for row in data:
        stamp, value = row[0], row[column]
        if (stamp in rows or not isinstance(value, (int, float))
                or isinstance(value, bool) or not math.isfinite(value)):
            raise ValueError("invalid or missing historical point")
        rows[stamp] = value
    expected = [before - n * 10 for n in reversed(range(12))]
    if set(rows) != set(expected):
        raise ValueError("stale or gapped historical window")
    return [rows[stamp] for stamp in expected]


def windows(values):
    return [sum(values[:6]) / 6, sum(values[6:]) / 6]


def attribution(api, parameters, before):
    result = {"status": "unavailable", "groups": []}
    try:
        coverage = api.get("v1", {**parameters, "chart": "hostswap.coverage"})
        coverage_history = {key: series(coverage, key, before)
                            for key in ("tracked", "measured", "errors", "truncated")}
        if any(value < 0 for values in coverage_history.values() for value in values):
            raise ValueError("invalid collection coverage")
        counts = {key: values[-1] for key, values in coverage_history.items()}
        window_partial = any(coverage_history["errors"][i] or coverage_history["truncated"][i]
                             or coverage_history["measured"][i] < coverage_history["tracked"][i]
                             for i in range(12))
        data = api.get("v2", {**parameters, "contexts": "hostswap.cgroup_io",
                              "group_by": "label,dimension", "group_by_label": "cgroup_path"})
        identifiers = data["view"]["dimensions"]["ids"]
        if len(identifiers) > 1024:
            raise ValueError("too many cgroup series")
        candidates, missing = {}, 0
        for identifier in identifiers:
            direction, label = identifier.split(",", 1)
            if direction not in ("in", "out") or not label.startswith("p") or len(label) > 2048:
                raise ValueError("invalid cgroup series identity")
            path = os.fsdecode(bytes.fromhex(label[1:]))
            if not path.startswith("/"):
                raise ValueError("invalid cgroup path")
            if any(part in (".", "..") for part in path.split("/")):
                raise ValueError("invalid cgroup path")
            try:
                rates = series(data, identifier, before, v2=True)
                if min(rates) < 0:
                    raise ValueError("negative cgroup swap rate")
            except ValueError:
                missing += 1
                continue
            candidates.setdefault(path, {})[direction] = sum(rates) / len(rates) * 1024
        ranked = sorted(((path, rates) for path, rates in candidates.items()
                         if len(rates) == 2 and max(rates.values()) > 0),
                        key=lambda item: max(item[1].values()), reverse=True)
        selected = []
        for path, rates in ranked:
            if any(path.startswith(other["path"] + "/") or other["path"].startswith(path + "/")
                   for other in selected):
                continue
            selected.append({"path": path, "in_bytes_per_second": rates["in"],
                             "out_bytes_per_second": rates["out"]})
            if len(selected) == 3:
                break
        partial = bool(window_partial or missing)
        return {"status": "partial" if partial else "measured", "coverage": counts,
                "window_partial": bool(window_partial),
                "incomplete_series": missing, "groups": selected}
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        return {**result, "error": str(error)}


def historical(api, before, threshold):
    parameters = {"after": before - 120, "before": before, "points": 12,
                  "format": "json", "group": "average", "options": "natural-points"}
    swap = api.get("v1", {**parameters, "chart": "mem.swapio"})
    incoming = series(swap, "in", before)
    outgoing = [abs(value) for value in series(swap, "out", before)]
    if min(incoming) < 0:
        raise ValueError("negative host swap-in rate")
    in_windows = windows([value * 1024 for value in incoming])
    out_windows = windows([value * 1024 for value in outgoing])
    sustained = min(in_windows) >= threshold or min(out_windows) >= threshold
    result = {"status": "measured", "sustained": sustained, "before": before,
              "swap_in_windows_bytes_per_second": in_windows,
              "swap_out_windows_bytes_per_second": out_windows,
              "psi_some_percent": None}
    try:
        pressure = api.get("v1", {**parameters, "chart": "system.memory_some_pressure"})
        psi = series(pressure, "some 60", before)[-1]
        if not 0 <= psi <= 100:
            raise ValueError("invalid PSI percentage")
        result["psi_some_percent"] = psi
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        result["pressure_error"] = str(error)
    # Group history is fetched only for a qualifying warning, not on every quiet check.
    if sustained:
        result["attribution"] = attribution(api, parameters, before)
    return result


def save_state(path, data):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, prefix=".netdata-", delete=False) as stream:
            temporary = Path(stream.name)
            os.fchmod(stream.fileno(), 0o600)
            json.dump(data, stream)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def check(args):
    args.state.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    lock_fd = os.open(args.state.with_suffix(".lock"), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(lock_fd, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"status": "already-running"}, 0
        now = time.monotonic()
        boot = args.boot_id.read_text().strip()
        state, reset = {}, False
        try:
            state = json.loads(args.state.read_text())
            if not isinstance(state, dict) or state.get("version") not in (1, 2):
                raise ValueError("invalid state version")
        except FileNotFoundError:
            pass
        except (ValueError, TypeError):
            state, reset = {}, True
        old_boot = state.get("boot", state.get("sample", {}).get("boot")
                             if isinstance(state.get("sample"), dict) else None)
        alerts = state.get("alerts", {})
        if (old_boot != boot or not isinstance(alerts, dict)
                or any(not isinstance(value, (int, float)) or not math.isfinite(value)
                       or value < 0 or value > now for value in alerts.values())):
            alerts = {}
        errors, conditions = {}, []
        try:
            host = historical(LocalAPI(args.netdata_url), int(time.time() // 10) * 10 - 10,
                              args.swap_threshold)
            if host["sustained"]:
                conditions.append("host-swap")
        except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
            host = {"status": "unavailable", "error": str(error)}
            errors["history"] = str(error)
        try:
            cgroup = args.cgroup
            if cgroup is None:
                relative = subprocess.run(
                    ["systemctl", "show", "netdata.service", "--property=ControlGroup", "--value"],
                    check=True, capture_output=True, text=True, timeout=3).stdout.strip()
                if not relative.startswith("/") or ".." in Path(relative).parts:
                    raise ValueError("Netdata has no active cgroup")
                cgroup = Path("/sys/fs/cgroup") / relative.lstrip("/")
            demand = capacity(cgroup)
            if demand["demand_ratio"] is not None and demand["demand_ratio"] >= args.demand_threshold:
                conditions.append("demand")
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
            demand = {"status": "unavailable"}
            errors["capacity"] = str(error)
        sent, suppressed, failures = [], [], []
        for condition in conditions:
            repeat = args.repeat_seconds if condition == "demand" else args.host_repeat_seconds
            if condition in alerts and now - alerts[condition] < repeat:
                suppressed.append(condition)
                continue
            if condition == "host-swap":
                title = "Memória: atividade de swap elevada"
                body = (f"Swap sustentado por 2 minutos: entrada {host['swap_in_windows_bytes_per_second'][-1] / 1048576:.2f} "
                        f"MiB/s; saída {host['swap_out_windows_bytes_per_second'][-1] / 1048576:.2f} MiB/s.")
                psi = host["psi_some_percent"]
                body += (f" PSI de memória: {psi:.2f}%." if psi is not None else " PSI indisponível.")
                if psi is not None and psi >= 2:
                    body += " Há pressão de memória e possível thrashing."
                attribution_result = host["attribution"]
                for group in attribution_result["groups"]:
                    name = html.escape(group["path"][:180])
                    body += (f"\n{name}: entrada {group['in_bytes_per_second'] / 1048576:.2f}, "
                             f"saída {group['out_bytes_per_second'] / 1048576:.2f} MiB/s.")
                body += "\nMedição por grupo; não identifica cada PID."
                if attribution_result["status"] != "measured":
                    body += " Atribuição parcial ou indisponível."
            else:
                title = "Netdata: demanda de memória elevada"
                body = (f"Memória anônima + swap: {demand['demand_ratio']:.0%} do limite de pressão. "
                        "É um alerta de capacidade; não comprova thrashing ativo.")
            try:
                subprocess.run([args.notify_command, "-a", "netdata-memory-check", "-u", "normal", title, body],
                               check=True, capture_output=True, text=True, timeout=5)
            except (OSError, subprocess.SubprocessError):
                failures.append(condition)
            else:
                alerts[condition] = now
                sent.append(condition)
        save_state(args.state, {"version": 2, "boot": boot, "alerts": alerts})
        return {"status": "unavailable" if errors else "measured", "host": host, **demand,
                "conditions": conditions, "state_reset": reset, "sent": sent, "errors": errors,
                "suppressed": suppressed, "notification_failures": failures}, 2 if errors or failures else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--netdata-url", default="http://127.0.0.1:19999")
    parser.add_argument("--cgroup", type=Path, help="Capacity cgroup instead of resolving netdata.service")
    parser.add_argument("--state", type=Path, default=Path.home() / ".local/state/netdata-memory-check/state.json")
    parser.add_argument("--boot-id", type=Path, default=Path("/proc/sys/kernel/random/boot_id"))
    parser.add_argument("--notify-command", default="notify-send")
    parser.add_argument("--swap-threshold", type=float, default=1048576, help="Bytes/s in each 60-second window")
    parser.add_argument("--demand-threshold", type=float, default=0.85)
    parser.add_argument("--repeat-seconds", type=float, default=21600, help="Capacity warning cooldown")
    parser.add_argument("--host-repeat-seconds", type=float, default=900)
    args = parser.parse_args(argv)
    if (any(not math.isfinite(value) or value <= 0 for value in (
            args.swap_threshold, args.demand_threshold, args.repeat_seconds, args.host_repeat_seconds))
            or args.demand_threshold > 1):
        parser.error("thresholds and intervals must be positive; demand fraction must not exceed 1")
    try:
        result, status = check(args)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"Netdata measurement unavailable: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
