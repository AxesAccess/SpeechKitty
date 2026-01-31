from __future__ import annotations
import os
import time
import warnings
import traceback
import aiohttp
from pydub import AudioSegment

from typing import Optional

from .cloud_storage import CloudStorage
from .audio_converter import AudioConverter
from .speech_service import SpeechService


class Transcriber:
    def __init__(
        self,
        api: str,
        aws_access_key_id: str = "",
        aws_secret_access_key: str = "",
        storage_bucket_name: str = "",
        transcribe_api_key: str = "",
        language_code: str = "",
        whisper_endpoint: str = "",
        webhook_url: str = "",
        mode: str = "longRunningRecognize",
        raise_exceptions: bool = False,
    ) -> None:
        self.api = str(api).lower()
        self.webhook_url = webhook_url
        self.raise_exceptions = raise_exceptions

        # Initialize services
        self.cloud_storage = CloudStorage(
            aws_access_key_id=(
                aws_access_key_id if aws_access_key_id else os.environ.get("AWS_ACCESS_KEY_ID", "")
            ),
            aws_secret_access_key=(
                aws_secret_access_key
                if aws_secret_access_key
                else os.environ.get("AWS_SECRET_ACCESS_KEY", "")
            ),
            bucket_name=(
                storage_bucket_name
                if storage_bucket_name
                else os.environ.get("STORAGE_BUCKET_NAME", "")
            ),
            raise_exceptions=raise_exceptions,
        )

        self.audio_converter = AudioConverter(raise_exceptions=raise_exceptions)

        self.speech_service = SpeechService(
            api_type=self.api,
            transcribe_api_key=(
                transcribe_api_key
                if transcribe_api_key
                else os.environ.get("TRANSCRIBE_API_KEY", "")
            ),
            language_code=language_code if language_code else os.environ.get("LANGUAGE_CODE", ""),
            whisper_endpoint=(
                whisper_endpoint if whisper_endpoint else os.environ.get("WHISPER_ENDPOINT", "")
            ),
            mode=mode,
            raise_exceptions=raise_exceptions,
        )

        self.validate_config()

    def validate_config(self):
        if self.api not in ["whisperx", "speechkit"]:
            raise ValueError('Valid values for API are "whisperx" or "speechkit".')

        if self.api == "whisperx" and not self.speech_service.whisper_endpoint:
            raise ValueError(
                "Endpoint for whisperX must be set in the .env or passed in the parameter"
            )

        if self.api == "speechkit":
            if not (
                self.cloud_storage.aws_access_key_id
                and self.cloud_storage.aws_secret_access_key
                and self.cloud_storage.bucket_name
                and self.speech_service.transcribe_api_key
            ):
                raise ValueError(
                    "Yandex Cloud credentials must be set in .env or passed in the parameters"
                )

    def set_raise_exceptions(self, raise_exceptions: bool = True):
        # Used for tests
        self.raise_exceptions = raise_exceptions
        self.cloud_storage.raise_exceptions = raise_exceptions
        self.audio_converter.raise_exceptions = raise_exceptions
        self.speech_service.raise_exceptions = raise_exceptions

    def to_ogg(self, file_path: str) -> str:
        return self.audio_converter.to_ogg(file_path)

    async def to_ogg_async(self, file_path: str) -> str:
        return await self.audio_converter.to_ogg_async(file_path)

    def upload_ogg(self, file_path: str, s3_client=None) -> Optional[str]:
        return self.cloud_storage.upload_file(file_path, s3_client)

    async def upload_ogg_async(self, file_path: str, s3_client=None) -> Optional[str]:
        return await self.cloud_storage.upload_file_async(file_path, s3_client)

    def delete_ogg(self, ogg_path: str, s3_client=None) -> None:
        try:
            os.unlink(ogg_path)
            self.cloud_storage.delete_file(ogg_path, s3_client)
        except Exception as e:
            if self.raise_exceptions:
                raise e
            else:
                warnings.warn(f"Delete error: {ogg_path} {traceback.format_exc()}")

    async def delete_ogg_async(self, ogg_path: str, s3_client=None) -> None:
        import asyncio

        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, os.unlink, ogg_path)
            await self.cloud_storage.delete_file_async(ogg_path, s3_client)
        except Exception as e:
            if self.raise_exceptions:
                raise e
            else:
                warnings.warn(f"Delete error: {ogg_path} {traceback.format_exc()}")

    def submit_task(self, file_link: str) -> str:
        return self.speech_service.submit_yandex_task(file_link)

    async def submit_task_async(self, file_link: str, session: aiohttp.ClientSession) -> str:
        return await self.speech_service.submit_yandex_task_async(file_link, session)

    def get_result(self, id: str):
        return self.speech_service.get_yandex_result(id)

    async def get_result_async(self, id: str, session: aiohttp.ClientSession):
        return await self.speech_service.get_yandex_result_async(id, session)

    async def send_webhook_async(
        self, data: dict, session: aiohttp.ClientSession, file_name: Optional[str] = None
    ):
        if not self.webhook_url:
            return
        try:
            payload = data.copy()
            if file_name:
                payload["file_name"] = file_name
            async with session.post(self.webhook_url, json=payload) as response:
                response.raise_for_status()
        except Exception as e:
            if self.raise_exceptions:
                raise e
            else:
                warnings.warn(f"Webhook error: {traceback.format_exc()}")

    def transcribe_file(self, wav_path: str, s3_client=None) -> Optional[str]:
        # Check duration of the audio record
        try:
            audio = AudioSegment.from_file(wav_path)
            audio_duration = audio.duration_seconds
            audio_channels = audio.channels
            if audio_duration < 1.0:
                return
        except Exception as e:
            if self.raise_exceptions:
                raise e
            else:
                warnings.warn(f"Transcribe error: {e}")
                return

        # If using Whisper API, send a request and we're done
        if self.api == "whisperx":
            return self.speech_service.transcribe_start_whisper(wav_path)

        ogg_path = self.to_ogg(wav_path)

        # Upload ogg to object storage
        ogg_link = self.upload_ogg(ogg_path, s3_client)

        # If upload ended with error
        if ogg_link is None:
            return

        # Start transcribing task
        id = self.submit_task(ogg_link)

        result = ""
        # Calculate pause before first request of result
        # using length of the audio (10 seconds per 1 minute * 1 channel)
        time.sleep(audio_duration * audio_channels / 6)
        # Limit number of attempts to get result
        for _ in range(10):
            result = self.get_result(id)
            # If there's an error, stop trying
            if result is None or result.get("done", False):
                break
            time.sleep(3)

        if not result:
            return

        # Delete ogg from temp_dir and object storage
        self.delete_ogg(ogg_path, s3_client)

        return result

    async def transcribe_file_async(
        self, wav_path: str, session: aiohttp.ClientSession, s3_client=None
    ) -> Optional[str]:
        import asyncio

        # Check duration of the audio record
        # Running pydub check in executor as it is blocking
        loop = asyncio.get_running_loop()

        def check_duration():
            try:
                audio = AudioSegment.from_file(wav_path)
                return audio.duration_seconds, audio.channels
            except Exception as e:
                # If checking fails, we might want to log/warn and return None
                # But here we just return exceptions to be handled by caller or wrapped
                raise e

        try:
            audio_duration, audio_channels = await loop.run_in_executor(None, check_duration)
            if audio_duration < 1.0:
                return None
        except Exception as e:
            if self.raise_exceptions:
                raise e
            else:
                warnings.warn(f"Transcribe error: {e}")
                return None

        # If using Whisper API, send a request and we're done
        if self.api == "whisperx":
            # Note: session is passed from caller
            return await self.speech_service.transcribe_start_whisper_async(wav_path, session)

        # Convert to OGG
        ogg_path = await self.to_ogg_async(wav_path)
        if not ogg_path:
            return None

        # Upload ogg to object storage
        ogg_link = await self.upload_ogg_async(ogg_path, s3_client)

        # If upload ended with error
        if ogg_link is None:
            return None

        # Start transcribing task
        id = await self.submit_task_async(ogg_link, session)
        if not id:
            return None

        result = None
        # Calculate pause before first request of result
        await asyncio.sleep(audio_duration * audio_channels / 6)

        # Limit number of attempts to get result
        for _ in range(10):
            result_data = await self.get_result_async(id, session)
            # If there's an error, stop trying
            if result_data is None or result_data.get("done", False):
                result = result_data
                break
            await asyncio.sleep(3)

        if not result:
            return None

        # Delete ogg from temp_dir and object storage
        await self.delete_ogg_async(ogg_path, s3_client)

        # Extract file name and send webhook
        file_name = os.path.basename(wav_path)
        await self.send_webhook_async(result, session, file_name=file_name)

        return result
