#!/bin/bash

# Provide records directory path in the first argument
if [ -z "$1" ]; then
  echo "Supply records directory path in the argument."
  exit 1
fi

if [ ! -d "$1" ]; then
  echo "Directory does not exist."
  exit 1
fi

# Path to credentials.ini
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source <(grep = $SCRIPT_DIR/credentials.ini)

# 'md5' at the end tells script to name html files using hash from the name of the audio file
# delete it if you want to name html files after audio files
docker run -i --rm -v $1:/mnt/Records speechkitty /bin/bash -c "python \
./sample/transcribe_directory.py /mnt/Records $AWS_ACCESS_KEY_ID $AWS_SECRET_ACCESS_KEY \
$STORAGE_BUCKET_NAME $TRANSCRIBE_API_KEY md5"
