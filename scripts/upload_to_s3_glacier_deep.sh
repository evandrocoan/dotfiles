#!/bin/bash
set -x
set -eo pipefail

parallel_uploads="4"
s3_bucket_name="disk-backup"
s3_main_logfile="/d/Backups/amazon_s3_glacier_deep_logs.txt"

directories_and_buckets_to_upload=(
"/i/My Backups/Local Disk C;disk-c-backup"
"/i/My Backups/Local Disk F;disk-f-backup"
"/i/My Backups/Local Disk D;disk-d-backup"
"/i/My Backups/Local Disk E;disk-e-backup"
"/i/My Backups/Local Disk G;disk-g-backup"
"/i/My Backups/Local Disk H;disk-h-backup"
"/i/My Backups/Local Disk J;disk-j-backup"
"/i/My Backups/Local Disk K;disk-k-backup"
)

function main()
{
    all_files=()

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
                get_all_the_files "$item"
            else
                file_name_on_s3="${item#"$base_directory"}";
                file_name_on_s3="${file_name_on_s3#/}"; # remove trailing /
                # https://unix.stackexchange.com/questions/163810/grep-on-a-variable
                # https://stackoverflow.com/questions/11287861/how-to-check-if-a-file-contains-a-specific-string-using-bash
                if ! grep -q "^$file_name_on_s3\$" <<< "$uploaded_files";
                then
                    all_files+=("$base_directory;$file_name_on_s3;$bucket");
                fi
            fi
        done
    }

    # https://stackoverflow.com/questions/9713104/loop-over-tuples-in-bash
    for items in "${directories_and_buckets_to_upload[@]}"
    do
        OLD_IFS="$IFS"; IFS=";";
        read directory bucket <<< "${items}"; IFS="$OLD_IFS";

        # https://bobbyhadz.com/blog/aws-cli-list-all-files-in-bucket
        # https://unix.stackexchange.com/questions/176477/why-is-the-end-of-line-anchor-not-working-with-the-grep-command-even-though-t
        uploaded_files="$(aws s3api list-objects --bucket "$bucket" --output text --query "Contents[].{Key: Key}" | dos2unix)"
        base_directory="$directory"
        get_all_the_files "$directory";
    done


    # Workaround for the posix shell bug they call it feature
    # https://unix.stackexchange.com/questions/65532/why-does-set-e-not-work-inside-subshells-with-parenthesis-followed-by-an-or
    function acually_upload_to_s3()
    {
        set -x;
        set -eu -o pipefail;
        OLD_IFS="$IFS"; IFS=";";
        read base_directory file_name_on_s3 s3_bucket_name <<< "${1}"; IFS="$OLD_IFS";

        file_to_upload="$base_directory/$file_name_on_s3";
        lockfile="/tmp/upload_to_s3_md5sum_computation.lock";
        while ! mkdir "$lockfile" 2>/dev/null;
        do
            sleeptime="$(( RANDOM % 5 + 1 ))"
            printf '%s MD5 is already running for %s, sleeping %s seconds for %s...\n' \
                    "$(date)" \
                    "$(cat "$lockfile/data.txt")" \
                    "$sleeptime" \
                    "$file_name_on_s3" >&2;
            sleep "$sleeptime";
        done
        trap "rm -rf '${lockfile}'" INT TERM EXIT
        printf '%s' "$file_name_on_s3" > "$lockfile/data.txt"

        # https://www.ti-enxame.com/pt/bash/como-codificar-soma-md5-em-base64-em-bash/970218127/
        # https://stackoverflow.com/questions/32940878/how-to-base64-encode-a-md5-binary-string-using-shell-commands
        printf '%s Calculating md5 for "%s"...\n' "$(date)" "${file_name_on_s3}";
        md5_sum_base64="$(openssl md5 -binary "${file_to_upload}" | base64)";
        file_md5sum="$(printf '%s\n' "$md5_sum_base64" | openssl enc -base64 -d | xxd -ps -l 16)";

        # Remove the trap to not release someone else's lock on exit
        # https://bash.cyberciti.biz/guide/How_to_clear_trap
        rm -rf "$lockfile"
        trap - INT TERM EXIT

        # https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObject.html
        # STANDARD | REDUCED_REDUNDANCY | STANDARD_IA | ONEZONE_IA | INTELLIGENT_TIERING | GLACIER | DEEP_ARCHIVE | OUTPOSTS
        printf '%s Uploading file "%s"...\n' "$(date)" "${file_name_on_s3}";

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
        s3_ETag="$(printf '%s' "$return_value" | perl -0777 -nle 'm/"ETag"\s*\:\s*"\\"(.*)\\""/; print $1')";

        if [[ -n "$s3_ETag" ]] && [[ "$s3_ETag" == "$file_md5sum" ]];
        then
            printf '%s GOOD: ETag "%s" does match, "%s"!\n\n' "$(date)" "$s3_ETag" "$file_to_upload";
        else
            printf '%s BAD: ETag "%s" does not match, "%s"!\n\n' "$(date)" "$s3_ETag" "$file_to_upload";
            exit 1;
        fi;
    }

    function upload_to_s3()
    {
        set -x;
        set -eu -o pipefail;
        # https://superuser.com/questions/403263/how-to-pass-bash-script-arguments-to-a-subshell
        /bin/bash -c "acually_upload_to_s3 $(printf "${1+ %q}" "$@")" || exit 255;
    }

    function upload_all()
    {
        export -f upload_to_s3;
        export -f acually_upload_to_s3;

        # https://unix.stackexchange.com/questions/566834/xargs-does-not-quit-on-error
        # https://stackoverflow.com/questions/11003418/calling-shell-functions-with-xargs
        # https://stackoverflow.com/questions/6441509/how-to-write-a-process-pool-bash-shell
        # https://stackoverflow.com/questions/356100/how-to-wait-in-bash-for-several-subprocesses-to-finish-and-return-exit-code-0
        printf "'%s'\n" "${all_files[@]}" | xargs \
                --max-procs="$parallel_uploads" \
                --max-args=1 \
                --replace={} \
                /bin/bash -c 'time upload_to_s3 "{}"';
    }

    time upload_all \
        && printf '%s Successfully uploaded all files\n' "$(date)" \
        || printf '%s Error: Could not upload some files\n'  "$(date)";
}

printf '\n\n\n\n\n\n\n\n\n' >> "$s3_main_logfile";
main 2>&1 | tee -a "$s3_main_logfile";

