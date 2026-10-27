"""Version an authenticated, already built source tree for local Debian packaging."""

from pathlib import Path
import re
import sys


package, base_version, version = sys.argv[1:]
reasons = {
    "gcr": "Ensure single terminal completion and discard closed system prompts.",
    "gnome-keyring": "Return D-Bus errors when OpenSession negotiation fails.",
}
if package not in reasons or version != base_version + "+keyringfix1":
    raise SystemExit("unexpected source package or local version")
path = Path("debian/changelog")
original = path.read_text()
match = re.match(r"([^ ]+) \(([^)]+)\)", original)
if match is None or match.groups() != (package, base_version):
    raise SystemExit("source changelog does not match the authenticated build base")
header = (
    f"{package} ({version}) noble; urgency=medium\n\n"
    f"  * Local source repair: {reasons[package]}\n\n"
    " -- Local build <local@localhost>  Tue, 27 Oct 2026 00:53:40 -0300\n\n"
)
path.write_text(header + original)
