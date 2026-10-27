"""Exercise package identity/integrity checks using real disposable Debian packages."""

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("rebuild", Path(__file__).with_name("rebuild.py"))
rebuild = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rebuild)


class PackageVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.packages = self.root / "packages"
        self.packages.mkdir()
        self.records = []
        for source in rebuild.load_sources()["sources"].values():
            for package in source["packages"]:
                tree = self.root / package
                (tree / "DEBIAN").mkdir(parents=True)
                (tree / "DEBIAN/control").write_text(
                    f"Package: {package}\nVersion: {source['package_version']}\nArchitecture: amd64\n"
                    "Maintainer: Test <test@example.invalid>\nDescription: Disposable identity fixture\n"
                )
                target = self.packages / (package + ".deb")
                subprocess.run(["dpkg-deb", "--build", "--root-owner-group", str(tree), str(target)],
                               check=True, stdout=subprocess.PIPE)
                self.records.append(dict(Package=package, Version=source["package_version"],
                                         Architecture="amd64", file=target.name,
                                         sha256=rebuild.sha256(target)))
        self.save_manifest()

    def save_manifest(self):
        (self.packages / "manifest.json").write_text(json.dumps(self.records))

    def test_exact_native_package_set(self):
        paths = rebuild.verify_packages(self.packages)
        self.assertEqual({rebuild.package_fields(p)["Package"] for p in paths},
                         {r["Package"] for r in self.records})

    def test_changed_payload_is_rejected(self):
        record = self.records[0]
        tree = self.root / record["Package"]
        (tree / "changed-content").write_text("valid package, different payload")
        subprocess.run(["dpkg-deb", "--build", "--root-owner-group", str(tree),
                        str(self.packages / record["file"])], check=True, stdout=subprocess.PIPE)
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            rebuild.verify_packages(self.packages)

    def test_extra_package_is_rejected(self):
        (self.packages / "unlisted.deb").write_bytes(b"not selected")
        with self.assertRaisesRegex(ValueError, "unlisted Debian package"):
            rebuild.verify_packages(self.packages)

    def test_missing_identity_is_rejected(self):
        self.records.pop()
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "exact repair package set"):
            rebuild.verify_packages(self.packages)

    def test_manifest_cannot_relabel_native_package(self):
        self.records[0]["Version"] = "0.0-original"
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "payload identity differs"):
            rebuild.verify_packages(self.packages, rollback=True)

    def test_package_symlink_is_rejected(self):
        target = self.packages / self.records[0]["file"]
        moved = self.root / "outside.deb"
        target.rename(moved)
        target.symlink_to(moved)
        with self.assertRaisesRegex(ValueError, "not a regular local file"):
            rebuild.verify_packages(self.packages)

    def test_cached_corrupt_source_never_reaches_extraction(self):
        cache = self.root / "cache"
        cache.mkdir()
        (cache / "source.dsc").write_bytes(b"wrong archive")
        builder = rebuild.Builder(self.root, [cache])
        source = dict(archives=[dict(file="source.dsc", sha256="0" * 64)], patches=[])
        with patch.object(builder, "container") as container:
            with self.assertRaisesRegex(ValueError, "source checksum mismatch"):
                builder.extract("bad-source", source, "unused-image")
        container.assert_not_called()

    def test_snapshot_preserves_exact_cached_installed_packages(self):
        original_check_output = subprocess.check_output
        by_name = {r["Package"]: r for r in self.records}

        def installed_or_native(args, **kwargs):
            if args[0] == "dpkg-query":
                record = by_name[args[-1]]
                return f"install ok installed\n{record['Version']}\n{record['Architecture']}"
            return original_check_output(args, **kwargs)

        destination = self.root / "snapshot"
        with patch.object(rebuild.subprocess, "check_output", side_effect=installed_or_native):
            rebuild.snapshot(destination, [self.packages])
        self.assertEqual({p.name: rebuild.sha256(p) for p in rebuild.verify_packages(destination, True)},
                         {r["file"]: r["sha256"] for r in self.records})


if __name__ == "__main__":
    unittest.main()
