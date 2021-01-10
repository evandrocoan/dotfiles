#!/bin/bash
# set -x

pushd `dirname $0` > /dev/null
SCRIPT_FOLDER_PATH=`pwd`
popd > /dev/null

source "${SCRIPT_FOLDER_PATH}/_generic_installer.sh";


function print_usage() {
    printf "\\n"
    printf "Installation: \\n"
    printf "    chmod +x \\n" "$0"
    printf "\\n"
    printf "Optionally:\\n"
    printf "    sudo chmod go+rwx -R ~/\\n"
    printf "    sudo chmod go+rwx -R /home/username/\\n"
    printf "\\n"
    printf "Usage: \\n"
    printf "    %s username commandline\\n" "$0"
    read -p "Press 'Enter' to continue..." variable1
    exit 1
}
rerunnow="rerunnow"
target_user="$2"

# Open a terminal window to ask for the sudo password
if [ "$1" != "$rerunnow" ]
then
    full_command_line="$0 $rerunnow $(printf '%q ' "${@:1}")"

    declare -a available_terminals=(
            "xfce4-terminal --maximize --command"
            "gnome-terminal --maximize -- /bin/bash -c"
            "terminator --maximise -e"
            "konsole -e /bin/bash -c"
            "xterm -maximize -e"
        )

    for current_command in "${available_terminals[@]}"
    do
        current_terminal=$(printf "%s" "$current_command" | head -n1 | cut -d " " -f1)
        printf "current_terminal: %s, current_command: %s\\n" "$current_terminal" "$current_command"

        if command -v "$current_terminal" >/dev/null 2>&1; then
            $current_command "$full_command_line"
            exit 0
        fi
    done

    printf "Error: No valid terminal found!\\n"
    read -p "Press 'Enter' to continue..." variable1
    exit 1
fi


SOURCE_USER="$USER"
DESTINE_USER="$target_user"

id -u "$SOURCE_USER" > /dev/null 2>&1


if [ "$?" != "0" ] || [ -z "$SOURCE_USER" ]
then
    printf "Error: Invalid source user '%s'\\n" "$SOURCE_USER"
    print_usage
fi

if [ -z "$DESTINE_USER" ]
then
    printf "Error: Invalid destine user '%s'\\n" "$DESTINE_USER"
    print_usage
fi


SOURCE_GROUPS=$(id -Gn "${SOURCE_USER}" | sed "s/${SOURCE_USER} //g" | sed "s/ ${SOURCE_USER}//g" | sed "s/ /,/g")
SOURCE_SHELL=$(awk -F : -v name="${SOURCE_USER}" '(name == $1) { print $7 }' /etc/passwd)

id -u "$DESTINE_USER" > /dev/null 2>&1


if [ "$?" != "0" ]
then
    printf "Creating destine user %s\\n" "$DESTINE_USER"
    run sudo useradd --groups "${SOURCE_GROUPS}" --shell "${SOURCE_SHELL}" --create-home "${DESTINE_USER}"
    run sudo passwd "${DESTINE_USER}"

    # Fix the new user not being able to access the files from other users
    # https://www.digitalocean.com/community/tutorials/how-to-create-a-new-sudo-enabled-user-on-ubuntu-20-04-quickstart
    run sudo usermod -aG sudo "$DESTINE_USER"

else
    printf "Updating destine user '%s' with groups '%s' and shell '%s'\\n" "$DESTINE_USER" "$SOURCE_GROUPS" "$SOURCE_SHELL"
    run xhost "+si:localuser:$DESTINE_USER"
    sudo useradd -G "$DESTINE_USER" "$SOURCE_USER"
    sudo useradd -G "$SOURCE_USER" "$DESTINE_USER"

    run sudo usermod -a -G "$DESTINE_USER" "$SOURCE_USER"
    run sudo usermod -a -G "$SOURCE_USER" "$DESTINE_USER"
    run sudo usermod -a -G "$SOURCE_GROUPS" "$DESTINE_USER"
    run sudo chsh -s "$SOURCE_SHELL" "$SOURCE_USER"

    # Fix the new user not being able to access the files from other users
    # https://www.digitalocean.com/community/tutorials/how-to-create-a-new-sudo-enabled-user-on-ubuntu-20-04-quickstart
    run sudo usermod -aG sudo "$DESTINE_USER"
fi


runset command_line printf '%q ' "${@:3}"
printf "%s command_line: '%s'\\n" "${0}" "${command_line}";

# This one is not working when the command line had path names with `\ ` escaped spaces!
# https://askubuntu.com/questions/294736/run-a-shell-script-as-another-user-that-has-no-password
# run sudo -H -u "$DESTINE_USER" $command_line

# read -p var;
run sudo runuser "$DESTINE_USER" --command "$command_line"

# read -p "Press 'Enter' to continue" variable1
printf "Exiting %s...\\n" "$0"
exit 0

