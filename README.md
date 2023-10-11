# SpeechKitty

SpeechKitty is a wrapper for Yandex SpeechKit API to asyncronously transcribe audio records. 

> **NOTE**
> 
> It's very initial version of the package. It works perfectly in my case with Asterisk records so its version is 0.1 and not 0.0.1, but it's not tested in other use cases and with other records so you may want to wait for version 0.2 to try it.

## Key features:

1. Scans directory recursively for wav files.
2. Applies regex mask to include and exclude certain files.
3. Skips already transcribed files.
4. Does all intermediate work like converting and uploading audio files to object storage.
5. Transcribes and puts json and html files into directory next to audio files.
6. Can obfuscate html files' names using hash.

## Usage

You can use it as a package or a docker container.

### Python Package

0. Install required [ffmpeg](https://ffmpeg.org/download.html) library. Depending on your distribution the command may look like:

```console
sudo apt-get install ffmpeg
```
or
```console
sudo yum install ffmpeg
```

1. Install package.

```console
pip install speechkitty
```

2. Download scripts from sample directory at [project page](https://github.com/AlekseiPrishchepo/SpeechKitty/blob/main/sample) and modify them according to your task. 

3. Retrieve credentials from Yandex Cloud and use them to initialize objects.

### Docker Container

0. Install Docker.

1. Download project's code from [project page](https://github.com/AlekseiPrishchepo/SpeechKitty) on GitHub.

2. Retrieve all credentials from Yandex Cloud and put them into credentials.ini file. See links in comments in the ini file.

3. Build docker image. For that open project directory in terminal then type:

```console
docker build -t speechkitty .
```

Building image may take a while. After it finishes:

4. Run container. Assuming you have records in /mnt/Records and/or its subdirectories, the command will look like:

```console
docker run -i --rm -v /mnt/Records:/mnt/Records speechkitty /bin/bash -c "/usr/bin/bash /root/transcribe_directory.sh /mnt/Records"
```
Transcribing job may take a while. A good sign that indicates it's working is an appearance of some new json and html files in records directory.
