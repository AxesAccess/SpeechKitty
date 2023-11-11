from __future__ import annotations
import os
import tempfile
import traceback
import warnings
import requests
import time
from pydub import AudioSegment
import boto3


class Transcriber:
    region_name = "ru-central1"
    storage_endpoint = "https://storage.yandexcloud.net"
    storage_base_url = "https://storage.yandexcloud.net"
    transcribe_endpoint = "https://transcribe.api.cloud.yandex.net/speech/stt/v2"
    operation_endpoint = "https://operation.api.cloud.yandex.net/operations"

    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        storage_bucket_name: str,
        transcribe_api_key: str,
        language_code: str,
        mode: str = "longRunningRecognize",
        raise_exceptions: bool = False,
    ) -> None:
        self.aws_key_id = aws_access_key_id
        self.aws_key = aws_secret_access_key
        self.storage_bucket_name = storage_bucket_name
        self.transcribe_api_key = transcribe_api_key
        self.language_code = language_code
        self.transcribe_endpoint = f"{self.transcribe_endpoint}/{mode}"
        self.temp_dir = tempfile.gettempdir()
        self.raise_exceptions = raise_exceptions

    def set_raise_exceptions(self, raise_exceptions: bool = True):
        self.raise_exceptions = raise_exceptions

    def to_ogg(self, file_path: str) -> str | None:
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
                return
        return ogg_path

    def upload_ogg(self, file_path: str, s3_client=None) -> str | None:
        file_name = os.path.basename(file_path)
        file_link = f"{self.storage_base_url}/{self.storage_bucket_name}/{file_name}"
        if not s3_client:
            session = boto3.session.Session(  # type: ignore
                region_name=self.region_name,
                aws_access_key_id=self.aws_key_id,
                aws_secret_access_key=self.aws_key,
            )
            s3_client = session.client(service_name="s3", endpoint_url=self.storage_endpoint)
        try:
            s3_client.upload_file(file_path, self.storage_bucket_name, file_name)
        except Exception as e:
            if self.raise_exceptions:
                raise e
            else:
                warnings.warn(f"Upload error: {file_path} {traceback.format_exc()}")
                return
        return file_link

    def delete_ogg(self, ogg_path: str, s3_client=None) -> None:
        if not s3_client:
            session = boto3.session.Session(  # type: ignore
                region_name=self.region_name,
                aws_access_key_id=self.aws_key_id,
                aws_secret_access_key=self.aws_key,
            )
            s3_client = session.client(service_name="s3", endpoint_url=self.storage_endpoint)
        try:
            os.unlink(ogg_path)
            for_deletion = [{"Key": os.path.basename(ogg_path)}]
            s3_client.delete_objects(
                Bucket=self.storage_bucket_name, Delete={"Objects": for_deletion}
            )
        except Exception as e:
            if self.raise_exceptions:
                raise e
            else:
                warnings.warn(f"Delete error: {ogg_path} {traceback.format_exc()}")
                return

    def submit_task(self, file_link: str) -> str:
        body = {
            "config": {"specification": {"languageCode": self.language_code}},
            "audio": {"uri": file_link},
        }
        header = {"Authorization": f"Api-Key {self.transcribe_api_key}"}
        response = requests.post(self.transcribe_endpoint, headers=header, json=body)
        data = response.json()
        return data["id"]

    def get_result(self, id: str):
        header = {"Authorization": f"Api-Key {self.transcribe_api_key}"}
        try:
            response = requests.get(self.operation_endpoint + "/" + id, headers=header)
            response = response.json()
        except Exception as e:
            if self.raise_exceptions:
                raise e
            else:
                warnings.warn(f"Result error: {traceback.format_exc()}")
                return
        return response

    def transcribe_file(self, wav_path: str, s3_client=None):
        ogg_path = self.to_ogg(wav_path)

        # Upload ogg to object storage
        ogg_link = self.upload_ogg(ogg_path, s3_client)

        # If upload ended with error
        if ogg_link is None:
            return

        # Start transcribing task
        id = self.submit_task(ogg_link)

        result = ""
        # Limit number of attempts to get result
        for i in range(200):
            time.sleep(3)
            result = self.get_result(id)
            # If there's an error, stop trying
            try:
                if result["done"]:
                    break
            except Exception:
                break

        # TODO Calculate pause before first request of result
        # using length of the audio (10 seconds for 1 minute * 1 channel)

        if not result:
            return

        # Delete ogg from temp_dir and object storage
        self.delete_ogg(ogg_path, s3_client)

        return result
