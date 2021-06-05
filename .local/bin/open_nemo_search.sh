#!/usr/bin/env bash
set -x

# https://unix.stackexchange.com/questions/264684/maximize-window-without-window-manager
function maximize() {

    while [[ true ]]
    do
        FocusApp=`xdotool getwindowfocus getwindowname`;
        active_window_id=$(xdotool getactivewindow)
        active_window_pid=$(xdotool getwindowpid "$active_window_id")
        
        # https://stackoverflow.com/questions/15545341/process-name-from-its-pid-in-linux
        process_name="$(cat /proc/${active_window_pid}/comm)"

        if [[ "$process_name" == "$program_name" ]];
        then
            xdotool key ctrl+f
            break;
        fi;

        sleep 0.5;
    done
}

program_name="nemo";

nemo_dir="$1";
"${program_name}" "${nemo_dir}" &

maximize &
