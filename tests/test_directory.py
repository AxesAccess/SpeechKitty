import unittest
from app.speechkitty.directory import Directory


class TestDirectory(unittest.TestCase):
    def setUp(self):
        self.directory = Directory(path="sample/records")

    def test_get_records(self):
        assert len(self.directory.get_records(skip_processed=False)) == 4

    def test_get_records_skip(self):
        assert len(self.directory.get_records(skip_processed=True)) == 2

    def test_get_records_exclude(self):
        exclude = "^.+(?:-in|-out)\\.wav"
        assert len(self.directory.get_records(regexp_exclude=exclude, skip_processed=False)) == 2

    def test_get_records_skip_exclude(self):
        exclude = "^.+(?:-in|-out)\\.wav"
        assert self.directory.get_records(regexp_exclude=exclude, skip_processed=True) == []

    def test_get_records_include(self):
        include = "^.+(?:-in|-out)\\.wav"
        assert len(self.directory.get_records(regexp_include=include, skip_processed=True)) == 2
