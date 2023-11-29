# SpeechKitty

![python-package](https://github.com/AlekseiPrishchepo/SpeechKitty/actions/workflows/python-package.yml/badge.svg) ![docker-image](https://github.com/AlekseiPrishchepo/SpeechKitty/actions/workflows/docker-image.yml/badge.svg) [![Upload Python Package](https://github.com/AlekseiPrishchepo/SpeechKitty/actions/workflows/python-publish.yml/badge.svg)](https://github.com/AlekseiPrishchepo/SpeechKitty/actions/workflows/python-publish.yml)

SpeechKitty is a wrapper for two ASR services: Yandex SpeechKit and whisperX (based on OpenAI's Whisper) intended to asynchronously transcribe audio records.

> **NOTE**
> 
> It's very initial version of the package. It works perfectly in my case with Asterisk records, but it's not tested in other use cases and with other records so you may want to wait for version 0.2 to try it.

## Key features:

1. Scans directory recursively for wav files.
2. Applies regex mask to include and exclude certain files.
3. Skips already transcribed files.
4. Does all intermediate work like converting and uploading audio files to object storage.
5. Transcribes and puts json and html files into directory next to audio files.
6. Can obfuscate html files' names using hash.

## Usage

You can use it as a package or a docker container.

### Prerequisites

* [Yandex Cloud](https://cloud.yandex.com/en/) account. 
* [Bucket](https://cloud.yandex.ru/docs/storage/operations/buckets/create) at Object Storage. 
* [Static access key](https://cloud.yandex.ru/docs/iam/operations/sa/create-access-key) for Object Storage.
* [API key](https://cloud.yandex.ru/docs/iam/concepts/authorization/api-key) for SpeechKit.

-OR-

* Up and running [whisperX-REST](https://github.com/AlekseiPrishchepo/whisperX-REST).

### Python Package

0. Install required [ffmpeg](https://ffmpeg.org/download.html) library.

2. Create venv (preferably) and install package.

```console
pip install speechkitty
```

3. Download scripts from sample directory at [project page](https://github.com/AlekseiPrishchepo/SpeechKitty/tree/main/sample):

* [.env-example](https://github.com/AlekseiPrishchepo/SpeechKitty/blob/main/sample/.env-example) — rename to ```.env```
* [transcribe_directory.py](https://github.com/AlekseiPrishchepo/SpeechKitty/blob/main/sample/transcribe_directory.py)

4. Fill in credentials into ```.env```

5. Start transcribing a directory (```/mnt/Records``` in the example below):

```console
python transcribe_directory.py /mnt/Records
```

### Docker Container

0. Install Docker.

1. Download project's code from [project page](https://github.com/AlekseiPrishchepo/SpeechKitty) on GitHub.

2. Put credentials into ```.env``` file.

3. Build docker image. For that open project directory in terminal then type:

```console
docker build -t speechkitty .
```

Building image may take a while. After it finishes:

4. Run container. Assuming you have records in ```/mnt/Records``` and/or its subdirectories, current directory in terminal is project's directory, and you have ```.env``` file in the ```sample``` directory, the command will look like:

```console
docker run -i --rm --env-file sample/.env -v /mnt/Records:/mnt/Records \
speechkitty /bin/bash -c "python sample/transcribe_directory.py /mnt/Records"
```
Or you can use shell script:
```console
source sample/transcribe_directory.sh /mnt/Records
```
To name html files using hash of the audio files names, add hash function as a second parameter like that:
```console
source sample/transcribe_directory.sh /mnt/Records md5
```
This can be useful if records directory is being published using a web server (with option preventing directory listing, of course) and you don't want to reveal names of audio files to prevent files from being downloaded via direct link. So you can put something like ```SELECT CONCAT(TO_HEX(MD5(recordingfile)), ".html") AS transcript``` into the DB view to get names of the html files.

Transcribing job may take a while. A good sign that indicates it's working is an appearance of some new json and html files in records directory.
