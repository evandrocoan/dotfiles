#!/usr/bin/env bash
# run it with open_maximized.sh "Sublime Text" /usr/bin/subl -n

function maximize() {
    program_name="${1}";
    shift;

    # https://unix.stackexchange.com/questions/264684/maximize-window-without-window-manager
    while [ true ]
    do
        FocusApp=`xdotool getwindowfocus getwindowname`;

        if [[ "$FocusApp" == *"${program_name}"* ]];
        then
            # xdotool key super+Up
            wmctrl -ir $(xdotool getactivewindow) -b add,maximized_vert,maximized_horz;
            break;
        fi;

        sleep 0.5;
    done
}

program_name="${1}";
shift;

maximize "${program_name}" &
