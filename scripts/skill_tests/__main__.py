"""Explicit offline, preparation, live, grading and reporting operations."""

import argparse
import json
from pathlib import Path
import sys

from .common import Invalid, digest, json_bytes, read_json, write_new
from .protocol import cases, prepare
from .reporting import export, grade, report
from .runner import execute, preflight
from .structure import check_repository


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="Offline checks of repository-owned skill structure")
    check.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    commands.add_parser("cases", help="Validate/list corpus without running models")
    prep = commands.add_parser("prepare", help="Freeze a new private round; does not run inference")
    prep.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    prep.add_argument("--output", type=Path, required=True)
    prep.add_argument("--baseline", type=Path)
    prep.add_argument("--repeat", type=int, default=2)
    prep.add_argument("--ceiling", type=int, default=12)
    prep.add_argument("--case", action="append")
    pre = commands.add_parser("preflight", help="Build and inspect client startup without inference")
    pre.add_argument("round", type=Path)
    run = commands.add_parser("run", help="Launch authorized cells after review; consumes model usage")
    run.add_argument("round", type=Path)
    run.add_argument("--reviewed-manifest", required=True)
    run.add_argument("--reviewed-preflight", required=True)
    run.add_argument("--count", type=int, default=1)
    grades = commands.add_parser("grade", help="Import complete manual grades backed by answer quotes")
    grades.add_argument("round", type=Path)
    grades.add_argument("run_id")
    grades.add_argument("input", type=Path)
    show = commands.add_parser("report", help="Write a private candidate or print status/counts")
    show.add_argument("round", type=Path)
    show.add_argument("--private-output", type=Path)
    share = commands.add_parser("export", help="Export only a reviewed, screened candidate")
    share.add_argument("round", type=Path)
    share.add_argument("--output", type=Path, required=True)
    share.add_argument("--reviewed-content", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            result = check_repository(args.repo)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return int(bool(result["errors"]))
        if args.command == "cases":
            print(json.dumps({key: {"kind": value["kind"], "initial_live": value["initial_live"]}
                              for key, value in cases().items()}, indent=2))
        elif args.command == "prepare":
            print(prepare(args.repo, args.output, baseline=args.baseline, repeats=args.repeat,
                          ceiling=args.ceiling, case_ids=args.case))
        elif args.command == "preflight":
            print(preflight(args.round))
        elif args.command == "run":
            execute(args.round, args.reviewed_manifest, args.reviewed_preflight, args.count)
        elif args.command == "grade":
            grade(args.round, args.run_id, read_json(args.input))
        elif args.command == "report":
            candidate = report(args.round)
            if args.private_output:
                if args.private_output.resolve().is_relative_to(args.round.resolve() / "prepared"):
                    raise Invalid("Private report cannot enter client inputs")
                write_new(args.private_output, candidate)
            print(json.dumps({"status": candidate["status"], "scheduled": candidate["scheduled"],
                              "started": candidate["started"], "candidate_sha256": digest(json_bytes(candidate))}))
            return candidate["exit_code"]
        elif args.command == "export":
            return export(args.round, args.output, args.reviewed_content)
        return 0
    except (Invalid, OSError, ValueError, KeyError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
