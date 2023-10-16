import unittest
from app.speechkitty.directory import Directory


class TestDirectory(unittest.TestCase):
    def setUp(self):
        self.directory = Directory(path="sample/records")

    def test_get_wavs(self):
        assert len(self.directory.get_wavs(skip_processed=False)) == 3

    def test_get_wavs_skip(self):
        assert len(self.directory.get_wavs(skip_processed=True)) == 2

    def test_get_wavs_exclude(self):
        exclude = "^.+(?:-in|-out)\\.wav"
        assert (
            len(self.directory.get_wavs(regexp_exclude=exclude, skip_processed=False)) == 1
        )

    def test_get_wavs_skip_exclude(self):
        exclude = "^.+(?:-in|-out)\\.wav"
        assert self.directory.get_wavs(regexp_exclude=exclude, skip_processed=True) == []

    def test_get_wavs_include(self):
        include = "^.+(?:-in|-out)\\.wav"
        assert len(self.directory.get_wavs(regexp_include=include, skip_processed=True)) == 2
