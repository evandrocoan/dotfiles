#!/bin/bash
# set -x
set -eu${VERBOSE-} -o pipefail

parallel_uploads="6"
s3_main_logfile="/d/Backups/amazon_s3_glacier_deep_logs.txt"

export bdsep=":"  # bucket_directory_separator
directories_and_buckets_to_upload=(
'/i/My Backups/Local Disk C'"${bdsep}"'disk-c-backup'
'/i/My Backups/Local Disk F'"${bdsep}"'disk-f-backup'
'/i/My Backups/Local Disk D'"${bdsep}"'disk-d-backup'
'/i/My Backups/Local Disk E'"${bdsep}"'disk-e-backup'
'/i/My Backups/Local Disk G'"${bdsep}"'disk-g-backup'
'/i/My Backups/Local Disk H'"${bdsep}"'disk-h-backup'
'/i/My Backups/Local Disk J'"${bdsep}"'disk-j-backup'
'/i/My Backups/Local Disk K'"${bdsep}"'disk-k-backup'
)

files_to_ignore='
desktop.ini
Thumbs.db
'

function main()
{
    all_upload_files=()

    # https://stackoverflow.com/questions/9713104/loop-over-tuples-in-bash
    for items in "${directories_and_buckets_to_upload[@]}"
    do
        OLD_IFS="$IFS"; IFS="$bdsep";
        read -r base_directory bucket <<< "$items"; IFS="$OLD_IFS";
        printf '%s Downloading "%s" list of files for "%s"...\n' "$(date)" "$bucket" "$base_directory";

        # https://bobbyhadz.com/blog/aws-cli-list-all-files-in-bucket
        # https://unix.stackexchange.com/questions/176477/why-is-the-end-of-line-anchor-not-working-with-the-grep-command-even-though-t
        # https://stackoverflow.com/questions/1723440/how-can-i-find-all-matches-to-a-regular-expression-in-perl
        # https://stackoverflow.com/questions/13927672/how-do-i-match-across-newlines-in-a-perl-regex
        # https://stackoverflow.com/questions/4495791/how-to-match-a-newline-n-in-a-perl-regex]
        # https://superuser.com/questions/848315/make-perl-regex-search-exit-with-failure-if-not-found
        # https://stackoverflow.com/questions/1955505/parsing-json-with-unix-tools
        uploaded_files="$(aws s3api list-objects \
                --bucket "$bucket" \
                --query "Contents[].{Key: Key, Size: Size}" \
                | dos2unix
            )";

        all_upload_files_string="$(printf '%s' "$uploaded_files" \
                | python3 -c '#!/usr/bin/env python3
import os
import sys
import json
import time

import math
import urllib.parse
import locale

bdsep = "'"$bdsep"'"
bucket = "'"$bucket"'"
base_directory = "'"$base_directory"'"

uploaded_files_set = set()
files_to_ignore = set("""'"$files_to_ignore"'""".splitlines())

# https://stackoverflow.com/questions/56791917/how-to-format-datetime-in-python-as-date-is-doing/56794800
locale.setlocale(locale.LC_ALL, "")

def now():
    return str(time.strftime("%c"))

def log(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def check_if_file_size_match(path, size):
    local_size = os.path.getsize(path)
    if os.path.getsize(path) != size:
        raise RuntimeError(f"{now()} Error: The local file \"{path}\" mismatch {size} != {local_size} for remote file size!")

def check_invalid_characther(file_path):
    for thing in ("\\", "\n"):
        if thing in file_path:
            raise RuntimeError(f"It is not allowed {thing} on \"{file_path}\"!")

# https://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python
def to_B(size_bytes, factor=0, postfix="B"):
    if size_bytes == 0:
        return "0 B"
    if factor:
        size_bytes = size_bytes / factor
    return f"{int(size_bytes):,} {postfix}".replace(",", ".")

def to_KB(size_bytes, factor=0, postfix="B"):
    return to_B(size_bytes, factor=1024, postfix="KB")

# https://stackoverflow.com/questions/18394147/how-to-do-a-recursive-sub-folder-search-and-return-files-in-a-list
# https://stackoverflow.com/questions/53026131/how-to-prevent-unicodedecodeerror-when-reading-piped-input-from-sys-stdin
with open(sys.stdin.fileno(), mode="r", closefd=False, errors="replace") as uploaded_files_stdin_binary:
    uploaded_files = json.load(uploaded_files_stdin_binary)

    if uploaded_files:
        log(f"{now()} Checking if all \"{bucket}\" remote files exist locally for \"{base_directory}\"...")

        for item in uploaded_files:
            file_name = item["Key"]
            file_name_unquoted = urllib.parse.unquote_plus(item["Key"])
            file_size = item["Size"]

            uploaded_files_set.add(file_name)
            check_invalid_characther(file_name)
            check_invalid_characther(file_name_unquoted)

            file_path = os.path.join(base_directory, file_name)
            file_path_unquoted = os.path.join(base_directory, file_name_unquoted)

            if os.path.exists(file_path):
                check_if_file_size_match(file_path, file_size)
            elif os.path.exists(file_path_unquoted):
                check_if_file_size_match(file_path_unquoted, file_size)
            else:
                raise RuntimeError(f"{now()} Error: Remote file \"{file_path} <{file_path_unquoted}>\" does not exist locally!")
    else:
        log(f"{now()} No files exist yet on the remote \"{bucket}\" for \"{base_directory}\"...")

files_counter = 0
files_local_size = 0
upload_counter = 0
upload_total_size = 0
log(f"{now()} Listing all local files for \"{base_directory}\"...")

def convert_absolute_path_to_relative(base_directory, file_path):
    relative_path = os.path.commonprefix( [ base_directory, file_path ] )
    relative_path = os.path.normpath( file_path.replace( relative_path, "" ) )
    relative_path = relative_path.replace("\\", "/")
    if relative_path.startswith( "/" ):
        relative_path = relative_path[1:]
    return relative_path

# https://stackoverflow.com/questions/13454164/os-walk-without-hidden-folders
for directory, directories, files in os.walk(base_directory):
    for file in files:
        local_file_path = os.path.join(directory, file)
        local_file_name = convert_absolute_path_to_relative(base_directory, local_file_path)
        local_file_name_url = urllib.parse.quote_plus(local_file_name)

        # log(f"local_file_name {local_file_name}, local_file_name_url {local_file_name_url}.")
        check_invalid_characther(local_file_name)
        local_size = os.path.getsize(local_file_path)

        if file in files_to_ignore:
            log(f"{now()} Ignoring item {local_file_path}...")
            continue

        if uploaded_files and (local_file_name in uploaded_files_set or local_file_name_url in uploaded_files_set):
            files_counter += 1
            files_local_size += local_size
            # log(f"{now()} {files_counter:6} Already uploaded file \"{local_file_name}\" {to_B(local_size)}!")
        else:
            upload_counter += 1
            upload_total_size += local_size
            print(f"{base_directory}{bdsep}{local_file_name}{bdsep}{bucket}")
            log(f"{now()} {upload_counter:6} Not yet uploaded file \"{local_file_name}\" {to_B(local_size)}!")

# https://stackoverflow.com/questions/6648493/how-to-open-a-file-for-both-reading-and-writing/
def add_to_file(file_path, add):
    with open(file_path, "r") as file:
        total_size = add + int(file.read())
    with open(file_path, "w") as file:
        file.write(f"{total_size}")
    return total_size

add_to_file("'"$upload_total_size_file"'", upload_total_size)
add_to_file("'"$local_total_size_file"'", files_local_size)
add_to_file("'"$local_files_counter_file"'", files_counter)

log(f"{now()}        Directory uploading {upload_counter} files of {files_counter} with {to_KB(upload_total_size)} of {to_KB(files_local_size)}...")
' | dos2unix)";

        if [[ -n "$all_upload_files_string" ]];
        then
            # https://stackoverflow.com/questions/10586153/how-to-split-a-string-into-an-array-in-bash
            readarray -t temp <<< "$all_upload_files_string";
            all_upload_files+=("${temp[@]}");
        fi;
    done;

    export all_files_count="${#all_upload_files[@]}";
    export local_total_size_formatted="$(cat "$local_total_size_file" | numfmt --grouping --to-unit 1000 | sed 's/,/./g')";
    export upload_total_size_formatted="$(cat "$upload_total_size_file" | numfmt --grouping --to-unit 1000 | sed 's/,/./g')";

    printf '\n%s Starting to upload %s files of %s with %s KB of %s KB...\n' \
            "$(date)" \
            "$all_files_count" \
            "$(cat "$local_files_counter_file")" \
            "$upload_total_size_formatted" \
            "$local_total_size_formatted";

    function get_file_lock()
    {
        lockfile="$1";
        locker_name="$2";

        # https://stackoverflow.com/questions/185451/quick-and-dirty-way-to-ensure-only-one-instance-of-a-shell-script-is-running-at
        while ! mkdir "$lockfile" 2>/dev/null;
        do
            sleeptime="$(( RANDOM % 5 + 1 ))";
            # printf '%s MD5 is already running for %s, sleeping %s seconds for %s...\n' "$(date)" "$(cat "$lockfile/data.txt")" "$sleeptime" "$locker_name" >&2;
            printf '.';
            sleep "$sleeptime";
        done;

        # Remove the trap later to not release someone else's lock on exit
        # https://bash.cyberciti.biz/guide/How_to_clear_trap
        trap "rm -rf '$lockfile'" INT TERM EXIT;
        printf '%s' "$locker_name" > "$lockfile/data.txt";
    }

    # Workaround for the posix shell bug they call it feature
    # https://unix.stackexchange.com/questions/65532/why-does-set-e-not-work-inside-subshells-with-parenthesis-followed-by-an-or
    function acually_upload_to_s3()
    {
        set -eu${VERBOSE-} -o pipefail;
        OLD_IFS="$IFS"; IFS="$bdsep";
        read -r base_directory local_file_name s3_bucket_name <<< "$1"; IFS="$OLD_IFS";

        file_to_upload="$base_directory/$local_file_name";
        lockfile="/tmp/upload_to_s3_md5sum_computation.lock";
        get_file_lock "$lockfile" "$file_to_upload";

        # Update the upload count when we still have a lock
        printf '%s' "$(( $(cat "$upload_counter_file") + 1 ))" > "$upload_counter_file";
        upload_counter="$(cat "$upload_counter_file")"

        local_file_size="$(stat --printf="%s" "$file_to_upload")";
        printf '%s' "$(( $(cat "$upload_size_file") + local_file_size ))" > "$upload_size_file";

        local_file_size_formatted="$(printf '%s' "$local_file_size" | numfmt --grouping --to-unit 1000 | sed 's/,/./g')";
        upload_size_formatted="$(cat "$upload_size_file" | numfmt --grouping --to-unit 1000 | sed 's/,/./g')";

        # https://www.ti-enxame.com/pt/bash/como-codificar-soma-md5-em-base64-em-bash/970218127/
        # https://stackoverflow.com/questions/32940878/how-to-base64-encode-a-md5-binary-string-using-shell-commands
        printf '%s Calculating hash %s of %s files, %s KB of %s KB, file "%s", %s KB...\n' \
                "$(date)" \
                "$upload_counter" \
                "$all_files_count" \
                "$local_file_size_formatted" \
                "$upload_size_formatted" \
                "$file_to_upload" \
                "$upload_total_size_formatted";

        md5_sum_base64="$(openssl md5 -binary "$file_to_upload" | base64)";
        file_md5sum="$(printf '%s\n' "$md5_sum_base64" | openssl enc -base64 -d | xxd -ps -l 16)";
        rm -rf "$lockfile"; trap - INT TERM EXIT;

        upload_attempts="0"
        file_name_on_s3="$(python3 -c '#!/usr/bin/env python3
import sys
import urllib.parse
print(urllib.parse.quote_plus("'"$local_file_name"'"), end="")
        ')";

        while true;
        do
            # TODO: Here, `upload_total_size_complete_file` is not protected against concurrent
            # access with `get_file_lock`. Protect it, if it causes problems in the future!
            upload_remaning_time="$(python3 -c '#!/usr/bin/env python3
import datetime
timenow = datetime.datetime.now().timestamp()

elapsed_time = timenow - '"$(cat "$upload_start_time_file")"'
upload_total_size = '"$(cat "$upload_total_size_file")"'
upload_total_size_complete = '"$(cat "$upload_total_size_complete_file")"'
upload_speed = upload_total_size_complete / elapsed_time

if upload_speed:
    remaining_upload = upload_total_size - upload_total_size_complete
    remaining_time = datetime.timedelta(seconds=remaining_upload / upload_speed)
    elapsed_time = datetime.timedelta(seconds=elapsed_time)
    print(f", {str(remaining_time)[:-4]} of {str(elapsed_time)[:-4]}...")
else:
    print(f"...")
            ')";

            # https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObject.html
            # STANDARD | REDUCED_REDUNDANCY | STANDARD_IA | ONEZONE_IA | INTELLIGENT_TIERING | GLACIER | DEEP_ARCHIVE | OUTPOSTS
            printf '%s Uploading %s of %s files, %s KB of %s KB, file "%s <%s>"%s\n' \
                    "$(date)" \
                    "$upload_counter" \
                    "$all_files_count" \
                    "$local_file_size_formatted" \
                    "$upload_size_formatted" \
                    "$file_to_upload" \
                    "$file_name_on_s3" \
                    "$upload_remaning_time";

            # Add a space before " $md5_sum_base64" to fix msys converting a hash starting with / to \
            # https://github.com/bmatzelle/gow/issues/196 - bash breaks Windows tools by replacing forward slash with a directory path
            return_value="$(aws s3api put-object \
                --bucket "$s3_bucket_name" \
                --key "$file_name_on_s3" \
                --body "$file_to_upload" \
                --content-md5 " $md5_sum_base64" \
                --storage-class "DEEP_ARCHIVE" \
                --server-side-encryption "AES256" \
            )" || {
                if [[ "$upload_attempts" -gt 10 ]];
                then
                    printf '%s Error uploading %s, stopping after %s attempts...\n' "$(date)" "$file_to_upload" "$upload_attempts";
                    exit 1;
                fi
                upload_attempts="$((upload_attempts + 1))";
                sleeptime="$(( (RANDOM % 60 + 1) * upload_attempts ))";

                printf '%s Error uploading %s, retrying %s times after %s seconds...\n' \
                        "$(date)" \
                        "$file_to_upload" \
                        "$upload_attempts" \
                        "$sleeptime";
                sleep "$sleeptime";
                continue;
            };
            break;
        done;

        get_file_lock "$lockfile" "$file_to_upload";
        printf '%s' "$(( $(cat "$upload_total_size_complete_file") + local_file_size ))" > "$upload_total_size_complete_file";
        rm -rf "$lockfile"; trap - INT TERM EXIT;

        # https://stackoverflow.com/questions/25087919/command-line-s-span-multiple-lines-in-perl
        # https://stackoverflow.com/questions/3532718/extract-string-from-string-using-regex-in-the-terminal
        s3_ETag="$(printf '%s' "$return_value" | perl -0777 -nle 'print "$1" if m/"ETag"\s*\:\s*"\\"(.*)\\""/')";

        if [[ -n "$s3_ETag" ]] && [[ "$s3_ETag" == "$file_md5sum" ]];
        then
            printf '%s %s of %s, GOOD: ETag "%s" does match, "%s" %s KB!\n' \
                    "$(date)" \
                    "$upload_counter" \
                    "$all_files_count" \
                    "$s3_ETag" \
                    "$file_to_upload" \
                    "$local_file_size_formatted";
        else
            printf '%s %s of %s, BAD: ETag "%s != %s" does not match, "%s"!\n\n' \
                    "$(date)" \
                    "$upload_counter" \
                    "$all_files_count" \
                    "$s3_ETag" \
                    "$file_md5sum" \
                    "$file_to_upload";
            exit 1;
        fi;
    }

    function upload_to_s3()
    {
        # https://superuser.com/questions/403263/how-to-pass-bash-script-arguments-to-a-subshell
        set -eu${VERBOSE-} -o pipefail;
        /bin/bash -c "acually_upload_to_s3 $(printf "${1+ %q}" "$@")" || exit 255;
    }

    function upload_all()
    {
        export -f upload_to_s3;
        export -f get_file_lock;
        export -f acually_upload_to_s3;

        # https://unix.stackexchange.com/questions/566834/xargs-does-not-quit-on-error
        # https://stackoverflow.com/questions/11003418/calling-shell-functions-with-xargs
        # https://stackoverflow.com/questions/6441509/how-to-write-a-process-pool-bash-shell
        # https://stackoverflow.com/questions/356100/how-to-wait-in-bash-for-several-subprocesses-to-finish-and-return-exit-code-0
        if [[ "$all_files_count" -gt 0 ]];
        then
            # https://unix.stackexchange.com/questions/280430/are-the-null-string-and-the-same-string
            # https://stackoverflow.com/questions/67952154/how-can-i-avoid-printing-anything-in-bash-printf-with-an-empty-array
            # https://stackoverflow.com/questions/6570531/assign-string-containing-null-character-0-to-a-variable-in-bash
            # https://stackoverflow.com/questions/60113944/0-and-printf-in-c
            # https://askubuntu.com/questions/1106805/xargs-unmatched-single-quote-by-default-quotes-are-special-to-xargs-unless-you
            printf "%s\\000" "${all_upload_files[@]}" | xargs \
                    --null \
                    --max-procs="$parallel_uploads" \
                    --max-args=1 \
                    --replace={} \
                    /bin/bash -c "time upload_to_s3 \"{}\"";
        fi;
    }

    time upload_all \
        && printf '%s Successfully uploaded all files\n' "$(date)" \
        || { printf '%s Error: Could not upload some files\n'  "$(date)"; exit 1; }
}

if shopt -qo xtrace;
then
    export VERBOSE=x;
fi

printf '\n\n\n\n\n\n\n\n' >> "$s3_main_logfile";
printf '%s Starting upload with %s threads (%s)...\n' \
        "$(date)" "$parallel_uploads" "$s3_main_logfile" 2>&1 | tee -a "$s3_main_logfile";

export upload_start_time_file="/tmp/upload_to_s3_upload_start_time.txt";
printf "%s" "$(date +%s.%N)" > "$upload_start_time_file";

export upload_counter_file="/tmp/upload_to_s3_upload_counter.txt";
printf '0' > "$upload_counter_file";

export local_files_counter_file="/tmp/upload_to_s3_local_files_counter.txt";
printf '0' > "$local_files_counter_file";

export upload_size_file="/tmp/upload_to_s3_upload_size.txt";
printf '0' > "$upload_size_file";

export local_total_size_file="/tmp/upload_to_s3_local_total_size.txt";
printf '0' > "$local_total_size_file";

export upload_total_size_file="/tmp/upload_to_s3_upload_total_size.txt";
printf '0' > "$upload_total_size_file";

export upload_total_size_complete_file="/tmp/upload_to_s3_upload_total_size_complete.txt";
printf '0' > "$upload_total_size_complete_file";

time main 2>&1 | tee -a "$s3_main_logfile";
