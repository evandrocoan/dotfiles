#!/bin/bash
set -eo pipefail

# Create a Task Scheduler with the following arguments: wscript "D:\User\Dropbox\SoftwareVersioning\SpeakTimeVBScript\silent_run.vbs" cmd "cmd /c ""F:\cygwin\bin\sh.exe"" ""/cygdrive/f/cygwin/home/Professional/scripts/backupanki.sh"""
# You can find a Windows 10 Task Scheduler task you can import: https://github.com/evandrocoan/batch_scripts/blob/master/WindowsTaksTcheduler/AnkiBackupDailyTask.xml
pushd `dirname $0` > /dev/null
SCRIPT_FOLDER_PATH=`pwd`
popd > /dev/null

export MAXIMUM_BACKUPS=100
export SRCDIR="/cygdrive/d/User/Documents/Anki2"
export DESTDIR="/cygdrive/d/User/Documents/AnkiApp"

BACKUP_FILE_NAME="${SCRIPT_FOLDER_PATH}/ankibackup.log"

# requires sudo apt-get install moreutils
if /bin/bash "${SCRIPT_FOLDER_PATH}/backupankihelper.sh" 2>&1 | ts '[%Y-%m-%d %H:%M:%S]' >> "${BACKUP_FILE_NAME}";
then :
else
    exitcode="$?"
    tail -20 "${BACKUP_FILE_NAME}"
    exit "${exitcode}"
fi
