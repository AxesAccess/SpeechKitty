from __future__ import annotations
import os
import tempfile
import traceback
import requests
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
    ) -> None:
        self.aws_key_id = aws_access_key_id
        self.aws_key = aws_secret_access_key
        self.storage_bucket_name = storage_bucket_name
        self.transcribe_api_key = transcribe_api_key
        self.language_code = language_code
        self.transcribe_endpoint = f"{self.transcribe_endpoint}/{mode}"
        self.temp_dir = tempfile.gettempdir()

    def wav_to_ogg(self, wav_path: str) -> str | None:
        try:
            a = AudioSegment.from_wav(wav_path)
            ogg_path = self.temp_dir + "/" + os.path.basename(wav_path[:-4]) + ".ogg"
            a.export(ogg_path, format="opus")
        except Exception:
            print("Exception occured while converting:", wav_path)
            traceback.print_exc()
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
        except Exception:
            traceback.print_exc()
            return

        return file_link

    def delete_ogg(self, ogg_path: str) -> None:
        session = boto3.session.Session(  # type: ignore
            region_name=self.region_name,
            aws_access_key_id=self.aws_key_id,
            aws_secret_access_key=self.aws_key,
        )
        s3 = session.client(service_name="s3", endpoint_url=self.storage_endpoint)
        os.unlink(ogg_path)
        try:
            for_deletion = [{"Key": os.path.basename(ogg_path)}]
            s3.delete_objects(Bucket=self.storage_bucket_name, Delete={"Objects": for_deletion})
        except Exception:
            traceback.print_exc()
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
        response = requests.get(self.operation_endpoint + "/" + id, headers=header)
        response = response.json()
        return response
