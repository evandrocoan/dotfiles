"""Export native Debian build outputs with machine-readable package identities."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def main():
    target = Path("/packages")
    target.mkdir()
    records = []
    for source in sorted(Path("/build").iterdir()):
        if source.suffix not in (".deb", ".ddeb", ".buildinfo", ".changes") or not source.is_file():
            continue
        destination = target / source.name
        shutil.copyfile(source, destination)
        if source.suffix in (".deb", ".ddeb"):
            fields = subprocess.check_output(
                ["dpkg-deb", "-f", str(source), "Package", "Version", "Architecture"], text=True
            )
            record = dict(line.split(": ", 1) for line in fields.splitlines())
            record.update(file=source.name, sha256=hashlib.sha256(source.read_bytes()).hexdigest())
            records.append(record)
    if not records:
        raise SystemExit("native package build produced no Debian packages")
    (target / "manifest.json").write_text(json.dumps(records, indent=2) + "\n")


if __name__ == "__main__":
    main()
