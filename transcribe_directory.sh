#!/bin/bash

source <(grep = credentials.ini)

python ./sample/transcribe_directory.py $REC_DIR $AWS_ACCESS_KEY_ID $AWS_SECRET_ACCESS_KEY $STORAGE_BUCKET_NAME $TRANSCRIBE_API_KEY "md5"
