#!/usr/bin/python3
"""XFCE tray client for loopback Mattermost notification reports."""
import json
from pathlib import Path
import tempfile
import threading
import urllib.error
import urllib.request


API_URL = "http://127.0.0.1:8000/mattermost/notifications"
MATTERMOST_URL = "http://mattermost.khomp.corp/"
STATES = {
    "idle": ("#9399a2", "Mattermost: nenhuma notificação"),
    "unread": ("#237cc5", "Mattermost: mensagens não lidas"),
    "mention": ("#dc3545", "Mattermost: menção ou mensagem privada"),
    "unknown": ("#c58c22", "Mattermost: sem comunicação com o navegador"),
}


def read_state():
    request = urllib.request.Request(API_URL, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=3) as response:
        data = json.loads(response.read(4096))
    if not isinstance(data, dict) or data.get("state") not in STATES:
        raise ValueError("Invalid notification response")
    return data["state"]


def icon_svg(color, unavailable=False):
    mark = ('<text x="16" y="24" text-anchor="middle" fill="white" '
            'font-family="sans-serif" font-weight="bold" font-size="23">?</text>'
            if unavailable else
            '<path d="M8 22V10h3l5 7 5-7h3v12h-3v-7l-5 7-5-7v7z" fill="white"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" '
            f'viewBox="0 0 32 32"><circle cx="16" cy="16" r="15" fill="{color}"/>'
            f'{mark}</svg>')


def main():
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("AyatanaAppIndicator3", "0.1")
    from gi.repository import AyatanaAppIndicator3, GLib, Gtk

    with tempfile.TemporaryDirectory(prefix="mattermost-tray-") as directory:
        icons = {}
        for state, (color, _) in STATES.items():
            path = Path(directory) / f"mattermost-{state}.svg"
            path.write_text(icon_svg(color, state == "unknown"))
            icons[state] = str(path)

        indicator = AyatanaAppIndicator3.Indicator.new(
            "mattermost-tray", icons["unknown"],
            AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )
        indicator.set_title("Mattermost")
        indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)
        menu = Gtk.Menu()
        status_item = Gtk.MenuItem(label=STATES["unknown"][1])
        status_item.set_sensitive(False)
        menu.append(status_item)
        open_item = Gtk.MenuItem(label="Abrir Mattermost")
        open_item.connect("activate", lambda _: Gtk.show_uri_on_window(
            None, MATTERMOST_URL, Gtk.get_current_event_time()))
        menu.append(open_item)
        quit_item = Gtk.MenuItem(label="Sair")
        quit_item.connect("activate", lambda _: Gtk.main_quit())
        menu.append(quit_item)
        menu.show_all()
        indicator.set_menu(menu)
        stop = threading.Event()

        def display(state, description):
            indicator.set_icon_full(icons[state], description)
            indicator.set_label("", "")
            status_item.set_label(description)
            return False

        def poll():
            previous = None
            while not stop.is_set():
                try:
                    state = read_state()
                    description = STATES[state][1]
                except (OSError, ValueError, TypeError, urllib.error.URLError):
                    state = "unknown"
                    description = "Mattermost: servidor local indisponível"
                current = (state, description)
                if current != previous:
                    GLib.idle_add(display, *current)
                    previous = current
                stop.wait(2)

        worker = threading.Thread(target=poll, name="mattermost-tray-poll", daemon=True)
        worker.start()
        try:
            Gtk.main()
        finally:
            stop.set()
            worker.join(timeout=4)


if __name__ == "__main__":
    main()
