import os
import tempfile
import unittest
import boto3
from moto import mock_s3
from app.speechkitty.transcriber import Transcriber

OGG_PATH = "sample/records/out-88001000800-102-20231014-184547-1697298346.17.ogg"
WAV_PATH = "sample/records/out-88001000800-102-20231014-184547-1697298346.17.wav"
STORAGE_BASE_URL = "https://storage.yandexcloud.net"
AWS_ACCESS_KEY_ID = "test_access_key_id"
AWS_SECRET_ACCESS_KEY = "test_access_key"
STORAGE_BUCKET_NAME = "test_bucket"
TRANSCRIBE_API_KEY = "test_api_key"


class TestTranscriber(unittest.TestCase):
    def setUp(self):
        self.transcriber = Transcriber(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            storage_bucket_name=STORAGE_BUCKET_NAME,
            transcribe_api_key=TRANSCRIBE_API_KEY,
            language_code="ru-RU",
            mode="longRunningRecognize",
        )

    def test_wav_to_ogg_fail(self):
        ogg_path = self.transcriber.wav_to_ogg(WAV_PATH + "nonexistent")
        assert not ogg_path

    def test_wav_to_ogg(self):
        ogg_path = self.transcriber.wav_to_ogg(WAV_PATH)
        assert ogg_path == tempfile.gettempdir() + "/" + os.path.basename(OGG_PATH)

    @mock_s3
    def test_upload_ogg_s3_fail(self):
        assert not self.transcriber.upload_ogg(OGG_PATH)

    @mock_s3
    def test_upload_ogg_s3(self):
        conn = boto3.resource("s3")
        s3_resource = conn.create_bucket(Bucket="test_bucket")
        file_name = os.path.basename(OGG_PATH)
        file_link = f"{STORAGE_BASE_URL}/{STORAGE_BUCKET_NAME}/{file_name}"
        assert file_link == self.transcriber.upload_ogg(
            OGG_PATH, s3_resource.meta.client
        )

    @mock_s3
    def test_delete_ogg(self):
        ogg_path = self.transcriber.wav_to_ogg(WAV_PATH)
        self.transcriber.delete_ogg(ogg_path)
