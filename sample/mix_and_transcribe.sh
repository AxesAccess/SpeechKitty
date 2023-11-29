#!/bin/bash

# Combines separate records into stereo file 
# (see mix_channels.py) and then transcribes

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

# Combine files with two separate channels into stereo files (mix_channels.py), then transcribe stereo files (transcribe_directory.py).
# Note that mix_channels.py skips already transcribed files. 
docker run -i --rm --env-file $SCRIPT_DIR/.env -v $1:/mnt/Records \
speechkitty /bin/bash -c "python sample/mix_channels.py /mnt/Records && python sample/transcribe_directory.py /mnt/Records $2"
