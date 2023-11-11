import os
import re


class Directory:
    """Scans directory for files"""

    def __init__(self, path: str) -> None:
        self.directory = path

    def walk_dir(self) -> list:
        """Returns list of paths of all files in a directory and its subdirectories"""
        paths = []
        for path, subdirs, files in os.walk(self.directory):
            for name in files:
                paths += [os.path.join(path, name)]
        return paths

    def get_records(
        self,
        regexp_include: str = "^.+\\.(:?wav|mp3|wma|aac|ogg)$",
        regexp_exclude: str = "",
        skip_processed: bool = False,
    ) -> list:
        """Returns list of paths of files matching given regex expressions in a directory
        and its subdirectories skipping already processed"""
        incl = re.compile(regexp_include)
        excl = re.compile(regexp_exclude) if regexp_exclude else None
        paths = self.walk_dir()

        if excl:
            wavs_paths = [f for f in paths if re.search(incl, f) and not re.search(excl, f)]
        else:
            wavs_paths = [f for f in paths if re.search(incl, f)]

        if skip_processed:
            processed = [f[:-5] for f in paths if f[-5:] == ".json"]
            output = [f for f in wavs_paths if f[:-4] not in processed]
            return output
        else:
            return wavs_paths
