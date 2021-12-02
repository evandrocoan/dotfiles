#!/bin/bash
# set -x
set -eu${VERBOSE-} -o pipefail

parallel_uploads="6"
s3_main_logfile="/d/Backups/amazon_s3_glacier_deep_logs.txt"

bdsep=":"  # bucket_directory_separator
directories_and_buckets_to_upload=(
"/i/My Backups/Local Disk C${bdsep}disk-c-backup"
"/i/My Backups/Local Disk F${bdsep}disk-f-backup"
"/i/My Backups/Local Disk D${bdsep}disk-d-backup"
"/i/My Backups/Local Disk E${bdsep}disk-e-backup"
"/i/My Backups/Local Disk G${bdsep}disk-g-backup"
"/i/My Backups/Local Disk H${bdsep}disk-h-backup"
"/i/My Backups/Local Disk J${bdsep}disk-j-backup"
"/i/My Backups/Local Disk K${bdsep}disk-k-backup"
)

function main()
{
    all_local_files=()
    all_upload_files=()
    all_uploaded_files=""

    # https://stackoverflow.com/questions/51191766/how-can-i-creates-array-that-contains-the-names-of-all-the-files-in-a-folder
    function get_all_the_files()
    {
        directory="$1";

        # https://stackoverflow.com/questions/51191766/how-can-i-creates-array-that-contains-the-names-of-all-the-files-in-a-folder
        # https://stackoverflow.com/questions/2437452/how-to-get-the-list-of-files-in-a-directory-in-a-shell-script
        for item in "$directory"/*;
        do
            if [[ -d "$item" ]];
            then
                get_all_the_files "$item";
            else
                local_file_name="${item#"$base_directory"}";
                local_file_name="${local_file_name#/}";  # remove possible leading /
                all_local_files+=("$base_directory${bdsep}$local_file_name${bdsep}$bucket");
            fi;
        done;
    }

    function check_if_file_size_match()
    {
        local_file_name="$1";
        remote_file_size="$2";
        local_file_size="$(stat --printf="%s" "$local_file_name")";

        if [[ "$local_file_size" != "$remote_file_size" ]];
        then
            printf '%s Error: The local file "%s" mismatch "%s != %s" the remote file size!\n' \
                    "$(date)" \
                    "$local_file_name" \
                    "$local_file_size" \
                    "$remote_file_size";
            exit 1;
        else :
            # printf '%s Already uploaded file "%s" !\n' "$(date)" "$local_file_name";
        fi;
    }

    # https://stackoverflow.com/questions/9713104/loop-over-tuples-in-bash
    for items in "${directories_and_buckets_to_upload[@]}"
    do
        OLD_IFS="$IFS"; IFS="$bdsep";
        read -r directory bucket <<< "$items"; IFS="$OLD_IFS";
        printf '%s Downloading "%s" list of files for "%s"...\n' "$(date)" "$bucket" "$directory";

        # https://bobbyhadz.com/blog/aws-cli-list-all-files-in-bucket
        # https://unix.stackexchange.com/questions/176477/why-is-the-end-of-line-anchor-not-working-with-the-grep-command-even-though-t
        # https://stackoverflow.com/questions/1723440/how-can-i-find-all-matches-to-a-regular-expression-in-perl
        # https://stackoverflow.com/questions/13927672/how-do-i-match-across-newlines-in-a-perl-regex
        # https://stackoverflow.com/questions/4495791/how-to-match-a-newline-n-in-a-perl-regex]
        # https://superuser.com/questions/848315/make-perl-regex-search-exit-with-failure-if-not-found
        # https://stackoverflow.com/questions/1955505/parsing-json-with-unix-tools
        # https://stackoverflow.com/questions/53026131/how-to-prevent-unicodedecodeerror-when-reading-piped-input-from-sys-stdin
        uploaded_files="$(aws s3api list-objects \
                --bucket "$bucket" \
                --query "Contents[].{Key: Key, Size: Size}" \
                | dos2unix
            )";

        uploaded_files="$(printf '%s' "$uploaded_files" \
                | python3 -c '#!/usr/bin/env python3
import sys;
import json;
import urllib.parse
with open(sys.stdin.fileno(), mode="r", closefd=False, errors="replace") as stdin_binary:
    jsonlist = json.load(stdin_binary)
    if not jsonlist: sys.exit(0)
    for item in jsonlist:
        print("'"$bdsep"'"
                + item["Key"]
                + "'"$bdsep"'"
                + urllib.parse.unquote_plus(item["Key"])
                + "'"$bdsep"'"
                + str(item["Size"])
        )
    print("")' \
                | dos2unix
            )";

        base_directory="$directory";
        printf '%s Listing all local files for "%s"...\n' "$(date)" "$base_directory";
        get_all_the_files "$directory";

        if [[ -n "$uploaded_files" ]];
        then
            printf '%s Checking if all "%s" remote files exist locally for "%s"...\n' "$(date)" "$bucket" "$base_directory";
            all_uploaded_files="$all_uploaded_files$uploaded_files";

            while IFS= read -r items;
            do
                OLD_IFS="$IFS"; IFS="$bdsep";
                read -r nothing remote_file_name remote_file_name_url remote_file_size <<< "$items"; IFS="$OLD_IFS";

                local_file_name="$base_directory/$remote_file_name";
                local_file_name_url="$base_directory/$remote_file_name_url";

                if [[ -f "$local_file_name" ]];
                then
                    check_if_file_size_match "$local_file_name" "$remote_file_size";
                elif [[ -f "$local_file_name_url" ]];
                then
                    check_if_file_size_match "$local_file_name_url" "$remote_file_size";
                else
                    printf '%s Error: The remote file "%s <%s>" does not exist locally!\n' \
                            "$(date)" \
                            "$local_file_name" \
                            "$local_file_name_url";
                    exit 1;
                fi
            done <<< "$uploaded_files";
        else
            printf '%s No files exist yet on the remote "%s" for "%s"...\n' "$(date)" "$bucket" "$directory";
        fi;
    done;

    printf '%s Building list of files to upload...\n' "$(date)";
    for items in "${all_local_files[@]}"
    do
        OLD_IFS="$IFS"; IFS="$bdsep";
        read -r base_directory local_file_name bucket <<< "$items"; IFS="$OLD_IFS";

        # https://unix.stackexchange.com/questions/163810/grep-on-a-variable
        # https://stackoverflow.com/questions/11287861/how-to-check-if-a-file-contains-a-specific-string-using-bash
        uploaded_file="$(grep -F "${bdsep}$local_file_name${bdsep}" \
                    <<< "$all_uploaded_files")" \
                || {
                file_to_upload="$base_directory/$local_file_name";
                local_file_size="$(stat --printf="%s" "$file_to_upload")";
                printf '%s' "$(( $(cat "$upload_total_size_file") + local_file_size ))" > "$upload_total_size_file";

                local_file_size_formatted="$(printf '%s' "$local_file_size" | numfmt --grouping --to-unit 1000 | sed 's/,/./g')";
                printf '%s Not yet uploaded file "%s" %s KB!\n' "$(date)" "$file_to_upload" "$local_file_size_formatted";
            }

        if [[ "w$uploaded_file" == "w" ]];
        then
            all_upload_files+=("$base_directory${bdsep}$local_file_name${bdsep}$bucket");
        else :
            # printf '%s Already uploaded file "%s" !\n' "$(date)" "$base_directory/$local_file_name";
        fi;
    done;

    # Workaround for the posix shell bug they call it feature
    # https://unix.stackexchange.com/questions/65532/why-does-set-e-not-work-inside-subshells-with-parenthesis-followed-by-an-or
    function acually_upload_to_s3()
    {
        set -eu${VERBOSE-} -o pipefail;
        OLD_IFS="$IFS"; IFS="$bdsep";
        read -r base_directory local_file_name s3_bucket_name <<< "$1"; IFS="$OLD_IFS";

        file_to_upload="$base_directory/$local_file_name";
        lockfile="/tmp/upload_to_s3_md5sum_computation.lock";

        while ! mkdir "$lockfile" 2>/dev/null;
        do
            sleeptime="$(( RANDOM % 5 + 1 ))";
            # printf '%s MD5 is already running for %s, sleeping %s seconds for %s...\n' "$(date)" "$(cat "$lockfile/data.txt")" "$sleeptime" "$file_to_upload" >&2;
            sleep "$sleeptime";
        done;
        trap "rm -rf '$lockfile'" INT TERM EXIT;
        printf '%s' "$file_to_upload" > "$lockfile/data.txt";

        # Update the upload count when we still have a lock
        printf '%s' "$(( $(cat "$upload_counter_file") + 1 ))" > "$upload_counter_file";
        upload_counter="$(cat "$upload_counter_file")"

        local_file_size="$(stat --printf="%s" "$file_to_upload")";
        printf '%s' "$(( $(cat "$upload_size_file") + local_file_size ))" > "$upload_size_file";
        local_file_size_formatted="$(printf '%s' "$local_file_size" | numfmt --grouping --to-unit 1000 | sed 's/,/./g')";

        upload_size_formatted="$(cat "$upload_size_file" | numfmt --grouping --to-unit 1000 | sed 's/,/./g')";
        upload_total_size_formatted="$(cat "$upload_total_size_file" | numfmt --grouping --to-unit 1000 | sed 's/,/./g')";

        # https://www.ti-enxame.com/pt/bash/como-codificar-soma-md5-em-base64-em-bash/970218127/
        # https://stackoverflow.com/questions/32940878/how-to-base64-encode-a-md5-binary-string-using-shell-commands
        printf '%s Calculating hash %s of %s, %s KB of %s KB, file "%s" %s KB...\n' \
                "$(date)" \
                "$upload_counter" \
                "$all_files_count" \
                "$upload_size_formatted" \
                "$upload_total_size_formatted" \
                "$file_to_upload" \
                "$local_file_size_formatted";

        md5_sum_base64="$(openssl md5 -binary "$file_to_upload" | base64)";
        file_md5sum="$(printf '%s\n' "$md5_sum_base64" | openssl enc -base64 -d | xxd -ps -l 16)";

        # Remove the trap to not release someone else's lock on exit
        # https://bash.cyberciti.biz/guide/How_to_clear_trap
        rm -rf "$lockfile";
        trap - INT TERM EXIT;

        file_name_on_s3="$(python3 -c '#!/usr/bin/env python3
import sys
import urllib.parse
print(urllib.parse.quote_plus("'"$local_file_name"'"), end="")'
            )";

        # https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObject.html
        # STANDARD | REDUCED_REDUNDANCY | STANDARD_IA | ONEZONE_IA | INTELLIGENT_TIERING | GLACIER | DEEP_ARCHIVE | OUTPOSTS
        printf '%s Uploading %s of %s, %s KB of %s KB, file "%s <%s> %s KB"...\n' \
                "$(date)" \
                "$upload_counter" \
                "$all_files_count" \
                "$upload_size_formatted" \
                "$upload_total_size_formatted" \
                "$file_to_upload" \
                "$file_name_on_s3" \
                "$local_file_size_formatted";

        # Add a space before " $md5_sum_base64" to fix msys converting a hash starting with / to \
        # https://github.com/bmatzelle/gow/issues/196 - bash breaks Windows tools by replacing forward slash with a directory path
        return_value="$(aws s3api put-object \
            --bucket "$s3_bucket_name" \
            --key "$file_name_on_s3" \
            --body "$file_to_upload" \
            --content-md5 " $md5_sum_base64" \
            --storage-class "DEEP_ARCHIVE" \
            --server-side-encryption "AES256" \
        )";
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
        set -eu${VERBOSE-} -o pipefail;
        # https://superuser.com/questions/403263/how-to-pass-bash-script-arguments-to-a-subshell
        /bin/bash -c "acually_upload_to_s3 $(printf "${1+ %q}" "$@")" || exit 255;
    }

    function upload_all()
    {
        export -f upload_to_s3;
        export -f acually_upload_to_s3;
        export all_files_count="${#all_upload_files[@]}";

        export upload_counter_file;
        export upload_size_file;
        export upload_total_size_file;
        export bdsep;

        # https://unix.stackexchange.com/questions/566834/xargs-does-not-quit-on-error
        # https://stackoverflow.com/questions/11003418/calling-shell-functions-with-xargs
        # https://stackoverflow.com/questions/6441509/how-to-write-a-process-pool-bash-shell
        # https://stackoverflow.com/questions/356100/how-to-wait-in-bash-for-several-subprocesses-to-finish-and-return-exit-code-0
        if [[ "$all_files_count" -gt 0 ]];
        then
            printf "'%s'\\n" "${all_upload_files[@]}" | xargs \
                    --max-procs="$parallel_uploads" \
                    --max-args=1 \
                    --replace={} \
                    /bin/bash -c 'time upload_to_s3 "{}"';
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

upload_counter_file="/tmp/upload_to_s3_upload_counter.txt";
printf '0' > "$upload_counter_file";

upload_size_file="/tmp/upload_to_s3_upload_size.txt";
printf '0' > "$upload_size_file";

upload_total_size_file="/tmp/upload_to_s3_upload_total_size.txt";
printf '0' > "$upload_total_size_file";

time main 2>&1 | tee -a "$s3_main_logfile";
