import os
import re


class Directory:
    """Scans direcory for audio files."""

    def __init__(self, path) -> None:
        self.directory = path

    def get_wavs(
        self, regexp_include="^.+\\.wav$", regexp_exclude="", skip_processed=True
    ) -> list:
        """Returns list of paths of wav files in a directory and its subdirectories."""
        regexp_include = re.compile(regexp_include)
        regexp_exclude = re.compile(regexp_exclude) if regexp_exclude else None
        paths = []
        for path, subdirs, files in os.walk(self.directory):
            for name in files:
                paths += [os.path.join(path, name)]

        if regexp_exclude:
            wavs_paths = [
                f
                for f in paths
                if re.search(regexp_include, f) and not re.search(regexp_exclude, f)
            ]
        else:
            wavs_paths = [f for f in paths if re.search(regexp_include, f)]

        if skip_processed:
            processed = [f[:-5] for f in paths if f[-5:] == ".json"]
            output = [f for f in wavs_paths if f[:-4] not in processed]
            return output
        else:
            return wavs_paths
