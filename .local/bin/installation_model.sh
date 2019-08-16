#!/bin/bash
#
# installation_model.sh
# Copyright (c) 2019 Evandro Coan
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

if [[ -z "${thing_name}" ]]; then
    thing_name="toolname";
fi;

if [[ -z "${git_server}" ]]; then
    git_server="https://repo.url.git";
fi;

if [[ -z "${tags_columns_width}" ]]; then
    tags_columns_width="30";
fi;

if [[ -z "${branches_columns_width}" ]]; then
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
    if [[ "${generalexceptiontype}" == "set" ]];
    then
        printf "The last set command '%s=%s' on step '%sº' returned with the error code '%s'...\\n" "${newvariablename}" "${commandline}" "${g_installation_model_command_counter}" "${returncode}";

    elif [[ "${generalexceptiontype}" == "run" ]];
    then
        printf "The last '%sº' command '%s' returned with the error code '%s'...\\n" "${g_installation_model_command_counter}" "${commandline}" "${returncode}";

    else
        printf "ERROR: Invalid option '%s' for the last '%sº' command '%s' returned with the error code '%s'...\\n" "${generalexceptiontype}" "${g_installation_model_command_counter}" "${commandline}" "${returncode}";
        read -e -r -p "Press 'Enter' to continue... " fixcommand;
        return 1;
    fi;

    while [[ "${fixcommand}" != "q" ]];
    do
        printf "\\n";
        printf "Type 'q' and press 'Enter' to continue the main script execution...\\n";

        if [[ "${generalexceptiontype}" == "set" ]];
        then
            printf "Type 'r' to run again the last set command...\\n";
            printf "Type 's' to manually set the '%s' variable value.\\n" "${newvariablename}";
            printf "Type 'e' to edit in memory the '%s=%s' variable set command...\\n" "${newvariablename}" "${commandline}";

        elif [[ "${generalexceptiontype}" == "run" ]];
        then
            printf "Type 'r' and press 'Enter' to repeat the last '%sº' command...\\n" "${g_installation_model_command_counter}";
            printf "Type 'e' to edit in memory the '%sº' command '%s'...\\n" "${g_installation_model_command_counter}" "${commandline}";
        fi;

        printf "Type 'l' to show all commands already run up to step '%sº'...\\n" "${g_installation_model_command_counter}";
        printf "Beyond these options, you can also run any command you would like as 'cd dir', 'ls -la', etc...\\n";
        read -e -r -p "Command: " fixcommand;

        while [[ "w${fixcommand}" == "w" ]];
        do
            printf "ERROR: The fix command cannot be empty. Please, type 'q', 'r' or some other command.\\n";
            read -e -r -p "Command: " fixcommand;
        done;

        if [[ "${fixcommand}" == "q" ]];
        then
            printf "\\n";
            printf "Continuing the main script execution on step '%sº'... (%s)\\n" "${g_installation_model_command_counter}" "$(pwd)";
            return 0;

        elif [[ "${fixcommand}" == "r" ]] && [[ "${generalexceptiontype}" == "run" ]];
        then
            printf "\\n";
            printf "Repeating the last '%sº' command '%s'... (%s)\\n" "${g_installation_model_command_counter}" "${commandline}" "$(pwd)";
            eval "${commandline}" || hiddeninstallationmodelhandlegeneralexception "run" "${commandline}" "${?}";
            return 0;

        elif [[ "${fixcommand}" == "e" ]] && [[ "${generalexceptiontype}" == "run" ]];
        then
            # https://stackoverflow.com/questions/2642585/read-a-variable-in-bash-with-a-default-value
            printf "\\n";
            printf "Editing the last '%sº' command '%s' to... (%s)\\n" "${g_installation_model_command_counter}" "${commandline}" "$(pwd)";
            read -e -r -p "Edit command: " -i "${commandline}" commandline;

            printf "Running the fix comand '%sº' command '%s'... (%s)\\n" "${g_installation_model_command_counter}" "${commandline}" "$(pwd)";
            eval "${commandline}" || hiddeninstallationmodelhandlegeneralexception "run" "${commandline}" "${?}";
            return 0;

        elif [[ "${fixcommand}" == "r" ]] && [[ "${generalexceptiontype}" == "set" ]];
        then
            printf "\\n";
            printf "Repeating the last set command '%s' on step '%sº'... (%s)\\n" "${commandline}" "${g_installation_model_command_counter}" "$(pwd)";
            hiddeninstallationmodelrunsetunexpandable "${newvariablename}" ${commandline};
            return 0;

        elif [[ "${fixcommand}" == "e" ]] && [[ "${generalexceptiontype}" == "set" ]];
        then
            # https://stackoverflow.com/questions/2642585/read-a-variable-in-bash-with-a-default-value
            printf "\\n";
            printf "Editing the last set command '%s' on step '%sº' to... (%s)\\n" "${commandline}" "${g_installation_model_command_counter}" "$(pwd)";
            read -e -r -p "${newvariablename}=" -i "${commandline}" commandline;

            hiddeninstallationmodelrunsetunexpandable "${newvariablename}" ${commandline};
            return 0;

        elif [[ "${fixcommand}" == "s" ]] && [[ "${generalexceptiontype}" == "set" ]];
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

        elif [[ "${fixcommand}" == "l" ]];
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
    g_installation_model_command_counter=$((g_installation_model_command_counter+1));

    # https://stackoverflow.com/questions/56822216/how-to-portability-use-2#56822303
    shift; shift;
    commandline="$(printf '%q ' "${@}" | sed -e 's/[[:space:]]*$//')";
    g_installation_model_commands_ranarray+=("${g_installation_model_command_counter}º ${commandline};");

    printf "\\n";
    printf "Setting the variable '%s' with the command '%s'... (%s)\\n" "${newvariablename}" "${commandline}" "$(pwd)";
    temporary_variable="$(eval "${commandline}" | sed -e 's/[[:space:]]*$//')" || hiddeninstallationmodelhandlegeneralexception "set" "${commandline}" "${?}" "${newvariablename}" || return "${?}";

    eval "${newvariablename}='${temporary_variable}'";
    if [[ "${issilent}" == "yes" ]];
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
    temporary_variable="$(eval "${commandline}" | sed -e 's/[[:space:]]*$//')" || hiddeninstallationmodelhandlegeneralexception "set" "${commandline}" "${?}" "${newvariablename}" || return "${?}";

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

        while [[ "${shouldirun}" != "y" ]] && [[ "${shouldirun}" != "n" ]] && [[ "${shouldirun}" != "q" ]];
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

            if [[ "${shouldirun}" == "q" ]];
            then
                printf "\\n";
                printf "Continuing the main script execution on step '%sº'... (%s)\\n" "${g_installation_model_command_counter}" "$(pwd)";
                return 0;

            elif [[ "${shouldirun}" == "y" ]];
            then
                printf "Running the '%sº' optional command '%s'...\\n" "${g_installation_model_command_counter}" "${commandline}";
                eval "${commandline}" || hiddeninstallationmodelhandlegeneralexception "run" "${commandline}" "${?}";

            elif [[ "${shouldirun}" == "n" ]];
            then
                printf "NOT running the '%sº' optional command '%s'...\\n" "${g_installation_model_command_counter}" "${commandline}";

            elif [[ "${shouldirun}" == "l" ]];
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

    git_raw_string="${1}";
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

        if [[ "${stringarray}" == "${git_filter_string}"* ]];
        then
            stringarraysize="${#git_filter_string}";
            stringarray="${stringarray:${stringarraysize}}";

            if [[ "${stringarray}" != *'^{}' ]];
            then
                # printf "linevariable=$linevariable\\n";
                arrayfilteredlines+=("${stringarray}");
            fi;
        fi;
    done < <(printf "%s\\n" "${git_raw_string}");

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

# https://stackoverflow.com/questions/4175264/bash-retrieve-absolute-path-given-relative
function getabsolutepath() {
    local target;
    local changedir;
    local basedir;
    local firstattempt;

    target="${1}";
    if [ "$target" == "." ];
    then
        printf "%s" "$(pwd)";

    elif [ "$target" == ".." ];
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

            if [[ "${pythoninterpreter}" != "python" ]];
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
