#!/usr/bin/env bash
set -x

oldvalue="$(xfconf-query -c xsettings -p /Xft/DPI)";

if [[ "$1" == "up" ]];
then
    xfconf-query -c xsettings -p /Xft/DPI -s $(( oldvalue + 10 ));
else
    xfconf-query -c xsettings -p /Xft/DPI -s $(( oldvalue - 10 ));
fi
