import os
import tempfile
import traceback
import warnings
from pydub import AudioSegment


class AudioConverter:
    def __init__(self, raise_exceptions: bool = False) -> None:
        self.temp_dir = tempfile.gettempdir()
        self.raise_exceptions = raise_exceptions

    def to_ogg(self, file_path: str) -> str:
        try:
            fmt = os.path.basename(file_path[-3:]).lower()
            a = AudioSegment.from_file(file_path, fmt)
            ogg_path = self.temp_dir + "/" + os.path.basename(file_path[:-4]) + ".ogg"
            a.export(ogg_path, format="opus")
        except Exception as e:
            if self.raise_exceptions:
                raise e
            else:
                warnings.warn(f"Convert error: {file_path} {traceback.format_exc()}")
                return ""
        return ogg_path
