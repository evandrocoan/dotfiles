#!/bin/bash

echo "Restoring missing XFCE custom shortcuts..."

# Function to add or update an XFCE keyboard shortcut
add_shortcut() {
    local key="$1"
    local command="$2"
    local property="/commands/custom/$key"

    # Attempt to create the property (-n). If it already exists, update it instead (-s).
    xfconf-query -c xfce4-keyboard-shortcuts -p "$property" -n -t string -s "$command" 2>/dev/null || \
    xfconf-query -c xfce4-keyboard-shortcuts -p "$property" -s "$command"

    echo "Restored: $key -> $command"
}

# Function to add a boolean property (used for startup-notify)
add_bool_property() {
    local key="$1"
    local prop_name="$2"
    local property="/commands/custom/$key/$prop_name"

    xfconf-query -c xfce4-keyboard-shortcuts -p "$property" -n -t bool -s true 2>/dev/null || \
    xfconf-query -c xfce4-keyboard-shortcuts -p "$property" -s true
}

# --- 🎵 Music & Media Controls ---
# add_shortcut "<Alt><Super>KP_1" "wmctrl -x -a minilyrics.exe.Wine"
# add_shortcut "<Alt><Super>KP_0" "wmctrl -x -a aimp.exe.Wine"
# add_shortcut "<Alt><Super>Right" "play_stop_music.sh AIMP.exe key Ctrl+F2"
# add_shortcut "<Alt><Super>Left" "play_stop_music.sh AIMP.exe key Ctrl+F1"
# add_shortcut "<Alt><Super>Down" "play_stop_music.sh AIMP.exe key Ctrl+Down"
# add_shortcut "<Alt><Super>Up" "play_stop_music.sh AIMP.exe key Ctrl+Up"
# add_shortcut "Pause" "play_stop_music.sh AIMP.exe key Ctrl+space"

# --- 💻 Custom Scripts & Utilities ---
add_shortcut "<Primary><Alt>j" "SublimeTextMaximazed.sh"
add_shortcut "<Primary><Alt><Super>Down" "changexfce4dpi.sh down"
add_shortcut "<Primary><Alt><Super>Up" "changexfce4dpi.sh up"
add_shortcut "KP_Separator" "autokey-run -p insert_dot"

# --- 🚀 Third-Party Applications ---
add_shortcut "<Primary><Alt>ccedilla" "google-chrome --start-maximized --new-window"
add_shortcut "<Primary><Alt>o" "speedcrunch"
add_shortcut "<Primary><Alt>h" "ksysguard"
add_shortcut "<Primary>Print" "flameshot gui"
add_shortcut "<Shift>Print" "flameshot gui"
add_shortcut "<Alt>v" "copyq show"

# --- ⚙️ Alternative XFCE System Bindings ---
add_shortcut "<Super>l" "xflock4"
# add_shortcut "<Super>m" "xfce4-popup-whiskermenu"
add_shortcut "<Super>F1" "xfce4-popup-applicationsmenu"
add_shortcut "<Super>F2" "xfce4-appfinder --collapsed"
add_shortcut "<Super>F3" "xfce4-appfinder"

# Re-enable startup notifications for Appfinder shortcuts
add_bool_property "<Super>F2" "startup-notify"
add_bool_property "<Super>F3" "startup-notify"

echo "Done! All missing shortcuts have been successfully added to your active configuration."