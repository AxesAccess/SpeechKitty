import os
import re


class Directory:
    def __init__(self, directory, regexp_include="^.+\\.wav$", regexp_exclude="") -> None:
        self.directory = directory
        self.regexp_include = re.compile(regexp_include)
        self.regexp_exclude = re.compile(regexp_exclude) if regexp_exclude else None

    def get_wavs(self):
        paths = []
        for path, subdirs, files in os.walk(self.directory):
            for name in files:
                paths += [os.path.join(path, name)]

        if self.regexp_exclude:
            wavs_paths = [f for f in paths if re.search(self.regexp_include, f)
                          and not re.search(self.regexp_exclude, f)]
        else:
            wavs_paths = [f for f in paths if re.search(self.regexp_include, f)]

        if len(wavs_paths) == 0:
            return []

        processed = [f[:-5] for f in paths if f[-5:] == ".json"]
        output = [f for f in wavs_paths if f[:-4] not in processed]
        return output
