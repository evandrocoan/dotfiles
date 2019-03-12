#!/bin/bash
# To list active windows use `wmctrl -lx`
window_title="$1"
key_to_send="$2"

active_window=$(xdotool getactivewindow)
target_window=$(xdotool search --limit 1 --all --pid $(pgrep "$window_title"))

# xdotool key --window "$target_window" "$key_to_send"
wmctrl -x -a "$window_title" &&
sleep 0.5 &&
xdotool key "$key_to_send" &&
xdotool windowactivate "$active_window" &&
printf "%s Done!\\n" "$0"
