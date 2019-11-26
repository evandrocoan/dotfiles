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

printf "sublime command_line: '%s'\\n" "${command_line}";

# https://www.brianstorti.com/understanding-shell-script-idiom-redirect/
if [[ -z "${log_file}" ]]; then
	log_file=
fi

# https://askubuntu.com/questions/157779/how-to-determine-whether-a-process-is-running-or-not-and-make-use-it-to-make-a-c
if pgrep -f "/opt/sublime_text/sublime_text" > /dev/null
then
    printf "Sublime Text is running...\\n";
    /opt/sublime_text/sublime_text -n "${command_line}";
else
    printf "Sublime Text is NOT running...\\n";
    "${SCRIPT_FOLDER_PATH}/run_as_user.sh" sublime /opt/sublime_text_vanilla/sublime_text -n "${command_line}";
fi

"${SCRIPT_FOLDER_PATH}/open_maximized.sh" "Sublime Text";
