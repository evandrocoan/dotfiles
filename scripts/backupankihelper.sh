#!/bin/bash
set -e

# Wait until anki exits before running the backup
ANKIPID="true"
BACKUP_FLAG_FILE="${DESTDIR}/backup_running"

if [[ -f "${BACKUP_FLAG_FILE}" ]];
then :
    printf 'The anki "backup=%s" is already running...\n' "${BACKUP_FLAG_FILE}"
    exit 1
else
    touch "${BACKUP_FLAG_FILE}"
fi

while [[ "w${ANKIPID}" != "w" ]];
do :
    ANKIPID="$(ps axf | grep anki | grep -v grep | awk '{print $1}')"
    printf 'Checking if "anki=%s" is running...\n' "${ANKIPID}"

    if [[ "w${ANKIPID}" != "w" ]];
    then
        sleep 600
    fi;
done

set -eo pipefail
FILENAME="$(date +%-Y-%-m-%-d)_$(date +%-T).zip"
FILENAME="$(printf '%s' "$FILENAME" | sed -E 's@\/|:@-@g')"

if [[ -f /bin/find ]];
then :
    FIND="/bin/find"
else
    FIND="/usr/bin/find"
fi

BACKUP_COUNTER=0
BACKUPDIR="$DESTDIR/Backups"
DESTFILE="$BACKUPDIR/$FILENAME"
mkdir -p "${BACKUPDIR}"

# https://linuxize.com/post/how-to-zip-files-and-directories-in-linux/
printf 'Create  "%s"\n' "${DESTFILE}"
zip -rq "${DESTFILE}" "${SRCDIR}"

# https://stackoverflow.com/questions/37793886/how-to-iterate-through-all-files-in-a-directory-ordered-by-date-created-with-s
"${FIND}" "${BACKUPDIR}" -type f -print0 | xargs -0 ls -t | while read file
do
    # printf 'Counter "%s", file: %s...\n' "${BACKUP_COUNTER}" "${file}"
    BACKUP_COUNTER=$((BACKUP_COUNTER + 1))

    # https://stackoverflow.com/questions/12118403/how-to-compare-binary-files-to-check-if-they-are-the-same
    if [[ "${BACKUP_COUNTER}" -eq 2 ]];
    then :
        if cmp "${file}" "${DESTFILE}" # >/dev/null 2>&1;
        then :
            printf 'The new backup file already exists, exiting...\n'
            rm "${file}"
            break
        fi
    fi

    if [[ "${BACKUP_COUNTER}" -gt "${MAXIMUM_BACKUPS}" ]];
    then :
        rm -v "${file}"
    fi
done

# read -p var
rm "${BACKUP_FLAG_FILE}"
