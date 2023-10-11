# SpeechKitty

SpeechKitty is a wrapper for Yandex SpeechKit API to asyncronously transcribe audio records. 

Note! It's very initial version of the package. It works perfectly in my case with Asterisk records so its version is 0.1 and not 0.0.1, but it's not tested in other use cases and with other records so you may want to wait for version 0.2 to try it.

## Usage

You can use it as a package or a docker container.

### Python Package

1. Install package.

```
pip install speechkitty
```

2. Download scripts from sample directory at [project page](https://github.com/AlekseiPrishchepo/SpeechKitty/blob/main/sample) and modify them according to your task. 

3. Retrieve credentials from Yandex Cloud and put then into scripts or pass them in arguments.

### Docker Container

0. Install Docker.

1. Download project's code from [project page](https://github.com/AlekseiPrishchepo/SpeechKitty) on GitHub.

2. Retrieve all credentials from Yandex Cloud and put them into credentials.ini file. See links in comments in the ini file.

3. Build docker image. For that open project directory in terminal then type:

```
docker build -t speechkitty .
```

Building image may take a while. After it finishes:

4. Run container. Assuming you have records in /mnt/Records or its subdirectories, the command will look like:

```
docker run -i --rm -v /mnt/Records:/mnt/Records speechkitty /bin/bash -c "/usr/bin/bash /root/transcribe_directory.sh"
```
Transcribing job may take a while. A good sign that indicates it's working is an appearance of some new json and html files in records directory.


