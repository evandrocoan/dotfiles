#!/bin/bash
run_more_quietly="v"

pushd `dirname $0` > /dev/null
SCRIPT_FOLDER_PATH=`pwd`
popd > /dev/null

function checkargsvalid() {
    argumentvalue="$2";
    if [[ "$argumentvalue" == '-'* ]];
    then
        argumentname="$1";
        printf 'Error: Invalid argument "%s" to "%s".\n' "${argumentvalue}" "${argumentname}";
        printhelp;
    fi
}

function check_expected_args() {
    argumentvalue="$2";
    if [[ "$argumentvalue" != '-'* ]];
    then
        argumentname="$1";
        printf 'Error: The command "%s" does not expect any arguments, but got "%s".\n' "${argumentname}" "${argumentvalue}";
        printhelp;
    fi
}

function printhelp() {
    set +x;
cat >&1 <<EOF

    Usage: bash ${0} ACTION [arguments]

    Run basic workflow setup programs.

    Note: It is not possible to tie togheter short options as '-b' and '-i' as '-bi';

    bash ${0} -v  | --verbose  (enable all verbose flags)
    bash ${0} -q  | --quiet  (do not pass -v to others)
EOF
    exit 1;
}

all_arguments=("$@");

while [[ "$#" -gt 0 ]];
do
    case ${1} in
        -h|--help)
            printhelp;
        ;;
        -v|--verbose)
            set -x;
            export DEBUG=1;
            export VERBOSE=1;
            check_expected_args "$1" "${2--}";
        ;;
        -q|--quiet)
            run_more_quietly="";
            check_expected_args "$1" "${2--}";
        ;;
        *)
            printf 'Error: Unknown parameter "%s".\n' "$1";
            printhelp;
        ;;
    esac;
    shift;
done;

function run_google_chrome() {
    home_dir="$HOME/chrome-ahgora";
    google-chrome --profile-directory="Ahgora" --user-data-dir="$home_dir";
}

# https://unix.stackexchange.com/questions/28181/how-to-run-a-script-on-screen-lock-unlock
dbus-monitor --session "type='signal',interface='org.xfce.ScreenSaver'" | \
( while true
    do read X
    if echo $X | grep "boolean true" &> /dev/null; then
        echo "locking at $(date)"
    elif echo $X | grep "boolean false" &> /dev/null; then
        echo "unlocking at $(date)";
        run_google_chrome;
        # running_processes="$(ps -ef | grep "$home_dir" | grep -v "grep" | wc -l)";
        # if [[ $running_processes -lt 2 ]];
        # then
        #     echo "running now $(date)";
        # fi;
    fi
done ) &
export foo_pid=$!
trap 'kill $foo_pid' EXIT

run_google_chrome;

sudo openfortivpn --persistent 5
