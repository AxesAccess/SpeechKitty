import os
import tempfile
import traceback
import requests
from pydub import AudioSegment
import boto3


class Transcriber:
    def __init__(
        self,
        aws_access_key_id,
        aws_secret_access_key,
        storage_bucket_name,
        transcribe_api_key,
        language_code="ru-RU",
        mode="longRunningRecognize"

    ) -> None:
        self.region_name = "ru-central1"
        self.aws_key_id = aws_access_key_id
        self.aws_key = aws_secret_access_key
        self.sample_rate = 48000
        self.ogg_bitrate = "256k"
        self.storage_endpoint = "https://storage.yandexcloud.net"
        self.storage_base_url = "https://storage.yandexcloud.net"
        self.storage_bucket_name = storage_bucket_name
        self.transcribe_endpoint = f"https://transcribe.api.cloud.yandex.net/speech/stt/v2/{mode}"
        self.transcribe_api_key = transcribe_api_key
        self.language_code = language_code
        self.operation_endpoint = "https://operation.api.cloud.yandex.net/operations"
        self.temp_dir = tempfile.gettempdir()

    def wav_to_ogg(self, wav_path):
        try:
            a = AudioSegment.from_wav(wav_path)
            a = a.set_frame_rate(self.sample_rate)
            ogg_path = self.temp_dir + "/" + os.path.basename(wav_path[:-4]) + ".ogg"
            a.export(ogg_path, format="opus", bitrate=self.ogg_bitrate)
        except Exception:
            print("Exception occured while converting:", wav_path)
            traceback.print_exc()
            return
        return ogg_path

    def upload_ogg(self, file_path):
        session = boto3.session.Session(
            region_name=self.region_name,
            aws_access_key_id=self.aws_key_id,
            aws_secret_access_key=self.aws_key,
        )
        s3 = session.client(service_name="s3", endpoint_url=self.storage_endpoint)
        file_name = os.path.basename(file_path)
        file_link = f"{self.storage_base_url}/{self.storage_bucket_name}/{file_name}"
        try:
            s3.upload_file(file_path, self.storage_bucket_name, file_name)
        except Exception:
            traceback.print_exc()
            return

        return file_link

    def delete_ogg(self, ogg_path):
        session = boto3.session.Session(
            region_name=self.region_name,
            aws_access_key_id=self.aws_key_id,
            aws_secret_access_key=self.aws_key,
        )
        s3 = session.client(service_name="s3", endpoint_url=self.storage_endpoint)
        os.unlink(ogg_path)
        try:
            for_deletion = [{"Key": os.path.basename(ogg_path)}]
            s3.delete_objects(
                Bucket=self.storage_bucket_name, Delete={"Objects": for_deletion}
            )
        except Exception:
            traceback.print_exc()
        return

    def submit_task(self, file_link):
        body = {
            "config": {"specification": {"languageCode": self.language_code}},
            "audio": {"uri": file_link},
        }
        header = {"Authorization": f"Api-Key {self.transcribe_api_key}"}
        response = requests.post(self.transcribe_endpoint, headers=header, json=body)
        data = response.json()
        return data["id"]

    def get_result(self, id):
        header = {"Authorization": f"Api-Key {self.transcribe_api_key}"}
        response = requests.get(self.operation_endpoint + "/" + id, headers=header)
        response = response.json()
        return response
