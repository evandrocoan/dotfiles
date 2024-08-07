#!/bin/bash
set -TEeuo pipefail
USERNAME="yourusername"

USER=$(id -un $USERNAME)
GROUP=$(id -gn $USERNAME)

OUTFILE="/home/$USERNAME/monitor-ps-aux.log"
OUTFILE_OLD="/home/$USERNAME/monitor-ps-aux-old.log"

counter=0
sleep_time=10
rotation_time=$(( 60 * 60 * 48 / sleep_time ))

while true
do 
    counter=$((counter+1));
    if [[ $((counter % rotation_time)) -eq 0 ]];
    then
        counter=0;
        printf '%s Clean up space on %s...\n' "$(date)" "${OUTFILE}";

        rm -vf "${OUTFILE_OLD}";
        mv -v "${OUTFILE}" "${OUTFILE_OLD}";
        chown $USER:$GROUP "${OUTFILE_OLD}";
    fi;

    # ps aux --sort=-pcpu
    printf "%s\n%s\n\n" "$(date)" "$(ps aux --sort -rss)" >> "${OUTFILE}";
    chown $USER:$GROUP "${OUTFILE}";
    sleep $sleep_time;
done

# sudo vim /etc/systemd/system/monitor-ps-aux.service
# sudo systemctl daemon-reload
# sudo systemctl enable monitor-ps-aux.service
# sudo systemctl start monitor-ps-aux.service
# sudo systemctl status monitor-ps-aux.service
# [Unit]
# Description=Run script monitor-ps-aux.sh to save ps aux data for last days
# After=network.target
# StartLimitBurst=10
# StartLimitIntervalSec=10

# [Service]
# Type=simple
# Restart=always
# RestartSec=60
# User=root
# ExecStart=/bin/bash /home/evandro_coan/scripts/monitor-ps-aux.sh

# [Install]
# WantedBy=multi-user.target

