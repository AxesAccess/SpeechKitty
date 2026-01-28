import os
import requests
import traceback
import warnings


class SpeechService:
    transcribe_endpoint = "https://transcribe.api.cloud.yandex.net/speech/stt/v2"
    operation_endpoint = "https://operation.api.cloud.yandex.net/operations"

    def __init__(
        self,
        api_type: str,
        transcribe_api_key: str = "",
        language_code: str = "ru-RU",
        whisper_endpoint: str = "",
        mode: str = "longRunningRecognize",
        raise_exceptions: bool = False,
    ) -> None:
        self.api_type = api_type.lower()
        self.transcribe_api_key = transcribe_api_key
        self.language_code = language_code
        self.whisper_endpoint = whisper_endpoint
        self.transcribe_endpoint = f"{self.transcribe_endpoint}/{mode}"
        self.raise_exceptions = raise_exceptions

    def submit_yandex_task(self, file_link: str) -> str:
        body = {
            "config": {"specification": {"languageCode": self.language_code}},
            "audio": {"uri": file_link},
        }
        header = {"Authorization": f"Api-Key {self.transcribe_api_key}"}
        try:
            response = requests.post(self.transcribe_endpoint, headers=header, json=body)
            response.raise_for_status()
            data = response.json()
            return data["id"]
        except Exception as e:
            if self.raise_exceptions:
                raise e
            warnings.warn(f"Submit task error: {traceback.format_exc()}")
            return ""

    def get_yandex_result(self, task_id: str):
        header = {"Authorization": f"Api-Key {self.transcribe_api_key}"}
        try:
            response = requests.get(f"{self.operation_endpoint}/{task_id}", headers=header)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if self.raise_exceptions:
                raise e
            warnings.warn(f"Result error: {traceback.format_exc()}")
            return None

    def transcribe_start_whisper(self, wav_path: str):
        try:
            with open(wav_path, "rb") as f:
                headers = {"accept": "application/json"}
                files = {"audio": f}
                response = requests.post(self.whisper_endpoint, headers=headers, files=files)
                response.raise_for_status()
            return response.json()
        except Exception as e:
            if self.raise_exceptions:
                raise e
            warnings.warn(f"Transcribe error: {traceback.format_exc()}")
            return None
