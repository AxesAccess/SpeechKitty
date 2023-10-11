from setuptools import find_packages, setup

with open("./README.md", "r") as f:
    long_description = f.read()

setup(
    name="speechkitty",
    version="0.1.1",
    description="A wrapper for Yandex SpeechKit API to asyncronously transcribe audio records.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"": "app"},
    packages=find_packages(where="app"),
    url="https://github.com/AlekseiPrishchepo/SpeechKitty",
    author="Aleksei Prishchepo",
    author_email="speechkitty@outlook.com",
    license="Apache 2.0",
    zip_safe=False,
    install_requires=["boto3", "pandas", "pydub", "Requests"],
    python_requires=">=3.8",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3 :: Only",
        "Operating System :: OS Independent",
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
    ],
)
