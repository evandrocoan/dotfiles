#!/bin/bash
# set -x

#
# _generic_installer.sh
# Copyright (c) 2019 Evandro Coan
#
# Version: 1.0.0
# Always ensure you are using the latest version by checking:
# wget https://github.com/evandrocoan/MyLinuxSettings/blob/master/.local/bin/_generic_installer.sh
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

if [[ -z "${thing_name+x}" ]]; then
    thing_name="toolname";
fi;

if [[ -z "${git_server+x}" ]]; then
    git_server="https://repo.url.git";
fi;

if [[ -z "${tags_columns_width+x}" ]]; then
    tags_columns_width="30";
fi;

if [[ -z "${branches_columns_width+x}" ]]; then
    branches_columns_width="30";
fi;


# http://stackoverflow.com/questions/4774054/reliable-way-for-a-bash-script-to-get-the-full-path-to-itself
# https://stackoverflow.com/questions/1178751/how-can-you-access-the-base-filename-of-a-file-you-are-sourcing-in-bash
INSTALLATION_MODEL_SCRIPT_PATH="${BASH_SOURCE[0]}";
declare -a g_installation_model_commands_ranarray=();

function print_help() {
    printf "Usage instructions, you can call this script with the following named arguments:\\n";
    printf "     -y           to answer all questions as yes\\n";
    printf "     -n           to answer all questions as no\\n";
    printf "     -h           to show this help message\\n";
    printf "     -s number    to skip the first nº instructions\\n";
    printf "     -v version   to install the selected version from git\\n";
    printf "\\n";
    printf "You can call this script with the following positional arguments:\\n";
    printf "     1. version   to install the selected version from git\\n";
    printf "     2. number    to skip the first nº instructions\\n";
    printf "\\n";
    printf "If you are going to call the 'list_git_tags' function, these the global \\n";
    printf "variables must be defined before calling the 'parse_command_line' function\\n";
    printf "     '\${thing_name}', the target directory to save the cloned git repositories\\n";
    printf "     '\${git_server}', the targer git repository to fetch data from\\n";
    printf "\\n";
    printf "And these global variables are optional for the 'list_git_tags' function\\n";
    printf "     '\${tags_columns_width}', the minimum length of each git tags column\\n";
    printf "     '\${branches_columns_width}', the minimum length of each git branches column\\n";
    printf "\\n";
    printf "These are the available global variables after calling 'parse_command_line'\\n";
    printf "     '\${branch_or_tag}', it has the same value/saves the version command line argument\\n";
    printf "     '\${clone_directory}', the full path to where clone the git repository\\n";
    printf "\\n";
    printf "Usage examples:\\n";
    printf "     %s\\n" "${0}";
    printf "     %s v1.8.4\\n" "${0}";
    printf "     %s v1.8.4 20\\n" "${0}";
    printf "     %s -h\\n" "${0}";
    printf "     %s -v v1.8.4\\n" "${0}";
    printf "     %s -v v1.8.4 -s 10\\n" "${0}";
    printf "     %s -y\\n" "${0}";
    printf "     %s -y -s 20\\n" "${0}";
    printf "     %s -y -s 20 -v v1.8.4\\n" "${0}";
    printf "\\n";
    printf "API Documentation\\n";
    printf "%s\\n" "$(grep -F -h "##" "${INSTALLATION_MODEL_SCRIPT_PATH}" | grep -F -v grep -F | sed -e 's/\\$$//' | sed -e 's/##//')";
}


## Function parse_command_line
## Validate and get all named and positional line arguments from $1 to $n.
## Example: parse_command_line "${@}";
##
# https://stackoverflow.com/questions/16483119/an-example-of-how-to-use-getopts-in-bash
# https://unix.stackexchange.com/questions/129391/passing-named-arguments-to-shell-scripts
# https://stackoverflow.com/questions/4341630/checking-for-the-correct-number-of-arguments
# https://stackoverflow.com/questions/11742996/shell-script-is-mixing-getopts-with-positional-parameters-possible
function parse_command_line() {
    local named_options;
    local parsed_positional_arguments;

    yes_to_all_questions="";
    parsed_positional_arguments=0;

    function hiddeninstallationmodel_validateduplicateoptions() {
        local item;
        local variabletoset;
        local namedargument;
        local argumentvalue;

        variabletoset="${1}";
        namedargument="${2}";
        argumentvalue="${3}";

        if [[ -z "${namedargument}" ]]; then
            printf "Error: Missing command line option for named argument '%s', got '%s'...\\n" "${variabletoset}" "${argumentvalue}";
            exit 1;
        fi;

        for item in "${named_options[@]}";
        do
            if [[ "${item}" == "${argumentvalue}" ]]; then
                printf "Warning: Named argument '%s' got possible invalid option '%s'...\\n" "${namedargument}" "${argumentvalue}";
                exit 1;
            fi;
        done;

        if [[ -n "${!variabletoset}" ]]; then
            printf "Warning: Overriding the named argument '%s=%s' with '%s'...\\n" "${namedargument}" "${!variabletoset}" "${argumentvalue}";
        else
            printf "Setting '%s' named argument '%s=%s'...\\n" "${thing_name}" "${namedargument}" "${argumentvalue}";
        fi;
        eval "${variabletoset}='${argumentvalue}'";
    }

    # https://stackoverflow.com/questions/2210349/test-whether-string-is-a-valid-integer
    function hiddeninstallationmodel_validateintegeroption() {
        local namedargument;
        local argumentvalue;

        namedargument="${1}";
        argumentvalue="${2}";

        if [[ -z "${2}" ]];
        then
            argumentvalue="${1}";
        fi;

        if [[ -n "$(printf "%s" "${argumentvalue}" | sed s/[0-9]//g)" ]];
        then
            if [[ -z "${2}" ]];
            then
                printf "Error: The %s positional argument requires a integer, but it got '%s'...\\n" "${parsed_positional_arguments}" "${argumentvalue}";
            else
                printf "Error: The named argument '%s' requires a integer, but it got '%s'...\\n" "${namedargument}" "${argumentvalue}";
            fi;
            exit 1;
        fi;
    }

    function hiddeninstallationmodel_validateposisionaloption() {
        local variabletoset;
        local argumentvalue;

        variabletoset="${1}";
        argumentvalue="${2}";

        if [[ -n "${!variabletoset}" ]]; then
            printf "Warning: Overriding the %s positional argument '%s=%s' with '%s'...\\n" "${parsed_positional_arguments}" "${variabletoset}" "${!variabletoset}" "${argumentvalue}";
        else
            printf "Setting the %s positional argument '%s=%s'...\\n" "${parsed_positional_arguments}" "${variabletoset}" "${argumentvalue}";
        fi;
        eval "${variabletoset}='${argumentvalue}'";
    }

    named_options=(
            "-y" "--yes"
            "-n" "--no"
            "-h" "--help"
            "-s" "--skip"
            "-v" "--version"
        );

    while [[ "${#}" -gt 0 ]];
    do
        case ${1} in
            -y|--yes)
                yes_to_all_questions="${1}";
                printf "Named argument '%s' for yes to all questions was triggered.\\n" "${1}";
                ;;

            -n|--no)
                yes_to_all_questions="${1}";
                printf "Named argument '%s' for no to all questions was triggered.\\n" "${1}";
                ;;

            -h|--help)
                printf "\\n";
                print_help;
                exit 0;
                ;;

            -s|--skip)
                hiddeninstallationmodel_validateintegeroption "${1}" "${2}";
                hiddeninstallationmodel_validateduplicateoptions g_installation_model_skip_commands "${1}" "${2}";
                shift;
                ;;

            -v|--version)
                hiddeninstallationmodel_validateduplicateoptions branch_or_tag "${1}" "${2}";
                shift;
                ;;

            *)
                parsed_positional_arguments=$((parsed_positional_arguments+1));

                case ${parsed_positional_arguments} in
                    1)
                        hiddeninstallationmodel_validateposisionaloption branch_or_tag "${1}";
                        ;;

                    2)
                        hiddeninstallationmodel_validateintegeroption "${1}";
                        hiddeninstallationmodel_validateposisionaloption g_installation_model_skip_commands "${1}";
                        ;;

                    *)
                        printf "ERROR: Extra positional command line argument '%s' found.\\n" "${1}";
                        exit 1;
                        ;;
                esac;
                ;;
        esac;
        shift;
    done;

    g_installation_model_command_counter=0;
    clone_directory="./${thing_name}/${branch_or_tag}";

    if [[ -z "${g_installation_model_skip_commands}" ]];
    then
        g_installation_model_skip_commands="0";
    fi;
}


# https://stackoverflow.com/questions/2642585/read-a-variable-in-bash-with-a-default-value
function hiddeninstallationmodellistalreadyrancommands() {
    local stringarray;
    printf "\\n";
    printf "These were the last '%sº' commands ran... (%s)\\n" "${g_installation_model_command_counter}" "$(pwd)";

    for stringarray in "${g_installation_model_commands_ranarray[@]}";
    do
        printf "%s\\n" "${stringarray}";
    done;
}


function hiddeninstallationmodelhandlegeneralexception() {
    local commandline;
    local returncode;
    local fixcommand;
    local generalexceptiontype;
    local newvariablename;
    local stringarray;

    generalexceptiontype="${1}";
    commandline="${2}";
    returncode="${3}";
    newvariablename="${4}";
    fixcommand="d";

    printf "\\n";
    if [[ "w${generalexceptiontype}" == "wset" ]];
    then
        printf "The last set command '%s=%s' on step '%sº' returned with the error code '%s'...\\n" "${newvariablename}" "${commandline}" "${g_installation_model_command_counter}" "${returncode}";

    elif [[ "w${generalexceptiontype}" == "wrun" ]];
    then
        printf "The last '%sº' command '%s' returned with the error code '%s'...\\n" "${g_installation_model_command_counter}" "${commandline}" "${returncode}";

    else
        printf "ERROR: Invalid option '%s' for the last '%sº' command '%s' returned with the error code '%s'...\\n" "${generalexceptiontype}" "${g_installation_model_command_counter}" "${commandline}" "${returncode}";
        read -e -r -p "Press 'Enter' to continue... " fixcommand;
        return 1;
    fi;

    while [[ "w${fixcommand}" != "wc" ]];
    do
        printf "\\n";
        printf "Type 'c' and press 'Enter' to continue the main script execution...\\n";

        if [[ "w${generalexceptiontype}" == "wset" ]];
        then
            printf "Type 'r' to run again the last set command...\\n";
            printf "Type 's' to manually set the '%s' variable value.\\n" "${newvariablename}";
            printf "Type 'e' to edit in memory the '%s=%s' variable set command...\\n" "${newvariablename}" "${commandline}";

        elif [[ "w${generalexceptiontype}" == "wrun" ]];
        then
            printf "Type 'r' and press 'Enter' to repeat the last '%sº' command...\\n" "${g_installation_model_command_counter}";
            printf "Type 'e' to edit in memory the '%sº' command '%s'...\\n" "${g_installation_model_command_counter}" "${commandline}";
        fi;

        printf "Type 'l' to show all commands already run up to step '%sº'...\\n" "${g_installation_model_command_counter}";
        printf "Beyond these options, you can also run any command you would like as 'cd dir', 'ls -la', etc...\\n";
        read -e -r -p "Command: " fixcommand;

        while [[ "w${fixcommand}" == "w" ]];
        do
            printf "ERROR: The fix command cannot be empty. Please, type 'c', 'r' or some other command.\\n";
            read -e -r -p "Command: " fixcommand;
        done;

        if [[ "w${fixcommand}" == "wc" ]];
        then
            printf "\\n";
            printf "Continuing the main script execution on step '%sº'... (%s)\\n" "${g_installation_model_command_counter}" "$(pwd)";
            return 0;

        elif [[ "w${fixcommand}" == "wr" ]] && [[ "w${generalexceptiontype}" == "wrun" ]];
        then
            printf "\\n";
            printf "Repeating the last '%sº' command '%s'... (%s)\\n" "${g_installation_model_command_counter}" "${commandline}" "$(pwd)";
            eval "${commandline}" || hiddeninstallationmodelhandlegeneralexception "run" "${commandline}" "${?}";
            return 0;

        elif [[ "w${fixcommand}" == "we" ]] && [[ "w${generalexceptiontype}" == "wrun" ]];
        then
            # https://stackoverflow.com/questions/2642585/read-a-variable-in-bash-with-a-default-value
            printf "\\n";
            printf "Editing the last '%sº' command '%s' to... (%s)\\n" "${g_installation_model_command_counter}" "${commandline}" "$(pwd)";
            read -e -r -p "Edit command: " -i "${commandline}" commandline;

            printf "Running the fix comand '%sº' command '%s'... (%s)\\n" "${g_installation_model_command_counter}" "${commandline}" "$(pwd)";
            eval "${commandline}" || hiddeninstallationmodelhandlegeneralexception "run" "${commandline}" "${?}";
            return 0;

        elif [[ "w${fixcommand}" == "wr" ]] && [[ "w${generalexceptiontype}" == "wset" ]];
        then
            printf "\\n";
            printf "Repeating the last set command '%s' on step '%sº'... (%s)\\n" "${commandline}" "${g_installation_model_command_counter}" "$(pwd)";
            hiddeninstallationmodelrunsetunexpandable "${newvariablename}" ${commandline};
            return 0;

        elif [[ "w${fixcommand}" == "we" ]] && [[ "w${generalexceptiontype}" == "wset" ]];
        then
            # https://stackoverflow.com/questions/2642585/read-a-variable-in-bash-with-a-default-value
            printf "\\n";
            printf "Editing the last set command '%s' on step '%sº' to... (%s)\\n" "${commandline}" "${g_installation_model_command_counter}" "$(pwd)";
            read -e -r -p "${newvariablename}=" -i "${commandline}" commandline;

            hiddeninstallationmodelrunsetunexpandable "${newvariablename}" ${commandline};
            return 0;

        elif [[ "w${fixcommand}" == "ws" ]] && [[ "w${generalexceptiontype}" == "wset" ]];
        then
            printf "\\n";
            printf "Manually setting the variable '%s' value for the command '%s' on step '%sº' (%s)\\n" "${newvariablename}" "${commandline}" "${g_installation_model_command_counter}" "$(pwd)";
            read -e -r -p "${newvariablename}=" fixcommand;

            # https://stackoverflow.com/questions/52065016/how-to-replace-n-string-with-a-new-line-in-unix-bash-script
            # https://unix.stackexchange.com/questions/527170/how-to-read-input-lines-with-newline-characters-from-command-line
            fixcommand=$(printf "%s\\n" "${fixcommand}" | sed 's/\\n/\n/g') && eval "${newvariablename}='${fixcommand}'";
            returncode="${?}";

            if [[ "w${returncode}" != "w0" ]];
            then
                printf "The new variable value set on step '%sº' is '%s=%s'...\\n" "${g_installation_model_command_counter}" "${newvariablename}" "${!newvariablename}";
                return 0;
            else
                printf "The '%sº' new variable set value command '%s=%s' returned with the error code '%s'...\\n" "${g_installation_model_command_counter}" "${newvariablename}" "${fixcommand}" "${returncode}";
            fi;

        elif [[ "w${fixcommand}" == "wl" ]];
        then
            hiddeninstallationmodellistalreadyrancommands;

        else
            printf "\\n";
            printf "Running the fix command '%s' on step '%sº'... (%s)\\n" "${fixcommand}" "${g_installation_model_command_counter}" "$(pwd)";
            eval "${fixcommand}";
            returncode="${?}";

            if [[ "w${returncode}" != "w0" ]];
            then
                printf "\\n";
                printf "The fix '%sº' command '%s' returned with the error code '%s'...\\n" "${g_installation_model_command_counter}" "${fixcommand}" "${returncode}";
            fi;
        fi;
    done;
}


## Function run
## Run the given command, only when we are not skipping the first nº commands.
## Example: run ls -la;
##
function run() {
    local commandline;

    g_installation_model_skip_commands=$((g_installation_model_skip_commands-1));
    g_installation_model_command_counter=$((g_installation_model_command_counter+1));

    commandline="$(printf '%q ' "${@}" | sed -e 's/[[:space:]]*$//')";
    g_installation_model_commands_ranarray+=("${g_installation_model_command_counter}º ${commandline};");

    if [[ "${g_installation_model_skip_commands}" -gt 0 ]];
    then
        printf "Skipping '%sº' required command '%s' (%s)\\n" "${g_installation_model_command_counter}" "${commandline}" "$(pwd)";
    else
        printf "\\n";
        printf "Running '%sº' required command '%s' (%s)\\n" "${g_installation_model_command_counter}" "${commandline}" "$(pwd)";
        eval "${commandline}" || hiddeninstallationmodelhandlegeneralexception "run" "${commandline}" "${?}";
    fi;
}


## Function runalways
## Always run the given command, even when we are skipping the first nº commands.
## Example: runalways ls -la;
##
function runalways() {
    local commandline;

    g_installation_model_skip_commands=$((g_installation_model_skip_commands-1));
    g_installation_model_command_counter=$((g_installation_model_command_counter+1));

    commandline="$(printf '%q ' "${@}" | sed -e 's/[[:space:]]*$//')";
    g_installation_model_commands_ranarray+=("${g_installation_model_command_counter}º ${commandline};");

    printf "\\n";
    printf "Running the '%sº' always command '%s' (%s)\\n" "${g_installation_model_command_counter}" "${commandline}" "$(pwd)";
    eval "${commandline}" || hiddeninstallationmodelhandlegeneralexception "run" "${commandline}" "${?}";
}


# https://unix.stackexchange.com/questions/222487/bash-dynamic-variable-variable-names
# https://stackoverflow.com/questions/37921942/unix-shell-script-exit-with-returning-value
# https://stackoverflow.com/questions/4419952/difference-between-return-and-exit-in-bash-functions
# https://unix.stackexchange.com/questions/41292/variable-substitution-with-an-exclamation-mark-in-bash
# https://stackoverflow.com/questions/4341630/checking-for-the-correct-number-of-arguments
# https://unix.stackexchange.com/questions/428895/how-can-i-generate-my-desired-exit-code-on-shell-commands-or-one-line-scripts
function hiddeninstallationmodelrunset() {
    local issilent;
    local newvariablename;
    local commandline;
    local temporary_variable;

    issilent="${1}";
    newvariablename="${2}";

    g_installation_model_skip_commands=$((g_installation_model_skip_commands-1));
    g_installation_model_command_counter=$((g_installation_model_command_counter+1));

    # https://stackoverflow.com/questions/56822216/how-to-portability-use-2#56822303
    shift; shift;
    commandline="$(printf '%q ' "${@}" | sed -e 's/[[:space:]]*$//')";
    g_installation_model_commands_ranarray+=("${g_installation_model_command_counter}º ${commandline};");

    printf "\\n";
    printf "Setting the variable '%s' with the command '%s'... (%s)\\n" "${newvariablename}" "${commandline}" "$(pwd)";
    temporary_variable="$(eval "${commandline}" | sed -e 's/[[:space:]]*$//')" || hiddeninstallationmodelhandlegeneralexception "set" "${commandline}" "${?}" "${newvariablename}" || return "${?}";

    eval "${newvariablename}='${temporary_variable}'";
    if [[ "w${issilent}" == "wyes" ]];
    then
        :
    else
        printf "The new variable value set on step '%sº' is '%s=%s'...\\n" "${g_installation_model_command_counter}" "${newvariablename}" "${!newvariablename}";
    fi;
}


## Function runset
## Set a global variable value as the output of the following shell command.
## This outputs to the console the assigned variable contents.
## Example: runset myglobalvar ls -la;
##
function runset() {
    hiddeninstallationmodelrunset "no" "${@}";
}


## Function runsets
## Set a global variable value as the output of the following shell command.
## This does NOT outputs (silent assignment) to the console the assigned variable contents.
## Example: runsets myglobalvar ls -la;
##
function runsets() {
    hiddeninstallationmodelrunset "yes" "${@}";
}


function hiddeninstallationmodelrunsetunexpandable() {
    local newvariablename;
    local commandline;
    local temporary_variable;

    newvariablename="${1}";
    shift;

    # https://stackoverflow.com/questions/56822216/how-to-portability-use-2#56822303
    commandline="$(printf "%s " "${@}" | sed -e 's/[[:space:]]*$//')";

    printf "\\n";
    printf "Setting the variable '%s' with the command '%s'... (%s)\\n" "${newvariablename}" "${commandline}" "$(pwd)";
    temporary_variable="$(eval "${commandline}")" || hiddeninstallationmodelhandlegeneralexception "set" "${commandline}" "${?}" "${newvariablename}" || return "${?}";

    eval "${newvariablename}='${temporary_variable}'";
    printf "The new variable value set on step '%sº' is '%s=%s'...\\n" "${g_installation_model_command_counter}" "${newvariablename}" "${!newvariablename}";
}


## Function ask_to_run
## Before running a command, ask whether the command should run or skipped.
## Example: ask_to_run ls -la;
##
function ask_to_run() {
    local shouldirun;
    local commandline;
    local returncode;

    g_installation_model_skip_commands=$((g_installation_model_skip_commands-1));
    g_installation_model_command_counter=$((g_installation_model_command_counter+1));

    commandline="$(printf '%q ' "${@}" | sed -e 's/[[:space:]]*$//')";
    g_installation_model_commands_ranarray+=("${g_installation_model_command_counter}º ${commandline};");

    if [[ "${g_installation_model_skip_commands}" -gt 0 ]];
    then
        printf "Skipping '%sº' optional command '%s' (%s)\\n" "${g_installation_model_command_counter}" "${commandline}" "$(pwd)";

    else
        # https://stackoverflow.com/questions/6594085/remove-first-character-of-a-string-in-bash
        printf "\\n";
        printf "Should I run the '%sº' optional command '%s'? (%s)\\n" "${g_installation_model_command_counter}" "${commandline}" "$(pwd)";
        shouldirun="${yes_to_all_questions:1}";

        while [[ "w${shouldirun}" != "wy" ]] &&
            [[ "w${shouldirun}" != "wyes" ]] &&
            [[ "w${shouldirun}" != "wn" ]] &&
            [[ "w${shouldirun}" != "wc" ]];
        do
            printf "\\n";
            printf "Type 'y' and press 'Enter' if yes. Otherwise, type 'n'...\\n";
            printf "Type 'l' to show all commands already run up to step '%sº'...\\n" "${g_installation_model_command_counter}";
            printf "Beyond these options, you can also run any command you would like as 'cd dir', 'ls -la', etc...\\n";
            read -e -r -p "Command: " shouldirun;

            while [[ "w${shouldirun}" == "w" ]];
            do
                printf "ERROR: The fix command cannot be empty. Please, type 'y', 'n' or some other command.\\n";
                read -e -r -p "Command: " shouldirun;
            done;

            if [[ "w${shouldirun}" == "wc" ]];
            then
                printf "\\n";
                printf "Continuing the main script execution on step '%sº'... (%s)\\n" "${g_installation_model_command_counter}" "$(pwd)";
                return 0;

            elif [[ "w${shouldirun}" == "wy" ]] || [[ "w${shouldirun}" == "wyes" ]];
            then
                printf "Running the '%sº' optional command '%s'...\\n" "${g_installation_model_command_counter}" "${commandline}";
                eval "${commandline}" || hiddeninstallationmodelhandlegeneralexception "run" "${commandline}" "${?}";

            elif [[ "w${shouldirun}" == "wn" ]];
            then
                printf "NOT running the '%sº' optional command '%s'...\\n" "${g_installation_model_command_counter}" "${commandline}";

            elif [[ "w${shouldirun}" == "wl" ]];
            then
                hiddeninstallationmodellistalreadyrancommands;

            else
                printf "\\n";
                printf "Running the fix command '%s' on step '%sº'... (%s)\\n" "${shouldirun}" "${g_installation_model_command_counter}" "$(pwd)";
                eval "${shouldirun}";
                returncode="${?}";

                if [[ "w${returncode}" != "w0" ]];
                then
                    printf "\\n";
                    printf "The fix '%sº' command '%s' returned with the error code '%s'...\\n" "${g_installation_model_command_counter}" "${shouldirun}" "${returncode}";
                fi;
            fi;
        done;
    fi;
}


function hiddeninstallationmodellistgitremote() {
    local column_accumulated_size;
    local version_to_flush;
    local number_of_columns;
    local filling_index;

    local arrayfilteredlines;
    local oldaccumulatedsize;
    local stringarray;
    local stringarraysize;
    local fillingdifference;
    local linevariable;
    local git_raw_string;
    local git_filter_string;
    local maximum_columns_width;
    local extradifferencetocompesate;

    # https://stackoverflow.com/questions/19912681/build-a-string-in-bash-with-newlines
    local newline=$'\n'

    git_raw_string="${1}";
    git_parsed_string="";
    git_filter_string="${2}";
    maximum_columns_width="${3}";

    # https://stackoverflow.com/questions/8880603/loop-through-an-array-of-strings-in-bash
    declare -a arrayfilteredlines=();
    column_accumulated_size="0";
    number_of_columns="$(tput cols)";

    # https://stackoverflow.com/questions/2376031/reading-multiple-lines-in-bash-without-spawning-a-new-subshell
    # https://stackoverflow.com/questions/1951506/add-a-new-element-to-an-array-without-specifying-the-index-in-bash
    while read -r linevariable
    do
        # https://stackoverflow.com/questions/1469849/how-to-split-one-string-into-multiple-strings-separated-by-at-least-one-space-in
        read -ra stringarray <<<"${linevariable}";
        stringarray="${stringarray[1]}";

        if [[ "w${stringarray}" == "w${git_filter_string}"* ]];
        then
            stringarraysize="${#git_filter_string}";
            stringarray="${stringarray:${stringarraysize}}";

            if [[ "${stringarray}w" != *'^{}w' ]];
            then
                # printf "linevariable=$linevariable\\n";
                git_parsed_string+="${stringarray}${newline}";
            fi;
        fi;
    done < <(printf "%s\\n" "${git_raw_string}");

    # printf '%s\n' "${hiddeninstallationmodelpythonsortprogram}" > hiddeninstallationmodelpythonsortprogram.py;
    # git_parsed_string="$(python hiddeninstallationmodelpythonsortprogram.py "${git_parsed_string}")";
    # git_parsed_string="$(printf '%s' "${git_parsed_string}" | tr -d '\r')"
    # rm hiddeninstallationmodelpythonsortprogram.py
    git_parsed_string="$(printf '%s' "${git_parsed_string}" | sort -V)"

    # printf "git_parsed_string: %s\\n" "${git_parsed_string}";
    while read -r linevariable;
    do
        # printf "linevariable=$linevariable\\n";
        if [[ -n "${linevariable}" ]];
        then
            arrayfilteredlines+=("${linevariable}");
        fi
    done < <(printf "%s\\n" "${git_parsed_string}");

    function hiddeninstallationmodelfillstringwithpaddding() {
        local padddingtofill;
        padddingtofill="${1}";

        # printf "Filling pad=$padddingtofill\\n"
        for(( filling_index = 0; filling_index < padddingtofill; filling_index++ ));
        do
            if [[ "$(( oldaccumulatedsize + filling_index + 1 ))" -gt "${number_of_columns}" ]];
            then
                # printf "BREAKING on filling_index=$filling_index\\n"
                break;
            else
                version_to_flush="${version_to_flush} ";
            fi;
        done;
    }

    # https://github.com/koalaman/shellcheck/issues/1635
    function hiddeninstallationmodelcompute_missing_padding() {
        extradifferencetocompesate="${fillingdifference}";
        while [[ "${extradifferencetocompesate}" -lt 0 ]];
        do
            extradifferencetocompesate="$(( maximum_columns_width + 1 + extradifferencetocompesate ))"
        done;
    }

    # printf "arrayfilteredlines=$arrayfilteredlines\\n";
    for stringarray in "${arrayfilteredlines[@]}";
    do
        # printf "stringarray '%s'" "${stringarray}";
        version_to_flush="${stringarray}";
        stringarraysize="${#stringarray}";
        fillingdifference="$(( maximum_columns_width - stringarraysize ))";

        # printf "column_accumulated_size=$column_accumulated_size, stringarraysize=$stringarraysize, number_of_columns=$number_of_columns\\n"
        if [[ "$(( column_accumulated_size + stringarraysize ))" -gt "${number_of_columns}" ]];
        then
            printf "\\n";
            oldaccumulatedsize="${stringarraysize}";

            if [[ "${fillingdifference}" -gt 0 ]];
            then
                column_accumulated_size="$(( maximum_columns_width + 1 ))";
                hiddeninstallationmodelfillstringwithpaddding "${fillingdifference}";
            else
                hiddeninstallationmodelcompute_missing_padding;
                column_accumulated_size="$(( stringarraysize + 1 + extradifferencetocompesate ))";
                hiddeninstallationmodelfillstringwithpaddding "${extradifferencetocompesate}";
            fi;

        else
            oldaccumulatedsize="$(( column_accumulated_size + stringarraysize ))";

            if [[ "${fillingdifference}" -gt 0 ]];
            then
                column_accumulated_size="$(( column_accumulated_size + maximum_columns_width + 1 ))";
                hiddeninstallationmodelfillstringwithpaddding "${fillingdifference}";
            else
                hiddeninstallationmodelcompute_missing_padding;
                column_accumulated_size="$(( column_accumulated_size + stringarraysize + 1 + extradifferencetocompesate ))";
                hiddeninstallationmodelfillstringwithpaddding "${extradifferencetocompesate}";
            fi;
        fi;

        if [[ "${column_accumulated_size}" -gt "${number_of_columns}" ]];
        then
            printf "%s" "${version_to_flush}";
        else
            printf "%s " "${version_to_flush}";
        fi;
    done;
}


## Function list_git_tags
## Fetch a git repository remote tags and list them. This function does not take any parameters.
## Example: list_git_tags;
##
function list_git_tags() {
    local git_raw_tags_string;
    local git_raw_branches_string;

    print_help;
    printf "\\n";

    printf "Loading '%s' versions from '%s'...\\n" "${thing_name}" "${git_server}";
    printf "This should take about 10 seconds...\\n";

    # https://stackoverflow.com/questions/22460054/ls-remote-heads-origin-vs-ls-remote-refs-remotes
    runsets git_raw_tags_string git ls-remote --tags ${git_server};
    runsets git_raw_branches_string git ls-remote --heads ${git_server};
    printf "Done loading...\\n";

    printf "\\n";
    printf "These are the available git remote '%s' versions:\\n" "${thing_name}";
    hiddeninstallationmodellistgitremote "${git_raw_tags_string}" "refs/tags/" "${tags_columns_width}";

    printf "\\n\\n";
    printf "These are the available git remote '%s' branches:\\n" "${thing_name}";
    hiddeninstallationmodellistgitremote "${git_raw_branches_string}" "refs/heads/" "${branches_columns_width}";

    printf "\\n\\n";
    printf "Now, choose which '%s' version you would like to install by running:\\n" "${thing_name}";
    printf "    %s version\n" "${0}";
    exit 0;
}


# For tests
# function list_git_tags() {
# git_raw_tags_string="$(cat << EndOfMessage
# 85335355efb2d7914a1fe20ed31afcef15fd210c        refs/tags/13.0.0
# 658f72cb71d8b5d4063e1ec70588cd55a4c52bc2        refs/tags/13.0.0-beta1
# e5a3b1d0e751e1d9799dfeddb31d3091b31a6e96        refs/tags/13.0.0-beta2
# e7305c01f21a8e935e449e19652f96a582bd76dd        refs/tags/13.0.0-beta3
# 1a9331e814407d43a2e46e24825a6eedc7f2805f        refs/tags/13.0.1
# ee7aa21e683f0b46705effb0cf9a8e0af59b0160        refs/tags/13.0.2
# 50b6747c1dbc69fd98ea9b1fc940130acbf92a22        refs/tags/13.1-cert2
# ff4dbeaf3894d28de5c9e2a718702442acddcb29        refs/tags/13.1.0
# c90ce6f6c254ce6ddc032c64fe3b10e7eeb0a846        refs/tags/13.1.0-rc1
# c45c3b55247f5735f16ebfa90b38a93913dfcee6        refs/tags/13.1.0-rc2
# 7a5aa65c063e33c4255bbec727d2985a166e35a6        refs/tags/13.1.1
# b8f42ac9571af377262a0bf1fc2cff865cea9650        refs/tags/13.10.0
# c30613f7923ddb339dd30b9e1ce7cb18d15f75dc        refs/tags/13.10.0^{}
# fb64d601f2e636eb047ef533e361107aac5c7073        refs/tags/13.10.0-rc1
# 3c4b64351bc44b26fdfbb9101501ad8e485c9e11        refs/tags/13.10.0-rc1^{}
# ca95c2eef225e23110cf623ea7af0d9779e2194d        refs/tags/13.10.0-rc2
# 9a8b4251b8b8833085b68853b472c501fb885c4a        refs/tags/13.10.0-rc2^{}
# 3c216e20c48efecd011d4a67875d803f22d87034        refs/tags/13.10.0-rc3
# af1421588249c5e0e0340c518fdd66b96a61cdff        refs/tags/13.10.0-rc3^{}
# f51d52362dd3ef194e9161947f796e0773d45ed2        refs/tags/13.11.0
# a6ac89c740a9a8e9ee0e008e12df3998ea6a2492        refs/tags/13.11.0^{}
# 30f2549c0874736477762246ec97f83174f25eb9        refs/tags/13.11.0-rc1
# 9f083db88b469c4b454a901c6b0e7c3f10dfc8f8        refs/tags/13.11.0-rc1^{}
# 6bdeed7fb366b83b1913f6e39a630b2769e0b735        refs/tags/13.11.0-rc2
# 35fd61b9dcc3c46c111183268c651e6a2725f5be        refs/tags/13.11.0-rc2^{}
# c0a73889c0c67cb162a6f2e39118492806d93b37        refs/tags/13.11.1
# ec0088f7fb1d4bc744657403d2607a1ae9547c27        refs/tags/13.11.1^{}
# 5f88098c3e9b549167aecab14daac03fd8a600ab        refs/tags/13.11.2
# 35d74f5d4e15903c66abe602432df9e04049edb5        refs/tags/13.11.2^{}
# 475b51dcf6886e3746e4a384b917e021bc53d088        refs/tags/13.12.0
# 226a7e36c538de73cee76de4183b1569bd5501e5        refs/tags/13.12.0^{}
# 635774c4bb217f52dce11232d7c7a1f1972344d5        refs/tags/13.12.0-rc1
# df75b647da03eba6920020bac0cc950032a1e930        refs/tags/13.12.0-rc1^{}
# 357640f1fa5445af662f501e83fcf1424a41baef        refs/tags/13.12.1
# 7d7b52c434eb23ef470ad51d08ee4029a7078b78        refs/tags/13.12.1^{}
# 37571699111be043d409c97cb3bcec8bbffed3ea        refs/tags/13.12.2
# ee73af1d88c9ff6db90f70f934f5ea57b8ab0625        refs/tags/13.12.2^{}
# b939d863dff510ae678bde31c953cfb6c7f6ab53        refs/tags/13.13.0
# fdde690e0fa2e58bf45ea2bf83962bb1c261d6e0        refs/tags/13.13.0^{}
# 1c0ba90a8f684f2f3a4493fb81ad4bd9d2348c45        refs/tags/13.13.0-rc1
# 751d43e8e4173386be5455311561dfa819a642d3        refs/tags/13.13.0-rc1^{}
# 89050e710a8a289c2e2c7402cb65458ec4ada81c        refs/tags/13.13.0-rc2
# f93e55d124da09eb9929303189c4b925c42ad0bb        refs/tags/13.13.0-rc2^{}
# 8d88432483fac92137afb3a1a6a036ac2bf2eb7b        refs/tags/13.13.1
# d8797b8c03b60883474dfa1d5e6d155d10a438fc        refs/tags/13.13.1^{}
# a207321898fa22958e6925cf3120135e1109e629        refs/tags/13.14.0
# 7fc2c4b7843f06a1f421fadbf15a3e2afef0e1fb        refs/tags/13.14.0^{}
# 034bb697ef884480cff209b3606bcf8872b8230f        refs/tags/13.14.0-rc1
# 7dbe77d63946ce204611a75d5f79d37f9d624ee1        refs/tags/13.14.0-rc1^{}
# 09607d42f82278d8fdd1b430551b7fcba69aea9d        refs/tags/13.14.0-rc2
# ec97c41ac817bce13d8bd9436c35ad3ef95a9f72        refs/tags/13.14.0-rc2^{}
# 5d295ad31dd54ba6f6df9989c404444024cccec0        refs/tags/13.14.1
# 3d32a671506472457298f7ab64f6efb84088bd61        refs/tags/13.14.1^{}
# 5101583c3b6046affd2eaa8e9bdc291310de9cdb        refs/tags/13.15.0
# 7f9db93d8afd8879b6e5583d4556d4626d7f02ba        refs/tags/13.15.0^{}
# ee3bfa8d80c4af2cab001633f7f64e03c279b441        refs/tags/13.15.0-rc1
# 552cf009c0939c8b6597708135412bdc596df4bb        refs/tags/13.15.0-rc1^{}
# da1503fc38065da4c3936923ce2aab5586ec3526        refs/tags/13.15.0-rc2
# e6c7e7d08f4652f4382d72100739116cf5586932        refs/tags/13.15.0-rc2^{}
# e1ebbb14eec6fb4bad596061294253e003a8ee1e        refs/tags/13.15.0-rc3
# 0800ab33b5502d3a28409f813a698e298c55a2a7        refs/tags/13.15.0-rc3^{}
# dcb4f7a2afd02d7e8133c63bf411ca4bbeeec2e1        refs/tags/13.15.1
# a33aa668a56760ef54ebe78bd878809910398b54        refs/tags/13.15.1^{}
# 4520ab85474d224769c78935b309e3ca5c6d4944        refs/tags/13.16.0
# 4d985c171d92eed50b95f542c4c15b60c84d188f        refs/tags/13.16.0^{}
# 6af95e37d7fe3efc4cfc9e42648f6b64ed4cc0e6        refs/tags/13.16.0-rc1
# b634297c8c7a22a6e62fd7150dea185bebf2129e        refs/tags/13.16.0-rc1^{}
# 65a3d21b2e7d6869b09490e76ce95228c77639fb        refs/tags/13.16.0-rc2
# 79ceeea8f80bac8c8d5870490a013036bd83e510        refs/tags/13.16.0-rc2^{}
# fee222689eb6faf5c342b221aab4e0690c7f2ae9        refs/tags/13.17.0
# 22f1f880c43a69190db29b73fede7073580bbc09        refs/tags/13.17.0^{}
# 0f9e1e61c15801a353f622bb1394dcdf8e675255        refs/tags/13.17.0-rc1
# 0c00ee754b436ca926b92b469ce259e8fdc8732e        refs/tags/13.17.0-rc1^{}
# b51fe82fdad270bea4b88da2443ce8b0f57ba410        refs/tags/13.17.1
# 49d56dc9d2c1eececb4cae27cbbb427403c3f9f5        refs/tags/13.17.1^{}
# c9b7b3dc7c958f7e8a245870daf9141fc34ff56a        refs/tags/13.17.2
# 6afc128fee2733df68de67bff6e33ab41bf3786c        refs/tags/13.17.2^{}
# c24e29a08bf37a3bbc3309357d723fa71657d22a        refs/tags/13.18.0
# 719ac573a6dea452f122da76ba17073dc6ee1164        refs/tags/13.18.0^{}
# e346a5a56d45cdb70a39688c37a4e7f1b79966d3        refs/tags/13.18.0-rc1
# d5d1e98fa44eb32c8c195468c123829b12ae66d2        refs/tags/13.18.0-rc1^{}
# 2a7ae0abc15304cce7f7bd3f40831e765f5bcb79        refs/tags/13.18.0-rc2
# 82cedfbcb303ce2cbb3b3125b1beb0d59bdff93a        refs/tags/13.18.0-rc2^{}
# 3fea15241f95e364469f7db03be1740a55a218ad        refs/tags/13.18.1
# f0eea53cdc7a9d1461726e3a4b8880af1ea53148        refs/tags/13.18.1^{}
# d80a4bd139ae42ad78552a093b4db4432b72c621        refs/tags/13.18.2
# 9553242ee6b717129bd6ae4fe2134af5356788a3        refs/tags/13.18.2^{}
# b901b32d67ad55b3bfd06f9489815434bcb71d3a        refs/tags/13.18.3
# 760c5b3f8366554054c6e79a5272aedb1a19998d        refs/tags/13.18.3^{}
# a75d114dd59659bb5a78b97d8aeb7e717313a52e        refs/tags/13.18.4
# f4644317b7dd1963c92dc13295027cdfbb4fbc5e        refs/tags/13.18.4^{}
# 28bcb1b39bfe15900e822ead82e57fefe7eb9909        refs/tags/13.18.5
# 7bd29501d2212a00b05a432cfaff2d5c3e614f18        refs/tags/13.18.5^{}
# 48cc14d6143067d2402ad0d160041ba6d9518387        refs/tags/13.19.0
# cf98ecc2bffe104c823a67a512eb376ddfaa18e8        refs/tags/13.19.0^{}
# 7ccf22fa35338602df72d51b88114eeea70c0111        refs/tags/13.19.0-rc1
# f1f1d002ce959f4ee537dab754c8b92941316271        refs/tags/13.19.0-rc1^{}
# 9d3de1b297b45f186ef830fff59b879b231ed0df        refs/tags/13.19.0-rc2
# 19f4c115239648d2a5a86a588fa1f02a4235e911        refs/tags/13.19.0-rc2^{}
# f74fb665f62f2c93fabcb1f94717bf266f4621a2        refs/tags/13.19.1
# d53653ed7a4ccb7f1dfaba6ec5543dc76e60fc53        refs/tags/13.19.1^{}
# ffa34c5570b9956a73796c9e6027cd8a15a37842        refs/tags/13.19.2
# f7b006adc261f8726b66651c4c781be4b40cfba1        refs/tags/13.19.2^{}
# 5cc6bd8fe6a4ee99ecb05178e30ca35e07ba8e4f        refs/tags/13.2.0
# a254eba1d54a43c012435ee14b7a3d949af9972b        refs/tags/13.2.0-rc1
# 9f52e16c269a3c18d9f50f92c4553e8e6d72e838        refs/tags/13.2.1
# 9beb6a1a4fcfbaea3850cfdf0f2909708390ff8b        refs/tags/13.20.0
# 204b080d700b3df035c46588cee3011e2b8ef17a        refs/tags/13.20.0^{}
# d3db39190a23924b55eff62cd9bc900bdf1baccf        refs/tags/13.20.0-rc1
# 83a8058cd85b342e4db0fff2216f31310f229d10        refs/tags/13.20.0-rc1^{}
# a54a912e082959fbdcd980004b81ee8ca7e92133        refs/tags/13.20.0-rc2
# 0a0c1b14079609471a4189cf8dba604ef17556c2        refs/tags/13.20.0-rc2^{}
# 4891276d2fcb9e2953cb73e3503197e7b911e95a        refs/tags/13.21.0
# f71a36701674cf50c47d91c403e824b9cc4868a7        refs/tags/13.21.0^{}
# 20f2108c493f43931c50628f4cdc115159928bb8        refs/tags/13.21.0-rc1
# 32f362c8962addbda98d5dc679a644b654ad486b        refs/tags/13.21.0-rc1^{}
# 6c5e083ceb4a1ee5f9a724de8685190748370817        refs/tags/13.21.1
# 15793b8e537c8a912b88bf94e496a098827fe2e5        refs/tags/13.21.1^{}
# 9e938051852dc2db4fb95c1b8933e2cff615e863        refs/tags/13.22.0
# a261dff069b614d433b30924dbc9997baa91d81c        refs/tags/13.22.0^{}
# 9d048a4bacc700099d23bf97705ff40266e8626a        refs/tags/13.22.0-rc1
# 5af96b71113be9abd4e23540626dc347da62d0b7        refs/tags/13.22.0-rc1^{}
# b61192480c68d72d8e5c46794c078769e0fcbbef        refs/tags/13.23.0
# 8ac08a916c7fcc1ceecf3d682a1877c46deab626        refs/tags/13.23.0^{}
# d7f4395f7719c5fcf3680e25d16e785326b90c2d        refs/tags/13.23.0-rc1
# 53bc93373765ef99765ef69d4e9441531788fc83        refs/tags/13.23.0-rc1^{}
# b6caa1cdaa78e784e5bb8eb9a3cecdd490149a7f        refs/tags/13.23.1
# afd4bcfc76756e8b72c9fe68b31afd6021011e54        refs/tags/13.23.1^{}
# 91a1a5a395838f1fddf56152512325b552a33b62        refs/tags/13.24.0
# 2fce5d3cf879962106d928a79f2d4a33e0eddf63        refs/tags/13.24.0^{}
# ef3eb47a8261e32fd37f957b6eb7f9638aa29146        refs/tags/13.24.0-rc1
# d0e89602771e2c2896cd9fa763307989c3829da6        refs/tags/13.24.0-rc1^{}
# 87d85b5a863dd0c963ca794ac2f41eb1801e2ddd        refs/tags/13.24.1
# 11fec5fdc8cf3777686c03f88c2cc9088f953ec0        refs/tags/13.24.1^{}
# 24ad4ff997c31cee435328573984555e4b4d06a6        refs/tags/13.25.0
# ec397504dfcaf357f19f12087702412ae9290e5b        refs/tags/13.25.0^{}
# 28c9724408aed3a086b847c2d0e786da359229e7        refs/tags/13.25.0-rc1
# 638e336137089a73a04b0bb8ddbecf7200296aff        refs/tags/13.25.0-rc1^{}
# 91dfd8ba05f49afc6038b8a7f1ef870e9978b0ce        refs/tags/13.25.0-rc2
# 208bc32f2b1b58fec0d0746586bd905a92c73b53        refs/tags/13.25.0-rc2^{}
# 34aea4d84ca8873fd149a3e2759a1b88ed659891        refs/tags/13.25.0-rc3
# c9d039ba4f3a813f222ad03e594c11932977d5ae        refs/tags/13.25.0-rc3^{}
# 161e2f4bf48d55141166395b25f6e423818bc92b        refs/tags/13.26.0
# 7055a8eca56d7fcc3b0cc094a518d0dc7b61af51        refs/tags/13.26.0^{}
# 153d58ac33c86aec869bb85dd7fd8a9dfe5aa17d        refs/tags/13.26.0-rc1
# 0ed0c92cabab0a3b5de5ccfe871811233b459d88        refs/tags/13.26.0-rc1^{}
# 2a7bbf95a2708e0d0ab134199f4834ede374ddde        refs/tags/13.27.0
# 152d446befb93f64883b156cb58aea105d629423        refs/tags/13.27.0^{}
# 97d4135d71b9385b8aad35e7ef2790b016da871b        refs/tags/13.27.0-rc1
# bcca2cf3e621aee40954d48a38f88f9e32a0ed94        refs/tags/13.27.0-rc1^{}
# 68a4990e47a84f583bdfc2a1e7e44bf15053238f        refs/tags/13.27.1
# 66fcb3499bd543d634d1ab161c81c42ba712def1        refs/tags/13.27.1^{}
# b2a3890e461b4671bc9b4a5dd6f59e3db6f4bc5f        refs/tags/13.28.0
# eb57fac90cc1f826ce58c73d5798e5ad7ac7e931        refs/tags/13.28.0^{}
# 91af79364e2bd023f777e181b9d34bb029d059fd        refs/tags/13.28.0-rc1
# b25e1231dd69fc9d4f74a7605648d46793089a0d        refs/tags/13.28.0-rc1^{}
# 4447e1bd9a68ed03ed9c041c448907ffb8bd9e3f        refs/tags/13.28.1
# 8397117ad80b84beb9dbda195d27f7a9138d77c4        refs/tags/13.28.1^{}
# 6bea87c4e869475fbc87b65a242d8cacf6d8b675        refs/tags/13.29.0
# 43da508b25bcafb348189fb1720ab6356406ef81        refs/tags/13.29.0^{}
# ba2d0981f0f9ddd5c788e3df6ee9fd60e6c48d51        refs/tags/13.29.0-rc1
# ba89536b5133ce85d2b61e5a2024e6c608129537        refs/tags/13.29.0-rc1^{}
# b673477c243dbf93dc7deb46e9a187c543ab06d5        refs/tags/13.29.0-rc2
# 7e2a0b5be256c29ffc720ec0b7a84553f0e222ce        refs/tags/13.29.0-rc2^{}
# 62a0ec48b9271b654e2fe154f09f2d0bcc832a7a        refs/tags/13.29.1
# fb53d3a79072ed172de6a0b88b801fdf9131d079        refs/tags/13.29.1^{}
# 536e4876786bba0e412dbb2ba251cc20573f8d0b        refs/tags/13.29.2
# 1863c35fc3f888d726e54e8674ec78a7cd099e34        refs/tags/13.29.2^{}
# c13803f4b48e107e318bd652ae9ce84b6d264c81        refs/tags/13.3.0
# e3830dec049a6b5316bcd609691df7c2d71ed4b8        refs/tags/13.3.0-rc1
# d6560cf707793d6945dbb4fae08e242edcee0efb        refs/tags/13.3.1
# f6ad2915b308e4132df613dce59d994656f7b7a8        refs/tags/13.3.2
# e8a1f5b98beecf5bd3990235cae0747690ba5f51        refs/tags/13.30.0
# 2262caf68c5ecbe58a52bde1bdd206c6239373bb        refs/tags/13.30.0^{}
# ecd67b3f08b7bca0259551fff143ef62e2e0359c        refs/tags/13.30.0-rc1
# ae6218a39e88426dd01d143d23c882743a750c80        refs/tags/13.30.0-rc1^{}
# 75693aed1dee882ff26c53c1b0b2a60907349992        refs/tags/13.30.0-rc2
# 3f757f22f5338d3091040f363456a4746456d101        refs/tags/13.30.0-rc2^{}
# 2522efa7ff6aa74e02047af5093bd03543ad52ea        refs/tags/13.4.0
# 933356d01000d7554810d34457a86e6d629fb026        refs/tags/13.4.0^{}
# 63d46b4e7a9b022b2cc8f870c9598afc57111677        refs/tags/13.4.0-rc1
# 7e8d5c6b50e1c25639e15d81718ff7095c406334        refs/tags/13.5.0
# 1639644ba71c01a03ceec06da8899b9dad62818c        refs/tags/13.5.0^{}
# 59b6e5db769d77f5f2ba41869fbcab0ae6e98696        refs/tags/13.5.0-rc1
# 7aac620a80f536634ae5560069483a3a7d25fedc        refs/tags/13.6.0
# 56487be6d9d0f9fbb0d46c97c7f84b1c0a0ec34c        refs/tags/13.6.0^{}
# a0fb436eda914dca26e96d304d3c9daca2be54de        refs/tags/13.6.0-rc1
# c3521e9469f95b962e52edbbb6e0cdef6d3ceab4        refs/tags/13.6.0-rc2
# d72dab4f402c06b304e339f4e8fd801b502cb003        refs/tags/13.6.0-rc3
# f3a578ce98f33b7302fca71066e96ab581aa5167        refs/tags/13.7.0
# 4efe7bf05179c25b96c6a0dea401d4847c7737af        refs/tags/13.7.0-rc1
# 7792775db142f515b2701e41ee25ae699ad57e4f        refs/tags/13.7.0-rc2
# 27f82f20306c76c7da11a1ac78cbd9923615594d        refs/tags/13.7.0-rc3
# 211d2836de28a51a91c1cb27f1ab16eba05c9b51        refs/tags/13.7.1
# 87018aaaf415ce16dd53f971875f7764efffe8af        refs/tags/13.7.2
# 7032890c9e21d69a628b40612aa3d86147c542d9        refs/tags/13.7.2^{}
# 2be408b40541c3873e2b9032ab3db05f0cfea9d4        refs/tags/13.8.0
# fad0410486b3a47743331f14fcb565b79357887c        refs/tags/13.8.0^{}
# 06f5ace1fa80ce0799c6d25954de2236a1f842c8        refs/tags/13.8.0-rc1
# 189466671e741802b7d360e651dfc545056ead0c        refs/tags/13.8.1
# 38bcf1f534a97acf185721246e2a157d487519ab        refs/tags/13.8.1^{}
# 8d3e0203f2a92f7840b62575b5176a116fac2117        refs/tags/13.8.2
# f7a90393ae25476a3e3b17ebc86a176a9ef98ce2        refs/tags/13.8.2^{}
# 921ea18c710dfd60090dc0c85630325d6e5e751c        refs/tags/13.9.0
# cc1106a06ac487e54c8222f30b6cc477d90986e1        refs/tags/13.9.0^{}
# 2423d4a1015163b918e50c7d25f197ffb909ebfe        refs/tags/13.9.0-rc1
# 0447d28fbd625334bdac49a8bcb7005e086195f9        refs/tags/13.9.0-rc1^{}
# 31e6f0fa8d590516e07d82294f03e155589becd8        refs/tags/13.9.0-rc2
# 435c2a12d4deda6d7a12a923110e68a46af288c1        refs/tags/13.9.0-rc2^{}
# 87cc63bd63fa42405a9cecda2d970c1491b34ff7        refs/tags/13.9.1
# fbdaade2645d954d9bd0191dd60a218acfa93ba1        refs/tags/13.9.1^{}
# df5493573af6efba1fb8ec7f852e85b611eb2fcc        refs/tags/certified/13.1-cert1
# 50f4abc37b36d878e27ad940c83c14a9fc39838f        refs/tags/certified/13.1-cert1-rc1
# d7ab04813b6c110614fbf5c19df9c32b72437396        refs/tags/certified/13.1-cert1-rc2
# fecd26298f9bbfee4ca567bbf915d63f515e189a        refs/tags/certified/13.1-cert1-rc3
# be6c0a782600491955cffa43497b3db78262299a        refs/tags/certified/13.1-cert2
# 9931aa6c6ff8554881f52d83108e9ffada85e184        refs/tags/certified/13.1-cert3
# 551012e5579f9dddfb4607301b7169974c8c8da4        refs/tags/certified/13.1-cert3-rc1
# 1c7db3df43a6744ef9458fd2b9c0702d5e3cd1e5        refs/tags/certified/13.1-cert3-rc1^{}
# 9ff436be75f2e36ec85a11e7624c0775101a17d0        refs/tags/certified/13.1-cert4
# d50b5d4f4c312db9258fd5c76ab21591690e2c2e        refs/tags/certified/13.1-cert4^{}
# 72d44acaabe37ba95216a867089c69dabdc1a38a        refs/tags/certified/13.1-cert5
# 7b599be0d69ab2054e7ae3f69108137304d2beb3        refs/tags/certified/13.1-cert5^{}
# 00e683e5d5b19edd9281a220a8eef5d5bd88bab0        refs/tags/certified/13.1-cert6
# 1bd1bd1178af16e6c04b39090a35ee03c37cc252        refs/tags/certified/13.1-cert6^{}
# 01c8e229d507539def1304f552884ca64c2f5e5b        refs/tags/certified/13.1-cert7
# 2f9e79aa6fefcfac5caafb1db8e5237122860a6e        refs/tags/certified/13.1-cert7^{}
# 30ecfe2bb97f191493e680268db55de09c260d8e        refs/tags/certified/13.1-cert8
# 7ce04c1641d67df68eac94c5bf5f8aff8fd44d43        refs/tags/certified/13.1-cert8^{}
# 24eed1089e3e81d09d6a9f13ec9a571d98ee7f5d        refs/tags/certified/13.13-cert1
# 7d9a0a89df7e81b6bc821e92ebdda56e7f865a4b        refs/tags/certified/13.13-cert1^{}
# 3eca6846feaed29e6b1b0008d365875f5d2e23f1        refs/tags/certified/13.13-cert1-rc1
# 33a0d64eab3db2dc863b37ce693f32e7a8fc3202        refs/tags/certified/13.13-cert1-rc1^{}
# d9b23f8f5e48199f6e947f4bce5355693fe41d8f        refs/tags/certified/13.13-cert1-rc2
# 92876c1c2a7c361108df6586387a208f67bec1cd        refs/tags/certified/13.13-cert1-rc2^{}
# d09e38f14ec2798a0c49632aaee9096cb581da5d        refs/tags/certified/13.13-cert1-rc3
# 47febcb9277f71089d4c072145b8e0d1b8338415        refs/tags/certified/13.13-cert1-rc3^{}
# e8ef10c96f57255ab0866908be7f013b06725fe1        refs/tags/certified/13.13-cert1-rc4
# 0ef6b6960d1c46b62df9974294392192c1398adf        refs/tags/certified/13.13-cert1-rc4^{}
# 757b3abb62781c83e8c07f9db38c4f610440c3ac        refs/tags/certified/13.13-cert2
# c1b521ad109122b09202e0cbf4018495bed6243b        refs/tags/certified/13.13-cert2^{}
# c4a8ebb48bb815b758e680c47c9f821b3c478f0b        refs/tags/certified/13.13-cert3
# 7e17de3d6634bcfcafe3e688807665e404580475        refs/tags/certified/13.13-cert3^{}
# 0408d3b5bb996a3c77584fed0f15d570330a5bc1        refs/tags/certified/13.13-cert4
# f3969e49d194467a3cf5316c6ab6d5d9db2eba41        refs/tags/certified/13.13-cert4^{}
# db3004f085003811414026fb8e593856f7e2524c        refs/tags/certified/13.13-cert5
# c37d4abe63e0a37d659da04e3726ba687d4ef9f2        refs/tags/certified/13.13-cert5^{}
# d01c30b57eaadccb0d6e43415e82927438677654        refs/tags/certified/13.13-cert6
# 1ee2ce8c703dd763d1779a877099640bb5cd46d0        refs/tags/certified/13.13-cert6^{}
# db73268b2ed8fb31009b7802fcbb8b4584f94d15        refs/tags/certified/13.13-cert7
# b8d1c8787e1cb329d294508a7d3f5d13da76216c        refs/tags/certified/13.13-cert7^{}
# bcb30ab14a48777806c41e32e896cda46ba09307        refs/tags/certified/13.13-cert8
# 3a76c2b0a9a51a0b80eaa8fea25ce728eb7db031        refs/tags/certified/13.13-cert8^{}
# 20dd33d78e318109a10601befbabad1aac3b861d        refs/tags/certified/13.13-cert9
# 9e5d6d7eb22a7e6af65406584c21d0b702dd92c3        refs/tags/certified/13.13-cert9^{}
# 4cb08c38147fb901353e53f6997019fbe1894c5f        refs/tags/certified/13.18-cert1
# b7607c41e4825490ffea9d09c0b3b8f9d65f87c0        refs/tags/certified/13.18-cert1^{}
# 2160406caaca5dcb5b738cd6bdc7c050d7268a1f        refs/tags/certified/13.18-cert1-rc1
# 3984942b1385ded4c21f8d6a4239afe5a8289760        refs/tags/certified/13.18-cert1-rc1^{}
# 9b54851c6cebef8e85f633a286aa2a8e67f53ccb        refs/tags/certified/13.18-cert1-rc2
# b64d924e1cab7924f6d7687d22ea0e28557b23d7        refs/tags/certified/13.18-cert1-rc2^{}
# 1a13467d0ed320fcb1a22f5875192a4fbfe22356        refs/tags/certified/13.18-cert1-rc3
# 673d7d081e18d7d6ab2a110df6375c934433f8ee        refs/tags/certified/13.18-cert1-rc3^{}
# ccfb83a71e263db67511869c3b81331160ae4fae        refs/tags/certified/13.18-cert2
# 9f9c03d928110b9636506f6bc7a8f88c5c315a71        refs/tags/certified/13.18-cert2^{}
# d78dc970b762cf2b311e67b77f51773c45c307a3        refs/tags/certified/13.18-cert3
# eff7fd8517df53cc2e5b01f0c7beb1c721a8796b        refs/tags/certified/13.18-cert3^{}
# 94ca35b0afdb236b814448d63f7181385d7b60bd        refs/tags/certified/13.18-cert4
# 07c49ec7b8fad91c5b5118775986c9e09a019cc5        refs/tags/certified/13.18-cert4^{}
# 50177839272ddffa0f1141167f69a02320177821        refs/tags/certified/13.21-cert1
# d661052e6d2eddae58bec5a04229c105d11e18f4        refs/tags/certified/13.21-cert1^{}
# 33d7af61469df48a77d486bc9a61cb880e1fcaa7        refs/tags/certified/13.21-cert1-rc1
# a9315f8d1a0e83f728fc70648f3c72a0c8bf6699        refs/tags/certified/13.21-cert1-rc1^{}
# 4f411f0b2d2889a90b314c43b7742da58ad81804        refs/tags/certified/13.21-cert1-rc2
# 474a6af80b583236e4f98723b0b9b74b25ad1b7d        refs/tags/certified/13.21-cert1-rc2^{}
# d4c24f67714c90fd29e1df3f6165b7b4c1a0f343        refs/tags/certified/13.21-cert2
# 742007f881f8cb04fe543fba4dbe5404589d9f14        refs/tags/certified/13.21-cert2^{}
# f1ea60e8ec1a428100aef0d8e1b9b632e3b0e7f7        refs/tags/certified/13.21-cert3
# ab699aa653ffbf9efe11fef940dd2cb0a80b075e        refs/tags/certified/13.21-cert3^{}
# 1ee8f55cb46677f6bbcde34610d1edf403d48c3a        refs/tags/certified/13.21-cert4
# bb3e299589a06b7cf5bdd06a117332eaf3cf0f4d        refs/tags/certified/13.21-cert4^{}
# 3012c65d56f081525bd3c4cbcaa63870c61cf967        refs/tags/certified/13.21-cert5
# f614f3c146543b7d6d4ba4b93b02515a760e4e9d        refs/tags/certified/13.21-cert5^{}
# 974cc4b00a6afc533665f9c47211f675bd73e927        refs/tags/certified/13.21-cert6
# a8b7b407f9a3f1c12d0aa03761cd32b550d6a140        refs/tags/certified/13.21-cert6^{}
# b61d687fd950e012392bbd695ff697735992931b        refs/tags/certified/13.8-cert1
# 45e0392397605b8c8d0d975c63e21dd7b2c951de        refs/tags/certified/13.8-cert1^{}
# 40b316663b723e23a82ad4a817ee4ae084292a57        refs/tags/certified/13.8-cert1-rc1
# dd93204a84785a1898042b46cd16db5b3013a141        refs/tags/certified/13.8-cert1-rc1^{}
# 76e001992bb971e6f57a06ca586af244cf9fd266        refs/tags/certified/13.8-cert1-rc2
# 601602f44b72c20a265d39f217eeda3d335712e9        refs/tags/certified/13.8-cert1-rc2^{}
# d41617c88fc975b2696eb9a61f1920d9cf9d331d        refs/tags/certified/13.8-cert1-rc3
# f282a88ee4b50a03848555604392314f1b00b6d4        refs/tags/certified/13.8-cert1-rc3^{}
# 0973a5aabdeb5366fcd1d3b126add7a974c864f1        refs/tags/certified/13.8-cert2
# ac0f73694b59317f776ea2f4b8f777327def154e        refs/tags/certified/13.8-cert2^{}
# ddec81a1ff3b4a1a15697802058de7886652c339        refs/tags/certified/13.8-cert2-rc1
# acf021cdec4d45f56aeb9bc87c08a00870f8a6a8        refs/tags/certified/13.8-cert2-rc1^{}
# 891ad438ba999eb60738c568810887039c252aa0        refs/tags/certified/13.8-cert3
# ad7e072a6d32dc0468fa08daa86bf302a7c057ab        refs/tags/certified/13.8-cert3^{}
# 9527a018582a96cebf2621be569c7d5c342f1bfa        refs/tags/certified/13.8-cert4
# f0955f190a42e5c1ca20080d9e34d19c3c1b8646        refs/tags/certified/13.8-cert4^{}
# EndOfMessage
# )"
#     hiddeninstallationmodellistgitremote "${git_raw_tags_string}" "refs/tags/" "30";
#     printf "\\n"
# }


# https://stackoverflow.com/questions/4175264/bash-retrieve-absolute-path-given-relative
function getabsolutepath() {
    local target;
    local changedir;
    local basedir;
    local firstattempt;

    target="${1}";
    if [ "w$target" == "w." ];
    then
        printf "%s" "$(pwd)";

    elif [ "w$target" == "w.." ];
    then
        printf "%s" "$(dirname "$(pwd)")";

    else
        changedir="$(dirname "${target}")" && basedir="$(basename "${target}")" && firstattempt="$(cd "${changedir}" && pwd)" && printf "%s/%s" "${firstattempt}" "${basedir}" && return 0;
        firstattempt="$(readlink -f "${target}")" && printf "%s" "${firstattempt}" && return 0;
        firstattempt="$(realpath "${target}")" && printf "%s" "${firstattempt}" && return 0;

        # If everything fails... TRHOW PYTHON ON IT!!!
        local fullpath;
        local pythoninterpreter;
        local pythonexecutables;
        local pythonlocations;

        pythoninterpreter="python";
        declare -a pythonlocations=("/usr/bin" "/bin");
        declare -a pythonexecutables=("python" "python2" "python3");

        for path in "${pythonlocations[@]}";
        do
            for executable in "${pythonexecutables[@]}";
            do
                fullpath="${path}/${executable}";

                if [[ -f "${fullpath}" ]];
                then
                    # printf "Found ${fullpath}\\n";
                    pythoninterpreter="${fullpath}";
                    break;
                fi;
            done;

            if [[ "w${pythoninterpreter}" != "wpython" ]];
            then
                # printf "Breaking... ${pythoninterpreter}\\n"
                break;
            fi;
        done;

        firstattempt="$(${pythoninterpreter} -c "import os, sys; print( os.path.abspath( sys.argv[1] ) );" "${target}")" && printf "%s" "${firstattempt}" && return 0;
        # printf "Error: Could not determine the absolute path!\\n";
        return 1;
    fi
}


hiddeninstallationmodelpythonsortprogram="$(cat << EndOfMessage
import sys
from natsort import natsorted

def sort_alphabetically_and_by_length(iterable):
    """ https://stackoverflow.com/questions/4659524/how-to-sort-by-length-of-string-followed-by-alphabetical-order """
    return natsorted( iterable, key=lambda item: str( item ).lower() )

lines = sys.argv[1].split( '\\n' )
# sys.stderr.write( "lines: %s\n\n" % lines )

sorted_lines = sort_alphabetically_and_by_length( lines )
# sys.stderr.write( "sorted_lines: %s\n\n" % sorted_lines )

text = '\n'.join( sorted_lines )
print( text )
EndOfMessage
)";
