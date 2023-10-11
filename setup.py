from setuptools import find_packages, setup

with open("./README.md", "r") as f:
    long_description = f.read()

setup(
    name="speechkitty",
    version="0.1.0",
    description="A wrapper for Yandex SpeechKit API to asyncronously transcribe audio records.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    package_dir={"": "app"},
    packages=find_packages(where="app"),
    url="https://github.com/AlekseiPrishchepo/SpeechKitty",
    author="Aleksei Prishchepo",
    author_email="speechkitty@outlook.com",
    license="Apache 2.0",
    zip_safe=False,
)
