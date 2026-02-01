import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.speechkitty.transcriber import Transcriber

# Constants
WAV_PATH = "sample/records/test.wav"
OGG_PATH = "sample/records/test.ogg"
TASK_ID = "test_task_id"
RESULT_JSON = {"done": True, "result": "text", "file_name": "test.wav"}
WHISPER_RESULT = {"text": "whisper text"}


@pytest.fixture
def transcriber():
    t = Transcriber(
        api="SpeechKit",
        aws_access_key_id="test_key",
        aws_secret_access_key="test_secret",
        storage_bucket_name="test_bucket",
        transcribe_api_key="test_api_key",
    )
    # Mock services
    t.audio_converter.to_ogg_async = AsyncMock(return_value=OGG_PATH)
    t.cloud_storage.upload_file_async = AsyncMock(return_value="http://storage/test.ogg")
    t.cloud_storage.delete_file_async = AsyncMock()
    t.speech_service.submit_yandex_task_async = AsyncMock(return_value=TASK_ID)
    t.speech_service.get_yandex_result_async = AsyncMock(return_value=RESULT_JSON)
    return t


@pytest.mark.asyncio
async def test_transcribe_file_async_speechkit_success(transcriber):
    session = MagicMock()

    # Mock checking duration (which runs in executor)
    with patch("pydub.AudioSegment.from_file") as mock_audio, patch("os.unlink"):
        mock_audio.return_value.duration_seconds = 10.0
        mock_audio.return_value.channels = 1

        result = await transcriber.transcribe_file_async(WAV_PATH, session)

        assert result == RESULT_JSON

        transcriber.audio_converter.to_ogg_async.assert_called_once_with(WAV_PATH)
        transcriber.cloud_storage.upload_file_async.assert_called_once()
        transcriber.speech_service.submit_yandex_task_async.assert_called_once()
        transcriber.speech_service.get_yandex_result_async.assert_called_once()
        transcriber.cloud_storage.delete_file_async.assert_called_once()  # Should coordinate cloud delete


@pytest.mark.asyncio
async def test_transcribe_file_async_short_audio(transcriber):
    session = MagicMock()
    with patch("pydub.AudioSegment.from_file") as mock_audio:
        mock_audio.return_value.duration_seconds = 0.5  # Too short

        result = await transcriber.transcribe_file_async(WAV_PATH, session)
        assert result is None
        transcriber.audio_converter.to_ogg_async.assert_not_called()


@pytest.mark.asyncio
async def test_transcribe_file_async_whisper(transcriber):
    transcriber.api = "whisperx"
    transcriber.speech_service.transcribe_start_whisper_async = AsyncMock(
        return_value=WHISPER_RESULT
    )
    # Validate config check for whisper endpoint usually happens in init, but we force changed api here
    # assuming endpoint is set or handled. Actually Transcriber init checks it.
    # Let's set it.
    transcriber.speech_service.whisper_endpoint = "http://whisper"

    session = MagicMock()

    with patch("pydub.AudioSegment.from_file") as mock_audio:
        mock_audio.return_value.duration_seconds = 10.0

        result = await transcriber.transcribe_file_async(WAV_PATH, session)

        assert result == WHISPER_RESULT
        transcriber.speech_service.transcribe_start_whisper_async.assert_called_once_with(
            WAV_PATH, session
        )
        transcriber.audio_converter.to_ogg_async.assert_not_called()


@pytest.mark.asyncio
async def test_transcribe_file_async_webhook(transcriber):
    transcriber.webhook_url = "http://webhook.url"
    session = MagicMock()
    # Mock post context manager
    post_mock = MagicMock()
    post_mock.raise_for_status = MagicMock()

    # Create an async context manager mock
    post_ctx = MagicMock()
    post_ctx.__aenter__ = AsyncMock(return_value=post_mock)
    post_ctx.__aexit__ = AsyncMock(return_value=None)
    session.post.return_value = post_ctx

    with patch("pydub.AudioSegment.from_file") as mock_audio, patch("os.unlink"):
        mock_audio.return_value.duration_seconds = 10.0
        mock_audio.return_value.channels = 1

        result = await transcriber.transcribe_file_async(WAV_PATH, session)

        assert result == RESULT_JSON
        session.post.assert_called_once_with("http://webhook.url", json=RESULT_JSON)
