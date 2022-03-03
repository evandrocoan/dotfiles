#!/bin/bash
PER_COMPUTER_SETTINGS=~/.per_computer_settings.sh

# linux@linux:(master)/root$ sudo apt ...
# https://stackoverflow.com/questions/37021988/conditional-space-in-ps1
# https://github.com/git/git/blob/master/contrib/completion/git-prompt.sh
# https://gist.github.com/justintv/168835 - Display git branch in bash prompt
if [ -z "${__git_ps1}" ];
then
    function __git_ps1() {
        :;
    }

    # To update it:
    # wget https://raw.githubusercontent.com/git/git/master/contrib/completion/git-prompt.sh -O ~/.local/git-prompt.sh
    if [ -f ~/.local/git-prompt.sh ];
    then
        source ~/.local/git-prompt.sh;
    fi
fi

# Import variable settings bound to each computer machine
if [[ -f "$PER_COMPUTER_SETTINGS" ]]
then
    source "$PER_COMPUTER_SETTINGS"
else
    printf '%s\n' '#!/bin/bash' >> "$PER_COMPUTER_SETTINGS"
    printf '%s\n' '# See "~/.bashrc"' >> "$PER_COMPUTER_SETTINGS"
    printf '%s\n' >> "$PER_COMPUTER_SETTINGS"
    printf '%s\n' '# # Windows only' >> "$PER_COMPUTER_SETTINGS"
    printf '%s\n' '# PATH=$PATH:"$(cygpath -u "$PROGRAMFILES")/Git"' >> "$PER_COMPUTER_SETTINGS"
    printf '%s\n' >> "$PER_COMPUTER_SETTINGS"
    printf '%s\n' '# # Computer dependent, put them on `.per_computer_settings.sh`'  >> "$PER_COMPUTER_SETTINGS"
    printf '%s\n' '# # Add the current tools to the bash path when running on portable mode.'  >> "$PER_COMPUTER_SETTINGS"
    printf '%s\n' '# PATH="$PATH:$(cygpath -u "$PROGRAMFILES")/Git:/cygdrive/l/someprogram"'  >> "$PER_COMPUTER_SETTINGS"
    printf '%s\n' '# PATH="~/.local/bin:$PATH"'  >> "$PER_COMPUTER_SETTINGS"
    printf '%s\n' >> "$PER_COMPUTER_SETTINGS"
    printf '%s\n' >> '# export LOCAL_COMPUTER_SSH=user@computer'
    printf '%s\n' >> "$PER_COMPUTER_SETTINGS"
    printf '%s\n' '# mkdir -p "$(cygpath -u "$USERPROFILE")/Downloads"'  >> "$PER_COMPUTER_SETTINGS"

    # https://stackoverflow.com/questions/1250079/how-to-escape-single-quotes-within-single-quoted-strings
    printf '%s\n' '# alias ~~='"'"'cd "$(cygpath -u "$USERPROFILE")/Downloads"'"'"''  >> "$PER_COMPUTER_SETTINGS"
    printf '%s\n' >> "$PER_COMPUTER_SETTINGS"
    printf '%s\n' '# https://stackoverflow.com/questions/23929235/multi-line-string-with-extra-space-preserved'  >> "$PER_COMPUTER_SETTINGS"
    printf '%s\n' 'run_post_rules_for_per_computer_settings=$(cat << EndOfMessage'  >> "$PER_COMPUTER_SETTINGS"
    printf '%s\n' >> "$PER_COMPUTER_SETTINGS"
    printf '%s\n' '    # # linux@linux:(master)/root$ echo hi' >> "$PER_COMPUTER_SETTINGS"

    # https://stackoverflow.com/questions/1250079/how-to-escape-single-quotes-within-single-quoted-strings
    # https://www.programiz.com/python-programming/datetime/strftime
    printf '%s\n' '    # export PS1='"'"'\D{%j %H:%M:%S} ${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:$(__git_ps1 "(\[\033[01;35m\]%s\[\033[01;35m\]\[\033[00m\])")\[\033[01;34m\]\w\[\033[00m\]\$ '"'"'' >> "$PER_COMPUTER_SETTINGS"
    printf '%s\n' 'EndOfMessage'  >> "$PER_COMPUTER_SETTINGS"
    printf '%s\n' ')'  >> "$PER_COMPUTER_SETTINGS"
    printf '%s\n' >> "$PER_COMPUTER_SETTINGS"
fi

# Prefix a command with start to run it detached from the terminal.
function run_disowned() {
    "$@" &
}

function start() {
    # run_disowned and silenced

    run_disowned "$@" 1>/dev/null 2>/dev/null
}


XPROFILE_FILE=~/.xprofile
IS_X_PROFILE_LOADED_ON_FIRST_BOOT=/tmp/is_x_profile_loaded_on_first_boot.txt

if [[ -f "$XPROFILE_FILE" ]] && [[ ! -f "$IS_X_PROFILE_LOADED_ON_FIRST_BOOT" ]];
then
    source "$XPROFILE_FILE";
    printf 'yes' > "$IS_X_PROFILE_LOADED_ON_FIRST_BOOT";
fi;


if ! command -v "sudo" >/dev/null 2>&1; then
    alias sudo="printf 'Warning: Running as current user\n';"
fi

# Invoke octave from command line, add the option -q to run without the intro.
alias octave='octave --no-gui -i'


# Somehow python was not opening on interactive mode by default
# alias python='python -i'

# https://stackoverflow.com/questions/15384025/bash-git-ps1-command-not-found/17508424
# https://stackoverflow.com/questions/12870928/mac-bash-git-ps1-command-not-found
source ~/.local/git-prompt.sh

# https://askubuntu.com/questions/63424/how-to-change-tab-width-in-terminal-in-ubuntu-10-04
[[ $- == *i* ]] && tabs -4

PROMPT_COMMAND='echo -ne "\033]0;${USER}@${HOSTNAME}: ${PWD}\007"'

# http://www.linuxjournal.com/content/using-bash-history-more-efficiently-histcontrol
#
# Another alternative is to tell bash not to store duplicates. This is done with the HISTCONTROL
# variable. HISTCONTROL controls how bash stores command history. Currently there are two possible
# flags: ignorespace and ignoredups. The ignorespace flag tells bash to ignore commands that start
# with spaces. The other flag, ignoredups, tells bash to ignore duplicates. You can concatenate and
# separate the values with a colon, ignorespace:ignoredups, if you wish to specify both values, or
# you can just specify ignoreboth.
# export HISTCONTROL=ignoredups:erasedups  # no duplicate entries
# export HISTSIZE=100000                   # big big history
# export HISTFILESIZE=100000               # big big history
# shopt -s histappend                      # append to history, don't overwrite it

# Save and reload the history after each command finishes
# https://unix.stackexchange.com/questions/1288/preserve-bash-history-in-multiple-terminal-windows
# Consistent and forever bash history
HISTSIZE=100000
HISTFILESIZE=$HISTSIZE
HISTCONTROL=ignoredups:erasedups

_bash_history_sync() {
  builtin history -a         #1
  HISTFILESIZE=$HISTSIZE     #2
}

_bash_history_sync_and_reload() {
  builtin history -a         #1
  HISTFILESIZE=$HISTSIZE     #2
  builtin history -c         #3
  builtin history -r         #4
}

history() {                  #5
  _bash_history_sync_and_reload
  builtin history "$@"
}

export HISTTIMEFORMAT="%y/%m/%d %H:%M:%S   "
PROMPT_COMMAND='history 1 >> ${HOME}/.bash_eternal_history'
PROMPT_COMMAND=_bash_history_sync;$PROMPT_COMMAND
# PROMPT_COMMAND="${PROMPT_COMMAND:+$PROMPT_COMMAND$'\n'}history -a; history -c; history -r"

# https://unix.stackexchange.com/questions/73498/how-to-cycle-through-reverse-i-search-in-bash
# https://stackoverflow.com/questions/24623021/getting-stty-standard-input-inappropriate-ioctl-for-device-when-using-scp-thro
[[ $- == *i* ]] && stty -ixon

alias clc='reset;clear;clear;'
# alias where='locate -b'


#export CYGWIN="$CYGWIN error_start=dumper -d %1 %2"

# To the extent possible under law, the author(s) have dedicated all
# copyright and related and neighboring rights to this software to the
# public domain worldwide. This software is distributed without any warranty.
# You should have received a copy of the CC0 Public Domain Dedication along
# with this software.
# If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.

# base-files version 4.2-3

# ~/.bashrc: executed by bash(1) for interactive shells.

# The latest version as installed by the Cygwin Setup program can
# always be found at /etc/defaults/etc/skel/.bashrc

# Modifying /etc/skel/.bashrc directly will prevent
# setup from updating it.

# The copy in your home directory (~/.bashrc) is yours, please
# feel free to customise it to create a shell
# environment to your liking.  If you feel a change
# would be benifitial to all, please feel free to send
# a patch to the cygwin mailing list.

# User dependent .bashrc file

# If not running interactively, don't do anything
# case $- in
#     *i*) ;;
#       *) return;;
# esac
[[ "$-" != *i* ]] && return

# Shell Options
#
# See man bash for more options...
#
# Don't wait for job termination notification
# set -o notify
#
# Don't use ^D to exit
# set -o ignoreeof
#
# Use case-insensitive filename globbing
# shopt -s nocaseglob

#
# When changing directory small typos can be ignored by bash
# for example, cd /vr/lgo/apaache would find /var/log/apache
# shopt -s cdspell

# Completion options
#
# These completion tuning parameters change the default behavior of bash_completion:
#
# Define to access remotely checked-out files over passwordless ssh for CVS
# COMP_CVS_REMOTE=1
#
# Define to avoid stripping description in --option=description of './configure --help'
# COMP_CONFIGURE_HINTS=1
#
# Define to avoid flattening internal contents of tar files
# COMP_TAR_INTERNAL_PATHS=1
#
# Uncomment to turn on programmable completion enhancements.
# Any completions you add in ~/.bash_completion are sourced last.
# [[ -f /etc/bash_completion ]] && . /etc/bash_completion

# History Options
#
# Don't put duplicate lines in the history.
# export HISTCONTROL=$HISTCONTROL${HISTCONTROL+,}ignoredups
#
# Ignore some controlling instructions
# HISTIGNORE is a colon-delimited list of patterns which should be excluded.
# The '&' is a special pattern which suppresses duplicate entries.
# export HISTIGNORE=$'[ \t]*:&:[fb]g:exit'
# export HISTIGNORE=$'[ \t]*:&:[fb]g:exit:ls' # Ignore the ls command as well
#
# Whenever displaying the prompt, write the previous line to disk
# export PROMPT_COMMAND="history -a"

# Aliases
#
# Some people use a different file for aliases
# if [ -f "${HOME}/.bash_aliases" ]; then
#   source "${HOME}/.bash_aliases"
# fi
#
# Some example alias instructions
# If these are enabled they will be used instead of any instructions
# they may mask.  For example, alias rm='rm -i' will mask the rm
# application.  To override the alias instruction use a \ before, ie
# \rm will call the real rm not the alias.
#
# Interactive operation...
# alias rm='rm -i'
# alias cp='cp -i'
# alias mv='mv -i'

# Verbose operation...
# alias rm='rm -v'
# alias cp='cp -v'
# alias mv='mv -v'

# Umask
#
# /etc/profile sets 022, removing write perms to group + others.
# Set a more restrictive umask: i.e. no exec perms for others:
# umask 027
# Paranoid: neither group nor others have any perms:
# umask 077

# Functions
#
# Some people use a different file for functions
# if [ -f "${HOME}/.bash_functions" ]; then
#   source "${HOME}/.bash_functions"
# fi
#
# Some example functions:
#
# a) function settitle
# settitle ()
# {
#   echo -ne "\e]2;$@\a\e]1;$@\a";
# }
#
# b) function cd_func
# This function defines a 'cd' replacement function capable of keeping,
# displaying and accessing history of visited directories, up to 10 entries.
# To use it, uncomment it, source this file and try 'cd --'.
# acd_func 1.0.5, 10-nov-2004
# Petar Marinov, http:/geocities.com/h2428, this is public domain
# cd_func ()
# {
#   local x2 the_new_dir adir index
#   local -i cnt
#
#   if [[ $1 ==  "--" ]]; then
#     dirs -v
#     return 0
#   fi
#
#   the_new_dir=$1
#   [[ -z $1 ]] && the_new_dir=$HOME
#
#   if [[ ${the_new_dir:0:1} == '-' ]]; then
#     #
#     # Extract dir N from dirs
#     index=${the_new_dir:1}
#     [[ -z $index ]] && index=1
#     adir=$(dirs +$index)
#     [[ -z $adir ]] && return 1
#     the_new_dir=$adir
#   fi
#
#   #
#   # '~' has to be substituted by ${HOME}
#   [[ ${the_new_dir:0:1} == '~' ]] && the_new_dir="${HOME}${the_new_dir:1}"
#
#   #
#   # Now change to the new dir and add to the top of the stack
#   pushd "${the_new_dir}" > /dev/null
#   [[ $? -ne 0 ]] && return 1
#   the_new_dir=$(pwd)
#
#   #
#   # Trim down everything beyond 11th entry
#   popd -n +11 2>/dev/null 1>/dev/null
#
#   #
#   # Remove any other occurence of this dir, skipping the top of the stack
#   for ((cnt=1; cnt <= 10; cnt++)); do
#     x2=$(dirs +${cnt} 2>/dev/null)
#     [[ $? -ne 0 ]] && return 0
#     [[ ${x2:0:1} == '~' ]] && x2="${HOME}${x2:1}"
#     if [[ "${x2}" == "${the_new_dir}" ]]; then
#       popd -n +$cnt 2>/dev/null 1>/dev/null
#       cnt=cnt-1
#     fi
#   done
#
#   return 0
# }
#
# alias cd=cd_func




# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# If set, the pattern "**" used in a pathname expansion context will
# match all files and zero or more directories and subdirectories.
#shopt -s globstar

# make less more friendly for non-text input files, see lesspipe(1)
[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
    xterm-color) color_prompt=yes;;
    screen-256color) color_prompt=yes;;
esac

# uncomment for a colored prompt, if the terminal has the capability; turned
# off by default to not distract the user: the focus in a terminal window
# should be on the output of commands, not on the prompt
force_color_prompt=yes

if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
        # We have color support; assume it's compliant with Ecma-48
        # (ISO/IEC-6429). (Lack of such support is extremely rare, and such
        # a case would tend to support setf rather than setaf.)
        color_prompt=yes
    else
        color_prompt=
    fi
fi

if [ "$color_prompt" = yes ];
then
    # https://unix.stackexchange.com/questions/1045/getting-256-colors-to-work-in-tmux
    export TERM=xterm-256color

    # linux@linux:(master)/root$ echo hi
    # https://www.tecmint.com/customize-bash-colors-terminal-prompt-linux/
    export PS1='\D{%j %H:%M:%S} ${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:$(__git_ps1 "(\[\033[01;35m\]%s\[\033[01;35m\]\[\033[00m\])")\[\033[01;34m\]\w\[\033[00m\]\$ '
else
    # https://www.programiz.com/python-programming/datetime/strftime
    export PS1='\D{%j %H:%M:%S} ${debian_chroot:+($debian_chroot)}\u@\h:$(__git_ps1 "(%s)")\w\$ '
fi
unset color_prompt force_color_prompt


# Default to human readable figures
# alias df='df -h'
# alias du='du -h'
#
# Misc :)
# alias less='less -r'                          # raw control characters
# alias whence='type -a'                        # where, of a sort

#
# Some shortcuts for different directory listings
# alias ls='ls -hF --color=tty'                 # classify files in colour
# alias dir='ls --color=auto --format=vertical'
# alias vdir='ls --color=auto --format=long'
# alias ll='ls -l'                              # long list
# alias la='ls -A'                              # all but . and ..
# alias l='ls -CF'                              #

#alias ls='ls -a -A --color=auto' # --group-directories-first'
#alias ll='ls -lh'


# enable color support of ls and also add handy aliases
if [ -x /usr/bin/dircolors ]; then
    alias ls='ls --color=auto'
    alias dir='dir --color=auto'
    alias vdir='vdir --color=auto'

    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'

    # dircolors: modify color settings globaly
    # https://unix.stackexchange.com/questions/94299/dircolors-modify-color-settings-globaly
    #
    # how to change colors of ls listing?
    # http://www.linuxquestions.org/questions/linux-newbie-8/how-to-change-colors-of-ls-listing-301378/
    if [ -f "/etc/dircolors" ]
    then
        eval "$(dircolors -b /etc/dircolors)"
    fi

    if [ -f "$HOME/.dircolors" ]
    then
        eval "$(dircolors -b "$HOME/.dircolors")"
    fi
fi

# Missing colors from `dircolors` export
# http://www.bigsoft.co.uk/blog/index.php/2008/04/11/configuring-ls_colors
#
# no  NORMAL, NORM           Global default, although everything should be something
# fi  FILE                   Normal file
# di  DIR Directory
# ln  SYMLINK, LINK, LNK     Symbolic link. If you set this to ‘target’ instead of a numerical value, the color is as for the file pointed to.
# pi  FIFO, PIPE             Named pipe
# do  DOOR                   Door
# bd  BLOCK, BLK             Block device
# cd  CHAR, CHR              Character device
# or  ORPHAN                 Symbolic link pointing to a non-existent file
# so  SOCK                   Socket
# su  SETUID                 File that is setuid (u+s)
# sg  SETGID                 File that is setgid (g+s)
# tw  STICKY_OTHER_WRITABLE  Directory that is sticky and other-writable (+t,o+w)
# ow  OTHER_WRITABLE         Directory that is other-writable (o+w) and not sticky
# st  STICKY                 Directory with the sticky bit set (+t) and not other-writable
# ex  EXEC                   Executable file (i.e. has ‘x’ set in permissions)
# mi  MISSING                Non-existent file pointed to by a symbolic link (visible when you type ls -l)
# lc  LEFTCODE, LEFT         Opening terminal code
# rc  RIGHTCODE, RIGHT       Closing terminal code
# ec  ENDCODE, END           Non-filename text
# *.extension                Every file using this extension e.g. *.jpg
#
LS_COLORS=$LS_COLORS':fi=93'
LS_COLORS=$LS_COLORS':ex=31'
LS_COLORS=$LS_COLORS':ln=01;36'
LS_COLORS=$LS_COLORS':di=01;34'
LS_COLORS=$LS_COLORS':tw=01;34' # ls --color=auto rendering directory color as file color
LS_COLORS=$LS_COLORS':ow=01;34' # https://github.com/Microsoft/BashOnWindows/issues/2343
LS_COLORS=$LS_COLORS':*.sh=00;31'
LS_COLORS=$LS_COLORS':*.exe=00;31'
LS_COLORS=$LS_COLORS':*.bat=00;31'
LS_COLORS=$LS_COLORS':*.com=00;31'
export LS_COLORS

# Using trial and error (and a little bash script I wrote... my first one ever! :) I
# worked out all the colour codes, at least my interpretation of them -
# http://linux-sxs.org/housekeeping/lscolors.html
#
# 0   = default colour
# 1   = bold
# 4   = underlined
# 5   = flashing text
# 7   = reverse field
# 30  = black
# 31  = red
# 32  = green
# 33  = orange/yellow
# 34  = blue
# 35  = purple/magenta
# 36  = cyan
# 37  = grey/white
# 40  = black background
# 41  = red background
# 42  = green background
# 43  = orange background
# 44  = blue background
# 45  = purple background
# 46  = cyan background
# 47  = grey background
# 90  = dark grey
# 91  = light red
# 92  = light green
# 93  = yellow
# 94  = light blue
# 95  = light purple
# 96  = turquoise
# 100 = dark grey background
# 101 = light red background
# 102 = light green background
# 103 = yellow background
# 104 = light blue background
# 105 = light purple background
# 106 = turquoise background
#
# colored GCC warnings and errors
export GCC_COLORS='error=01;31:warning=01;35:note=01;36:caret=01;32:locus=01:quote=01'

# some more ls aliases
alias ll='ls -alF --time-style=full-iso --human-readable'
alias la='ls -A'
alias l='ls -CF'

# Add an "alert" alias for long running commands.  Use like so:
#   sleep 10; alert
alias alert='notify-send --urgency=low -i "$([ $? = 0 ] & startxwin & echo terminal || echo error)" "$(history|tail -n1|sed -e '\''s/^\s*[0-9]\+\s*//;s/[;&|]\s*alert$//'\'')"'

# Alias definitions.
# You may want to put all your additions into a separate file like
# ~/.bash_aliases, instead of adding them here directly.
# See /usr/share/doc/bash-doc/examples in the bash-doc package.

if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi

# enable programmable completion features (you don't need to enable
# this, if it's already enabled in /etc/bash.bashrc and /etc/profile
# sources /etc/bash.bashrc).
if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi

# https://stackoverflow.com/questions/767040/save-last-working-directory-on-bash-logout
# https://superuser.com/questions/19318/how-can-i-give-write-access-of-a-folder-to-all-users-in-linux
trap 'printf "%s" "$(pwd)" > /tmp/last_used_pwd.txt && printf "%s" "${OLDPWD}" > /tmp/last_used_cd.txt || printf "You need to run: sudo chmod -R 777 /tmp/last_used_*\\n";' EXIT

# fix  X11 DISPLAY environment variable not set and allow to use `startxwin`
export DISPLAY=:0

# https://stackoverflow.com/questions/35898734/pip-installs-packages-successfully-but-executables-not-found-from-command-line/35899029
python3 -m site &> /dev/null && PATH="$PATH:`python3 -m site --user-base`/bin"
python2 -m site &> /dev/null && PATH="$PATH:`python2 -m site --user-base`/bin"

# Run `.per_computer_settings` rules which override some other variable on this `.bashrc`
# https://stackoverflow.com/questions/23929235/multi-line-string-with-extra-space-preserved-indentation/36240082
eval "$run_post_rules_for_per_computer_settings"

# If this is an xterm set the title to user@host:dir
case "$TERM" in
xterm*|rxvt*)
    export PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]$PS1"
    ;;
*)
    ;;
esac
