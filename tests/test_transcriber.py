import os
import tempfile
import unittest
import boto3
from moto import mock_s3
import json
import shutil
import pytest
import requests_mock
from app.speechkitty.transcriber import Transcriber

OGG_PATH = "sample/records/rg-170-74994043564-20231021-171101-1697897360.54.ogg"
WAV_PATH = "sample/records/rg-170-74994043564-20231021-171101-1697897360.54.wav"
JSON_PATH = "sample/records/rg-170-74994043564-20231021-171101-1697897360.54.json"
STORAGE_BASE_URL = "https://storage.yandexcloud.net"
AWS_ACCESS_KEY_ID = "test_access_key_id"
AWS_SECRET_ACCESS_KEY = "test_access_key"
STORAGE_BUCKET_NAME = "test_bucket"
TRANSCRIBE_API_KEY = "test_api_key"
WHISPER_ENDPOINT = ""


class TestTranscriber(unittest.TestCase):
    def setUp(self):
        os.environ["TRANSCRIBE_API_KEY"] = TRANSCRIBE_API_KEY
        self.transcriber = Transcriber(
            api="SpeechKit",
            language_code="ru-RU",
            mode="longRunningRecognize",
        )
        self.transcriber.storage_base_url = STORAGE_BASE_URL
        self.transcriber.storage_bucket_name = STORAGE_BUCKET_NAME

    @pytest.mark.filterwarnings("ignore: Convert")
    def test_to_ogg_fail_caught(self):
        self.transcriber.set_raise_exceptions(False)
        ogg_path = self.transcriber.to_ogg(WAV_PATH + "nonexistent")
        assert not ogg_path

    def test_to_ogg_fail_raised(self):
        self.transcriber.set_raise_exceptions(True)
        try:
            _ = self.transcriber.to_ogg(WAV_PATH + "nonexistent")
            assert False
        except FileNotFoundError:
            assert True

    def test_to_ogg(self):
        ogg_path = self.transcriber.to_ogg(WAV_PATH)
        assert ogg_path == tempfile.gettempdir() + "/" + os.path.basename(OGG_PATH)

    @mock_s3
    @pytest.mark.filterwarnings("ignore: Upload")
    def test_upload_ogg_s3_fail_caught(self):
        assert not self.transcriber.upload_ogg(OGG_PATH + "nonexistent")

    @mock_s3
    def test_upload_ogg_s3_fail_raised(self):
        self.transcriber.set_raise_exceptions(True)
        try:
            _ = self.transcriber.upload_ogg(OGG_PATH + "nonexistent")
            assert False
        except FileNotFoundError:
            assert True

    @mock_s3
    def test_upload_ogg_s3(self):
        conn = boto3.resource("s3")
        s3_resource = conn.create_bucket(Bucket="test_bucket")
        file_name = os.path.basename(OGG_PATH)
        file_link = f"{STORAGE_BASE_URL}/{STORAGE_BUCKET_NAME}/{file_name}"
        assert file_link == self.transcriber.upload_ogg(OGG_PATH, s3_resource.meta.client)

    @mock_s3
    def test_delete_ogg(self):
        temp_path = self.transcriber.temp_dir + "/" + os.path.basename(OGG_PATH)
        shutil.copyfile(OGG_PATH, temp_path)
        conn = boto3.resource("s3")
        s3_resource = conn.create_bucket(Bucket="test_bucket")
        self.transcriber.delete_ogg(temp_path, s3_resource.meta.client)

    @mock_s3
    def test_delete_ogg_fail_raised(self):
        self.transcriber.set_raise_exceptions(True)
        try:
            _ = self.transcriber.delete_ogg("")
            assert False
        except FileNotFoundError:
            assert True

    @mock_s3
    @pytest.mark.filterwarnings("ignore: Delete")
    def test_delete_ogg_fail_caught(self):
        self.transcriber.set_raise_exceptions(False)
        self.transcriber.delete_ogg("")

    def test_set_raise_exceptions(self):
        self.transcriber.set_raise_exceptions(True)
        assert True is self.transcriber.raise_exceptions

    @requests_mock.Mocker()
    def test_submit_task(self, m):
        task_id = "ca9x8ew1l8g06hgdlf6r"
        result = '{"id": "' + task_id + '"}'
        m.post(self.transcriber.transcribe_endpoint, text=result)
        file_name = os.path.basename(OGG_PATH)
        file_link = f"{STORAGE_BASE_URL}/{STORAGE_BUCKET_NAME}/{file_name}"
        assert task_id == self.transcriber.submit_task(file_link)

    @requests_mock.Mocker()
    def test_get_result(self, m):
        task_id = "ca9x8ew1l8g06hgdlf6r"
        with open(JSON_PATH, "r") as f:
            result = f.read()
        m.get(self.transcriber.operation_endpoint + "/" + task_id, text=result)
        assert json.loads(result) == self.transcriber.get_result(task_id)

    @mock_s3
    @requests_mock.Mocker()
    def test_transcribe_file_empty_result_raised(self, m):
        self.transcriber.set_raise_exceptions(True)
        conn = boto3.resource("s3")
        s3_resource = conn.create_bucket(Bucket="test_bucket")
        task_id = "ca9x8ew1l8g06hgdlf6r"
        result = '{"id": "' + task_id + '"}'
        m.post(self.transcriber.transcribe_endpoint, text=result)
        m.get(self.transcriber.operation_endpoint + "/" + task_id, text="")
        try:
            _ = self.transcriber.transcribe_file(WAV_PATH, s3_resource.meta.client)
            assert False
        except json.decoder.JSONDecodeError:
            assert True

    @mock_s3
    @requests_mock.Mocker()
    @pytest.mark.filterwarnings("ignore: Result")
    def test_transcribe_file_empty_result_caught(self, m):
        self.transcriber.set_raise_exceptions(False)
        conn = boto3.resource("s3")
        s3_resource = conn.create_bucket(Bucket="test_bucket")
        task_id = "ca9x8ew1l8g06hgdlf6r"
        result = '{"id": "' + task_id + '"}'
        m.post(self.transcriber.transcribe_endpoint, text=result)
        m.get(self.transcriber.operation_endpoint + "/" + task_id, text="")
        assert self.transcriber.transcribe_file(WAV_PATH, s3_resource.meta.client) is None

    @requests_mock.Mocker()
    @pytest.mark.filterwarnings("ignore: Upload")
    def test_transcribe_file_no_ogg(self, m):
        self.transcriber.set_raise_exceptions(False)
        task_id = "ca9x8ew1l8g06hgdlf6r"
        result = '{"id": "' + task_id + '"}'
        m.post(self.transcriber.transcribe_endpoint, text=result)
        with open(JSON_PATH, "r") as f:
            result = f.read()
        m.get(self.transcriber.operation_endpoint + "/" + task_id, text=result)
        assert None is self.transcriber.transcribe_file(WAV_PATH)

    @mock_s3
    @requests_mock.Mocker()
    def test_transcribe_file(self, m):
        conn = boto3.resource("s3")
        s3_resource = conn.create_bucket(Bucket="test_bucket")
        task_id = "ca9x8ew1l8g06hgdlf6r"
        result = '{"id": "' + task_id + '"}'
        m.post(self.transcriber.transcribe_endpoint, text=result)
        with open(JSON_PATH, "r") as f:
            result = f.read()
        m.get(self.transcriber.operation_endpoint + "/" + task_id, text=result)
        assert json.loads(result) == self.transcriber.transcribe_file(
            WAV_PATH, s3_resource.meta.client
        )
