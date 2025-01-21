#!/bin/bash
# set -x
set -eu${VERBOSE-} -o pipefail

# target_file="/d/Downloads/Recording.wav"

# aws s3api put-object \
#     --bucket "$s3_bucket_name" \
#     --key "$file_name_on_s3" \
#     --body "$file_to_upload" \
#     --content-md5 " $md5_sum_base64" \
#     --storage-class "DEEP_ARCHIVE" \
#     --server-side-encryption "AES256"

aws transcribe start-transcription-job \
    --region us-east-1 \
    --transcription-job-name my-first-transcription-job \
    --media MediaFileUri=s3://buketnamee/Recording.wav \
    --output-bucket-name buketnamee \
    --output-key my-output-files/ \
    --language-code pt-BR \
    --settings 'ShowSpeakerLabels=TRUE,MaxSpeakerLabels=12'
