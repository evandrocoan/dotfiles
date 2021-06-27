#!/bin/bash
# set -x

action="$1"
workspaces_count="$2"

if [[ "w${workspaces_count}" == "w" ]];
then
    workspaces_count="10";
fi

# https://askubuntu.com/questions/17484/is-there-a-way-to-detect-which-workspace-you-are-currently-in-from-the-command-l
current_desktop="$(xdotool get_desktop)"

# https://unix.stackexchange.com/questions/154546/how-to-get-window-id-from-xdotool-window-stack
active_window="$(xdotool getactivewindow)"

# https://askubuntu.com/questions/31240/how-to-shift-applications-from-workspace-1-to-2-using-command
# # https://superuser.com/questions/183680/gnome-ubuntu-how-to-bring-a-program-window-to-the-front-using-a-command-line
if [[ "${action}" == "next" ]];
then
    next_desktop="$(( (current_desktop + 1) % workspaces_count ))"
else
    if [[ "$(( current_desktop - 1 ))" -lt 0 ]];
    then
        next_desktop="$(( workspaces_count - 1 ))"
    else
        next_desktop="$(( (current_desktop - 1) % workspaces_count ))"
    fi
fi

# https://askubuntu.com/questions/59783/how-to-move-windows-to-another-workspace-without-switching-workspace
xdotool getactivewindow set_desktop_for_window "${next_desktop}"

# Move the window to the top on the target workspace
xdotool windowactivate "$active_window"

# Switch back to the current workspace
xdotool set_desktop "${current_desktop}"
