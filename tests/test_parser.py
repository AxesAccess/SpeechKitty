import hashlib
import json
from os import listdir
import os
import unittest
from xml.dom import minidom
import pandas as pd
from app.speechkitty.result_parser import Parser
import pytest

PATH = "sample/records"


class TestParser(unittest.TestCase):
    def setUp(self):
        self.parser = Parser()
        files = [f"{PATH}/{f}" for f in listdir(PATH) if f[-5:] == ".json"]
        wavs = [f"{PATH}/{f}" for f in listdir(PATH) if f[-4:] == ".wav"]
        self.wav_path = wavs[0]
        for filename in files:
            if ".whisper." in filename:
                with open(filename, "r") as f:
                    self.result_whisper = json.loads(f.read())
            else:
                with open(filename, "r") as f:
                    self.result = json.loads(f.read())

    def test_header_footer(self) -> None:
        assert len(self.parser.header) & len(self.parser.footer)

    def test_parse_result(self):
        df = self.parser.parse_result(self.result)
        assert isinstance(df, pd.DataFrame)

    def test_parse_result_whisper(self):
        df = self.parser.parse_result(self.result_whisper)
        assert isinstance(df, pd.DataFrame)

    def test_parse_result_no_chunks(self):
        del self.result["response"]["chunks"]
        assert self.parser.parse_result(self.result).empty

    def test_create_html(self):
        df = self.parser.parse_result(self.result)
        html = self.parser.create_html(df)
        doc = minidom.parseString(html)
        assert len(doc.getElementsByTagName("table")) == 1

    def test_name_html(self):
        html_name = self.parser.name_html(self.wav_path, hash_func="")
        assert html_name[:-4] == self.wav_path[:-3]

    @pytest.mark.filterwarnings("ignore:Hash")
    def test_name_html_shake_128(self):
        html_name = self.parser.name_html(self.wav_path, hash_func="shake_128")
        assert html_name[:-4] == self.wav_path[:-3]

    def test_name_html_hash(self):
        algorithms = hashlib.algorithms_guaranteed - {"shake_128", "shake_256"}
        test = []
        for hash_func in algorithms:
            html_name = self.parser.name_html(self.wav_path, hash_func=hash_func)
            h = getattr(hashlib, hash_func)
            wav_name = os.path.basename(self.wav_path)
            test_html_name = h(wav_name.encode()).hexdigest() + ".html"
            test_html_name = os.path.dirname(self.wav_path) + "/" + test_html_name
            test += [html_name == test_html_name]
        assert sum(test) == len(algorithms)
