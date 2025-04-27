# SpeechKitty

![python-package](https://github.com/AxesAccess/SpeechKitty/actions/workflows/python-package.yml/badge.svg) ![docker-image](https://github.com/AxesAccess/SpeechKitty/actions/workflows/docker-image.yml/badge.svg) [![Upload Python Package](https://github.com/AxesAccess/SpeechKitty/actions/workflows/python-publish.yml/badge.svg)](https://github.com/AxesAccess/SpeechKitty/actions/workflows/python-publish.yml)

SpeechKitty is a wrapper for two Automatic Speech Recognition (ASR) services: Yandex SpeechKit and whisperX (powered by OpenAI's Whisper). It is designed to asynchronously transcribe audio recordings.

> **NOTE**
>
> This is an early version of the package. While it works reliably with Asterisk recordings in my setup, it has not been extensively tested with other use cases or audio formats. You may encounter bugs or limitations that have not yet been identified.

## Key features

1. Recursively scans directories for `.wav` files.
2. Supports regex patterns to include or exclude specific files.
3. Skips files that have already been transcribed.
4. Handles intermediate tasks such as audio conversion and uploading to object storage.
5. Generates transcription outputs as `.json` and `.html` files, saved alongside the audio files.
6. Offers the option to obfuscate `.html` file names using a hash function for added privacy.

## Usage

You can use SpeechKitty either as a Python package or within a Docker container, depending on your preference and setup requirements.

### Prerequisites

* [Yandex Cloud](https://cloud.yandex.com/en/) account. 
* [Bucket](https://cloud.yandex.ru/docs/storage/operations/buckets/create) at Object Storage. 
* [Static access key](https://cloud.yandex.ru/docs/iam/operations/sa/create-access-key) for Object Storage.
* [API key](https://cloud.yandex.ru/docs/iam/concepts/authorization/api-key) for SpeechKit.

-OR-

* Up and running [whisperX-REST](https://github.com/AxesAccess/whisperX-REST).

### Python Package

0. Install required [ffmpeg](https://ffmpeg.org/download.html) library.

2. Create venv (preferably) and install the package.

```console
pip install speechkitty
```

3. Download scripts from sample directory at [project page](https://github.com/AxesAccess/SpeechKitty/tree/main/sample):

* [.env-example](https://github.com/AxesAccess/SpeechKitty/blob/main/sample/.env-example) — rename to `.env`
* [transcribe_directory.py](https://github.com/AxesAccess/SpeechKitty/blob/main/sample/transcribe_directory.py)

4. Fill in credentials into `.env`.

5. Start transcribing a directory (`/mnt/Records` in the example below):

```console
python transcribe_directory.py /mnt/Records
```

### Docker Container

0. Install Docker Engine.

1. Download project code from the [project page](https://github.com/AxesAccess/SpeechKitty) on GitHub.

2. Put credentials into `.env` file.

3. Build the Docker image. Open the project directory in your terminal and run the following command:

```console
docker build -t speechkitty .
```
Building image may take a while. After it finishes:

4. Run container. Assuming you have records in `/mnt/Records` and/or its subdirectories, current directory in terminal is project's directory, and you have `.env` file in the `sample` directory, the command will look like:

```console
docker run -i --rm --env-file sample/.env -v /mnt/Records:/mnt/Records \
speechkitty /bin/bash -c "python sample/transcribe_directory.py /mnt/Records"
```
Another option is to use shell script:
```console
source sample/transcribe_directory.sh /mnt/Records
```
To rename html files using hash of the audio files names, add name of hash function as a second parameter like that:
```console
source sample/transcribe_directory.sh /mnt/Records md5
```
This approach is particularly useful if the records directory is hosted on a web server (with directory listing disabled for security). By obfuscating the HTML file names, you enhance privacy by preventing direct access to the audio files via predictable links. To retrieve the obfuscated HTML file names, you can use a database query like the following:

```sql
SELECT CONCAT(TO_HEX(MD5(recordingfile)), ".html") AS transcript
FROM your_table_name;
```
Replace `your_table_name` with the appropriate table name in your database.

Transcribing jobs may take some time to complete. You can verify that the process is running successfully by checking for the creation of new `.json` and `.html` files in the records directory. These files indicate that transcription results are being generated.
