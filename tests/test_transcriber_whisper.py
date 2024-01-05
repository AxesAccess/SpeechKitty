import os
import unittest
import json
import pytest
import requests_mock
from app.speechkitty.transcriber import Transcriber

OGG_PATH = "sample/records/rg-170-74994043564-20231021-171101-1697897360.54.ogg"
WAV_PATH = "sample/records/rg-170-74994043564-20231021-171101-1697897360.54.wav"
JSON_PATH = "sample/records/rg-170-74994043564-20231021-171101-1697897360.54.whisper.json"
WHISPER_ENDPOINT = "http://127.0.0.1:5001/whisperx?output=json"


class TestTranscriber(unittest.TestCase):
    def setUp(self):
        os.environ["WHISPER_ENDPOINT"] = WHISPER_ENDPOINT
        self.transcriber = Transcriber(api="whisperX")

    @requests_mock.Mocker()
    def test_transcribe_file_empty_result_raised(self, m):
        self.transcriber.set_raise_exceptions(True)
        result = ""
        m.post(self.transcriber.whisper_endpoint, text=result)
        try:
            _ = self.transcriber.transcribe_file(WAV_PATH)
            assert False
        except json.decoder.JSONDecodeError:
            assert True

    @requests_mock.Mocker()
    @pytest.mark.filterwarnings("ignore: Transcribe")
    def test_transcribe_file_empty_result_caught(self, m):
        self.transcriber.set_raise_exceptions(False)
        result = ""
        m.post(self.transcriber.whisper_endpoint, text=result)
        assert None is self.transcriber.transcribe_file(WAV_PATH)

    @requests_mock.Mocker()
    def test_transcribe_file(self, m):
        with open(JSON_PATH, "r") as f:
            result = f.read()
        m.post(self.transcriber.whisper_endpoint, text=result)
        assert json.loads(result) == self.transcriber.transcribe_file(WAV_PATH)

    @requests_mock.Mocker()
    def test_transcribe_file_no_wav_raised(self, m):
        self.transcriber.set_raise_exceptions(True)
        try:
            self.transcriber.transcribe_file(WAV_PATH + "nonexistent")
        except FileNotFoundError:
            assert True

    @requests_mock.Mocker()
    @pytest.mark.filterwarnings("ignore: Convert")
    @pytest.mark.filterwarnings("ignore: Transcribe")
    def test_transcribe_file_no_wav_caught(self, m):
        self.transcriber.set_raise_exceptions(False)
        assert None is self.transcriber.transcribe_file(WAV_PATH + "nonexistent")
