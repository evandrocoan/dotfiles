#!/usr/bin/env bash

# Reliable way for a bash script to get the full path to itself?
# http://stackoverflow.com/questions/4774054/reliable-way-for-a-bash-script-to-get-the-full-path-to-itself
pushd `dirname $0` > /dev/null
SCRIPT_FOLDER_PATH=`pwd`
popd > /dev/null

command_line=$(printf '%q ' "${@:1}")
"${SCRIPT_FOLDER_PATH}/open_maximized.sh" "Sublime Text" /usr/bin/subl -n ${command_line}
