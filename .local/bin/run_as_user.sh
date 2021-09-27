#!/bin/bash
# set -x

pushd `dirname $0` > /dev/null
SCRIPT_FOLDER_PATH=`pwd`
popd > /dev/null

creating_user=no;
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
            if [ "$?" != "0" ];
            then
                read -p "Error: Running command on new terminal. Press 'Enter' to continue...\\n" variable1
                exit 1
            fi
            exit 0
        fi
    done

    read -p "Error: No valid terminal found! Press 'Enter' to continue..." variable1
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
    creating_user=yes;
    printf "Creating destine user %s\\n" "$DESTINE_USER"
    run sudo useradd --groups "${SOURCE_GROUPS}" --shell "${SOURCE_SHELL}" --create-home "${DESTINE_USER}"
    run sudo passwd "${DESTINE_USER}"

    # Fix the new user not being able to access the files from other users
    # https://www.digitalocean.com/community/tutorials/how-to-create-a-new-sudo-enabled-user-on-ubuntu-20-04-quickstart
    run sudo usermod -aG sudo "$DESTINE_USER"
fi

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

# Fix new files permissions for new unzip files:
# setfacl -R -d -m g::rwX /somedir
# https://unix.stackexchange.com/questions/1314/how-to-set-default-file-permissions-for-all-folders-files-in-a-directory

runset command_line printf '%q ' "${@:3}"
printf "%s command_line: '%s'\\n" "${0}" "${command_line}";

# read -p var;
run sudo runuser "$DESTINE_USER" --command "$command_line"

# To allow a user directory to be accessed by other users
# https://askubuntu.com/questions/487527/give-specific-user-permission-to-write-to-a-folder-using-w-notation
newuserhome="$(getent passwd "$DESTINE_USER" | cut -d : -f 6)"
run sudo runuser "$DESTINE_USER" --command "sudo chmod -f -R g+rw '$newuserhome' || cd ."
run sudo runuser "$DESTINE_USER" --command "sudo chmod -f -R go+rw '$newuserhome' || cd ."
run sudo runuser "$SOURCE_USER" --command "sudo chmod -f -R g+rw '$newuserhome' || cd ."
run sudo runuser "$SOURCE_USER" --command "sudo chmod -f -R go+rw '$newuserhome' || cd ."

if [[ "w$creating_user" == "wyes" ]]
then
    # Remove user and its group
    # https://linuxize.com/post/how-to-delete-users-in-linux-using-the-userdel-command/
    # https://askubuntu.com/questions/233668/rm-cannot-remove-run-user-root-gvfs-is-a-directory
    # sudo umount /home/username/.cache/gvfs
    # sudo umount /home/username/.cache/doc
    # userdel -r username
    # groupdel username
    #
    # To rename a user
    # https://serverfault.com/questions/437342/how-can-i-rename-an-unix-user
    # usermod --login newusername --move-home --home /home/newusername oldusername
    # groupmod --new-name newusername oldusername
    read -p "Created a new user successfully. Press 'Enter' to continue" variable1
fi

printf "Exiting %s...\\n" "$0"
exit 0

