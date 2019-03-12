#!/usr/bin/env bash
# run it with /home/evandro/Documents/Programs/open_maximized.sh "Sublime Text" /usr/bin/subl -n
command_line=$(printf '%q ' "${@:2}")
eval "$command_line"

# https://unix.stackexchange.com/questions/264684/maximize-window-without-window-manager
while [ true ]
do
    FocusApp=`xdotool getwindowfocus getwindowname`

    if [[ "$FocusApp" == *"$1"* ]];
    then
        # xdotool key super+Up
        wmctrl -ir $(xdotool getactivewindow) -b add,maximized_vert,maximized_horz
        break
    fi

    sleep 0.5
done

