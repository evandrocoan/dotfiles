#!/bin/bash
OUTFILE=/root/monitor-ps-aux.log
OUTFILE_OLD=/root/monitor-ps-aux-old.log

counter=0

while true
do 
    counter=$((counter+1));
	if [[ $((counter % 17280)) -eq 0 ]];
    then
        counter=0;
        printf 'Clean up space on %s...\n' "${OUTFILE}";
        rm -v "${OUTFILE_OLD}";
        mv -v "${OUTFILE}" "${OUTFILE_OLD}";
    fi;

	# printf "%s\n\n" "$(ps aux --sort=-pcpu)" >> "${OUTFILE}"
	printf "%s\n\n" "$(ps aux --sort -rss)" >> "${OUTFILE}"
	sleep 10
done

# sudo vim /etc/systemd/system/monitor-ps-aux.service
# sudo systemctl daemon-reload
# sudo systemctl enable monitor-ps-aux.service
# sudo systemctl start monitor-ps-aux.service
# sudo systemctl status monitor-ps-aux.service
# [Unit]
# Description=Executa script monitor-ps-aux.sh to save ps aux data for last days
# After=network.target
# StartLimitIntervalSec=0

# [Service]
# Type=simple
# Restart=always
# RestartSec=60
# User=root
# ExecStart=/bin/bash /home/evandro_coan/scripts/monitor-ps-aux.sh

# [Install]
# WantedBy=multi-user.target

