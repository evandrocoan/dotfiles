"""Version an authenticated, already built source tree for local Debian packaging."""

from pathlib import Path
import re
import sys


package, base_version, version = sys.argv[1:]
reasons = {
    "gcr": ("+keyringfix1",
            "Ensure single terminal completion and discard closed system prompts.",
            "Tue, 27 Oct 2026 00:53:40 -0300"),
    "gnome-keyring": ("+keyringfix2",
                      "Handle failed OpenSession negotiation and keep unlock requests progressing.",
                      "Fri, 30 Oct 2026 00:00:00 -0300"),
}
if package not in reasons or version != base_version + reasons[package][0]:
    raise SystemExit("unexpected source package or local version")
path = Path("debian/changelog")
original = path.read_text()
match = re.match(r"([^ ]+) \(([^)]+)\)", original)
if match is None or match.groups() != (package, base_version):
    raise SystemExit("source changelog does not match the authenticated build base")
header = (
    f"{package} ({version}) noble; urgency=medium\n\n"
    f"  * Local source repair: {reasons[package][1]}\n\n"
    f" -- Local build <local@localhost>  {reasons[package][2]}\n\n"
)
path.write_text(header + original)
