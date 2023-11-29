import json
import os
import sys
import traceback
from speechkitty import Directory, Transcriber, Parser
from dotenv import find_dotenv, load_dotenv


def main():
    load_dotenv(find_dotenv())

    api = os.environ.get("API")
    aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    storage_bucket_name = os.environ.get("STORAGE_BUCKET_NAME")
    transcribe_api_key = os.environ.get("TRANSCRIBE_API_KEY")
    language_code = os.environ.get("LANGUAGE_CODE")
    whisper_endpoint = os.environ.get("WHISPER_ENDPOINT")

    try:
        rec_dir = sys.argv[1]
    except Exception:
        print("Not enough arguments.")
        return 1

    try:
        filename_hash_func = str(sys.argv[2])
    except Exception:
        filename_hash_func = ""

    include = "^.+\\.wav$"
    # This is business specific, delete it from your production code
    exclude = "^.+(:?-in|-out)\\.wav$"

    # Set up directory
    directory = Directory(rec_dir)

    # Find files recursively
    wavs = directory.get_records(
        regexp_include=include, regexp_exclude=exclude, skip_processed=True
    )

    # If there're no files found just exit silently
    if not wavs:
        return

    wavs = list(set(wavs))

    # If you want to limit number of records processed
    # wavs = random.choices(wavs, k=min(len(wavs), 10))

    transcriber = Transcriber(
        api=api,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        storage_bucket_name=storage_bucket_name,
        transcribe_api_key=transcribe_api_key,
        language_code=language_code,
        raise_exceptions=False,
        whisper_endpoint=whisper_endpoint,
    )
    parser = Parser()

    for wav_path in wavs:
        result = transcriber.transcribe_file(wav_path)

        # Compose resulting json path
        json_path = wav_path[:-4] + ".json"

        # Create empty json to skip the wav during next runs
        if len(result) == 0:
            with open(json_path, "w") as f:
                f.write("")
            continue

        with open(json_path, "w") as f:
            f.write(json.dumps(result, ensure_ascii=False))

        # Parse json into pandas dataframe
        try:
            df = parser.parse_result(result)
        except Exception:
            print("exception in parse_result():", wav_path)
            print(traceback.format_exc())
            continue
        # Create html table
        if df is None:
            continue
        html = parser.create_html(df)
        html_path = parser.name_html(wav_path, hash_func=filename_hash_func)
        # Write table
        with open(html_path, "w") as f:
            f.write(html)


if __name__ == "__main__":
    main()
