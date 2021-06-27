#!/usr/bin/env bash
set -x

oldvalue="$(xfconf-query -c xsettings -p /Xft/DPI)";

if [[ "$1" == "up" ]];
then
    newvalue="$(( oldvalue + 5 ))"
else
    newvalue="$(( oldvalue - 5 ))"
fi

# https://superuser.com/questions/31917/is-there-a-way-to-show-notification-from-bash-script-in-ubuntu
notify-send -u low -t 3000 "DPI $newvalue"
xfconf-query -c xsettings -p /Xft/DPI -s "$newvalue";
