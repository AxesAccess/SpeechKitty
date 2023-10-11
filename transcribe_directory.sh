#!/bin/bash

if [ -z "$1" ]
  then
    echo "No DIR_PATH supplied."
    exit 1
fi

source <(grep = ./sample/credentials.ini)

python ./sample/transcribe_directory.py $1 $AWS_ACCESS_KEY_ID $AWS_SECRET_ACCESS_KEY $STORAGE_BUCKET_NAME $TRANSCRIBE_API_KEY "md5"