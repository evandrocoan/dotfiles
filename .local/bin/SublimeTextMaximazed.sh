#!/usr/bin/env bash

# Reliable way for a bash script to get the full path to itself?
# http://stackoverflow.com/questions/4774054/reliable-way-for-a-bash-script-to-get-the-full-path-to-itself
pushd `dirname $0` > /dev/null;
SCRIPT_FOLDER_PATH=`pwd`;
popd > /dev/null;

# https://stackoverflow.com/questions/3306007/replace-a-string-in-shell-script-using-a-variable
command_line=$(printf '%s ' "${@}" | sed -e 's/[[:space:]]*$//');

# command_line=$(printf '%q ' "${@}" | sed -e 's/[[:space:]]*$//');
# command_line="$(printf "%s" "${command_line}" | sed -E "s/\\\\(.)/\\1/g")";
# "${SCRIPT_FOLDER_PATH}/open_maximized.sh" "Sublime Text" /usr/bin/subl -n "${@:1}";

printf "sublime   command_line: '%s'\\n" "${command_line}";
/usr/bin/subl -n "${command_line}";
"${SCRIPT_FOLDER_PATH}/open_maximized.sh" "Sublime Text";
