#!/bin/bash

# Transcribes separate records for each of two channels
# and then combines them into resulting html table 

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

# Searches for wav files containing left and right tracks (inbound and outbound call parts),
# transcribes each independently and then combines pairs into resulting html files.
# See 'sample/transcribe_split_channels.py' for details and parameters. 
docker run -i --rm --env-file $SCRIPT_DIR/.env -v $1:/mnt/Records \
speechkitty /bin/bash -c "python sample/transcribe_split_channels.py -d /mnt/Records -h $2"
