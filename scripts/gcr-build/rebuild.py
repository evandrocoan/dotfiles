#!/usr/bin/env python3
"""Rebuild the pinned GNOME Keyring/GCR repairs without installing host packages."""

import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import urllib.request
import uuid


HERE = Path(__file__).resolve().parent
KEYRING = HERE.parent / "gnome-keyring-build"


def sha256(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def load_sources():
    return json.loads((HERE / "sources.json").read_text())


def package_fields(path):
    fields = subprocess.check_output(
        ["dpkg-deb", "-f", str(path), "Package", "Version", "Architecture"], text=True
    )
    return dict(line.split(": ", 1) for line in fields.splitlines())


def verify_packages(directory, rollback=False):
    directory = directory.resolve(strict=True)
    records = json.loads((directory / "manifest.json").read_text())
    expected = {
        package: source["package_version"]
        for source in load_sources()["sources"].values()
        for package in source["packages"]
    }
    if len(records) != len(expected) or {r["Package"] for r in records} != set(expected):
        raise ValueError("package manifest does not contain the exact repair package set")
    files = []
    for record in records:
        filename = record["file"]
        if Path(filename).name != filename or not filename.endswith(".deb"):
            raise ValueError("package filename must be a plain .deb basename")
        path = directory / filename
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"package is not a regular local file: {filename}")
        if (not rollback and record["Version"] != expected[record["Package"]]) or record["Architecture"] != "amd64":
            raise ValueError(f"unexpected package version or architecture: {filename}")
        if sha256(path) != record["sha256"]:
            raise ValueError(f"package checksum mismatch: {filename}")
        if package_fields(path) != {k: record[k] for k in ("Package", "Version", "Architecture")}:
            raise ValueError(f"package payload identity differs from manifest: {filename}")
        files.append(path)
    if {p.name for p in directory.glob("*.deb")} != {p.name for p in files}:
        raise ValueError("unlisted Debian package in selected package directory")
    return files


def snapshot(output, caches):
    """Preserve the exact installed package group before a later manual APT transaction."""
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    records = []
    names = [p for s in load_sources()["sources"].values() for p in s["packages"]]
    for name in names:
        installed = subprocess.check_output(
            ["dpkg-query", "-W", "-f=${Status}\\n${Version}\\n${Architecture}", name], text=True
        ).splitlines()
        if len(installed) != 3 or installed[0] != "install ok installed":
            raise ValueError(f"snapshot requires the existing repair group; {name} is not installed")
        identity = dict(Package=name, Version=installed[1], Architecture=installed[2])
        cached = None
        for cache in caches:
            for path in sorted(cache.iterdir()):
                if path.suffix in (".deb", ".ddeb") and path.is_file() and package_fields(path) == identity:
                    cached = path
                    break
            if cached:
                break
        if cached:
            target = output / cached.with_suffix(".deb").name
            shutil.copyfile(cached, target)
        else:
            subprocess.run(["apt-get", "download", f"{name}:{installed[2]}={installed[1]}"],
                           cwd=output, check=True)
            matches = [p for p in output.glob("*.deb") if package_fields(p) == identity]
            if len(matches) != 1:
                raise ValueError(f"download did not produce exactly one original {name} package")
            target = matches[0]
        records.append(dict(identity, file=target.name, sha256=sha256(target)))
    (output / "manifest.json").write_text(json.dumps(records, indent=2) + "\n")
    verify_packages(output, rollback=True)
    print(f"Original installed package group preserved: {output}")


class Builder:
    def __init__(self, output, caches):
        self.output = output.resolve()
        self.caches = caches
        self.prefix = "local/keyring-rebuild-" + uuid.uuid4().hex[:12]
        self.images = {}

    def command(self, args, label):
        log = self.output / (label + ".log")
        print(f"{label}: {log}", flush=True)
        with log.open("w") as stream:
            subprocess.run(args, stdout=stream, stderr=subprocess.STDOUT, check=True)

    def build_image(self, name, dockerfile, context, target=None, arguments=None):
        image = self.prefix + ":" + name
        args = ["docker", "build", "--progress=plain", "-t", image, "-f", str(dockerfile)]
        if target:
            args += ["--target", target]
        for key, value in (arguments or {}).items():
            args += ["--build-arg", f"{key}={value}"]
        args += [str(context)]
        self.command(args, name + "-build")
        self.images[name] = subprocess.check_output(
            ["docker", "image", "inspect", "--format", "{{.Id}}", image], text=True
        ).strip()
        return image

    def container(self, image, command, label, inputs=None, export=None):
        # No host mounts, real session environment, network, or extra capabilities.
        args = ["docker", "create", "--network=none", "--cap-drop=ALL",
                "--security-opt=no-new-privileges", "--ulimit", "core=0", "--pids-limit=512",
                "--user=1000:1000", "--env", "HOME=/tmp/keyring-rebuild-home",
                image, *command]
        cid = subprocess.check_output(args, text=True).strip()
        try:
            if inputs:
                subprocess.run(["docker", "cp", str(inputs) + "/.", cid + ":/tmp/inputs"], check=True)
            self.command(["docker", "start", "--attach", cid], label)
            status = subprocess.check_output(
                ["docker", "inspect", "--format", "{{.State.ExitCode}}", cid], text=True
            ).strip()
            if status != "0":
                raise ValueError(f"{label}: container exited with {status}")
            if export:
                source, destination = export
                subprocess.run(["docker", "cp", cid + ":" + source, str(destination)], check=True)
        finally:
            subprocess.run(["docker", "rm", "--force", cid], check=True, stdout=subprocess.PIPE)

    def extract(self, name, source, deps):
        inputs = self.output / (name + "-inputs")
        inputs.mkdir()
        for archive in source["archives"]:
            destination = inputs / archive["file"]
            cached = next((p / archive["file"] for p in self.caches
                           if (p / archive["file"]).is_file()), None)
            if cached:
                shutil.copyfile(cached, destination)
            else:
                print(f"download: {archive['url']}", flush=True)
                with urllib.request.urlopen(archive["url"], timeout=60) as response:
                    with destination.open("wb") as stream:
                        shutil.copyfileobj(response, stream)
            if sha256(destination) != archive["sha256"]:
                raise ValueError(f"source checksum mismatch: {archive['file']}")
        dsc = next(a["file"] for a in source["archives"] if a["file"].endswith(".dsc"))
        steps = [shlex.join(["dpkg-source", "--no-check", "-x", "/tmp/inputs/" + dsc,
                            "/tmp/source"]), "cd /tmp/source"]
        for number, patch in enumerate(source["patches"]):
            target = f"repair-{number}.patch"
            shutil.copyfile(HERE / patch, inputs / target)
            steps.append(f"patch --batch --fuzz=0 -p1 < /tmp/inputs/{target}")
        tree = self.output / name
        self.container(deps, ["timeout", "180", "sh", "-ec", " && ".join(steps)],
                       name + "-extract", inputs, ("/tmp/source", tree))
        shutil.copyfile(HERE / "source.dockerignore", tree / ".dockerignore")
        return tree

    def run(self):
        spec = load_sources()
        server = subprocess.check_output(
            ["docker", "version", "--format", "{{.Server.Os}}/{{.Server.Arch}}"], text=True
        ).strip()
        if server != "linux/" + spec["architecture"]:
            raise ValueError("this repair recipe supports a native Linux amd64 Docker daemon")
        self.output.mkdir(parents=True, exist_ok=False)
        # Copy only maintained packaging inputs; source trees are freshly authenticated/extracted.
        recipes = self.output / "recipes"
        recipes.mkdir()
        for name in ("packaging.Dockerfile", "package_changelog.py", "export_packages.py", ".dockerignore"):
            shutil.copyfile(HERE / name, recipes / name)
        deps = self.build_image("dependencies", KEYRING / "build.Dockerfile", recipes, "dependencies",
                                {"BASE_IMAGE": spec["base_image"]})
        gcr_deps = self.build_image("gcr-dependencies", HERE / "build.Dockerfile", recipes,
                                    "dependencies", {"KEYRING_DEPS_IMAGE": deps})
        sources = spec["sources"]
        gcr_tree = self.extract("gcr", sources["gcr"], gcr_deps)
        gcr = self.build_image("gcr", HERE / "build.Dockerfile", gcr_tree, "build",
                               {"KEYRING_DEPS_IMAGE": deps})
        self.container(gcr, ["timeout", "1800", "dbus-run-session", "--", "dh_auto_test",
                              "--max-parallel=2"], "gcr-tests")
        keyring_tree = self.extract("gnome-keyring", sources["gnome-keyring"], deps)
        keyring = self.build_image("keyring", KEYRING / "build.Dockerfile", keyring_tree, "build",
                                   {"BASE_IMAGE": spec["base_image"]})
        consumer = self.build_image("consumer", HERE / "consumer.Dockerfile", recipes,
                                    arguments={"GCR_IMAGE": gcr, "KEYRING_IMAGE": keyring})
        self.container(consumer, ["timeout", "1800", "dbus-run-session", "--", "dh_auto_test",
                                   "--max-parallel=2"], "keyring-tests")
        selected = self.output / "packages"
        selected.mkdir()
        records = []
        # The consumer only overlays GCR libraries for tests. Native shlibdeps must use
        # distribution package metadata, rather than its unpackaged LD_LIBRARY_PATH.
        for name, image in (("gcr", gcr), ("gnome-keyring", keyring)):
            source = sources[name]
            packaged = self.build_image(name + "-packages", recipes / "packaging.Dockerfile", recipes,
                                       arguments={"SOURCE_IMAGE": image, "SOURCE_PACKAGE": name,
                                                  "BASE_VERSION": source["version"],
                                                  "PACKAGE_VERSION": source["package_version"]})
            exported = self.output / (name + "-packages")
            self.container(packaged, ["/bin/true"], name + "-export",
                           export=("/packages", exported))
            available = json.loads((exported / "manifest.json").read_text())
            for package in source["packages"]:
                matches = [r for r in available if r["Package"] == package]
                if len(matches) != 1:
                    raise ValueError(f"native build must produce exactly one {package} package")
                record = matches[0]
                filename = Path(record["file"]).with_suffix(".deb").name
                shutil.copyfile(exported / record["file"], selected / filename)
                records.append(dict(record, file=filename))
        (selected / "manifest.json").write_text(json.dumps(records, indent=2) + "\n")
        verify_packages(selected)
        (self.output / "images.json").write_text(json.dumps(self.images, indent=2) + "\n")
        print(f"Build and native package tests passed. Verify/install instructions: {selected}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="authenticate, build, test and export; never installs")
    build.add_argument("--output", type=Path, default=HERE / "build" / "output",
                       help="new output directory (default: %(default)s)")
    build.add_argument("--source-cache", type=Path, action="append", default=[],
                       help="optional downloaded source directory; hashes are always checked")
    verify = commands.add_parser("verify", help="check the exact exported package set and hashes")
    verify.add_argument("directory", type=Path)
    verify.add_argument("--rollback", action="store_true", help="verify original saved versions")
    save = commands.add_parser("snapshot", help="save exact installed versions; never installs")
    save.add_argument("--output", type=Path, required=True, help="new rollback directory")
    save.add_argument("--cache", type=Path, action="append", default=[],
                      help="existing .deb/.ddeb directory to search before apt-get download")
    args = parser.parse_args()
    try:
        if args.command == "build":
            Builder(args.output, args.source_cache).run()
        elif args.command == "snapshot":
            snapshot(args.output, args.cache)
        else:
            files = verify_packages(args.directory, rollback=args.rollback)
            print(f"Verified {len(files)} repair packages.")
            print(shlex.join(["sudo", "apt-get", "--simulate", "--no-remove", "install", *map(str, files)]))
            print(shlex.join(["sudo", "apt-get", "--no-remove", "install", *map(str, files)]))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
