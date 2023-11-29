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

# Get path to script directory
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

# If the second parameter contains name of hash function then the names of html files
# will use hash of the audio files 
docker run -i --rm --env-file $SCRIPT_DIR/.env -v $1:/mnt/Records \
speechkitty /bin/bash -c "python sample/transcribe_directory.py /mnt/Records $2"
