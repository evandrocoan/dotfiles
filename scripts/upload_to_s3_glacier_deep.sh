#!/bin/bash
set -x
set -eo pipefail

parallel_uploads="4"
s3_bucket_name="disk-backup"

all_files=(
"/i/My Backups/Local Disk C/Local Disk v1.pbd"
)


function upload_to_s3()
{
    set -x;
    (
        set -eo pipefail;
        s3_bucket_name="$1";
        file_to_upload="$2";
        file_name_on_s3="$(basename "$file_to_upload")";

        # https://www.ti-enxame.com/pt/bash/como-codificar-soma-md5-em-base64-em-bash/970218127/
        # https://stackoverflow.com/questions/32940878/how-to-base64-encode-a-md5-binary-string-using-shell-commands
        printf 'Calculating md5...\n';
        md5_sum_base64="$(openssl md5 -binary "${file_to_upload}" | base64)";
        file_md5sum="$(printf '%s\n' "$md5_sum_base64" | openssl enc -base64 -d | xxd -ps -l 16)";

        # https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObject.html
        # STANDARD | REDUCED_REDUNDANCY | STANDARD_IA | ONEZONE_IA | INTELLIGENT_TIERING | GLACIER | DEEP_ARCHIVE | OUTPOSTS
        printf 'Uploading file...\n';
        return_value="$(aws s3api put-object \
            --bucket "$s3_bucket_name" \
            --key "$file_name_on_s3" \
            --body "$file_to_upload" \
            --content-md5 "$md5_sum_base64" \
            --storage-class "DEEP_ARCHIVE" \
            --server-side-encryption "AES256" \
        )";

        # https://stackoverflow.com/questions/25087919/command-line-s-span-multiple-lines-in-perl
        # https://stackoverflow.com/questions/3532718/extract-string-from-string-using-regex-in-the-terminal
        s3_ETag="$(printf '%s' "$return_value" | perl -0777 -nle 'm/"ETag"\s*\:\s*"\\"(.*)\\""/; print $1')";

        if [[ "$s3_ETag" == "$file_md5sum" ]];
        then
            printf 'GOOD: ETag does match, "%s"!\n\n' "$file_to_upload";
        else
            printf 'BAD: ETag does not match, ""%s!\n\n' "$file_to_upload";
            exit 1;
        fi;
    ) || exit 255;
}

function upload_all()
{
    export s3_bucket_name;
    export -f upload_to_s3;

    # https://unix.stackexchange.com/questions/566834/xargs-does-not-quit-on-error
    # https://stackoverflow.com/questions/11003418/calling-shell-functions-with-xargs
    # https://stackoverflow.com/questions/6441509/how-to-write-a-process-pool-bash-shell
    # https://stackoverflow.com/questions/356100/how-to-wait-in-bash-for-several-subprocesses-to-finish-and-return-exit-code-0
    printf "'%s'\n" "${all_files[@]}" | xargs \
            --max-procs="$parallel_uploads" \
            --max-args=1 \
            --replace={} \
            bash -c 'time upload_to_s3 "$s3_bucket_name" "{}"';
}

time upload_all;
printf 'Successfully uploaded all files\n'
