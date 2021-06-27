#!/bin/bash
# set -x

# To list active windows use `wmctrl -lx`
window_title="$1"
key_to_send=$(printf '%q ' "${@:2}")

source ~/.per_computer_settings.sh

if [[ "${key_to_send}" == *"Ctrl+space"* ]];
then
    # ssh "user@ip"
    ssh "$LOCAL_COMPUTER_SSH" 'schtasks //run //I //TN playpausemusicoverssh'
fi

# https://unix.stackexchange.com/questions/154546/how-to-get-window-id-from-xdotool-window-stack
active_window=$(xdotool getactivewindow)
target_window=$(xdotool search --limit 1 --all --pid $(pgrep "$window_title"))

# https://superuser.com/questions/183680/gnome-ubuntu-how-to-bring-a-program-window-to-the-front-using-a-command-line
# xdotool key --window "$target_window" "$key_to_send"
wmctrl -x -a "$window_title" &&
sleep 0.5 &&
xdotool $key_to_send &&
xdotool windowactivate "$active_window" &&
printf "Script '%s' sent '%s' to '%s'!\\n" "$0" "$key_to_send" "$window_title"
