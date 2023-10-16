import json
import os
import sys
import time
import traceback
from speechkitty import Directory, Transcriber, Parser


def main():
    try:
        rec_dir = sys.argv[1]
        aws_access_key_id = sys.argv[2]
        aws_secret_access_key = sys.argv[3]
        storage_bucket_name = sys.argv[4]
        transcribe_api_key = sys.argv[5]
        transcribe_api_key = sys.argv[5]
    except Exception:
        print("Not enough arguments.")
        return 1

    try:
        filename_hash_func = sys.argv[6]
    except Exception:
        filename_hash_func = None

    # This is business specific, delete it from your production code
    exclude = "^.+(:?-in|-out)\\.wav$"

    # Set up directory
    directory = Directory(rec_dir)

    # Find files recursively
    wavs = directory.get_wavs(regexp_exclude=exclude)

    # If there're no files found just exit silently
    if not wavs:
        return

    # This is business specific, delete it from your production code
    for i in range(len(wavs)):
        if "wav-mix" in wavs[i]:
            new = wavs[i].replace(".wav-mix", "")
            os.rename(wavs[i], new)
            wavs[i] = new

    wavs = list(set(wavs))

    # If you want to limit number of records processed
    # wavs = random.choices(wavs, k=min(len(wavs), 10))

    transcriber = Transcriber(
        aws_access_key_id,
        aws_secret_access_key,
        storage_bucket_name,
        transcribe_api_key,
    )
    parser = Parser()

    for wav_path in wavs:
        # Convert wav to ogg
        ogg_path = transcriber.wav_to_ogg(wav_path)
        # If there's an error
        if ogg_path is None:
            # Create empty json to skip the wav during next runs
            json_path = wav_path[:-4] + ".json"
            with open(json_path, "w") as f:
                f.write("")
            continue
        # Upload ogg to object storage
        ogg_link = transcriber.upload_ogg(ogg_path)
        # Start transcribing task
        id = transcriber.submit_task(ogg_link)
        # Limit number of attempts to get result
        for i in range(100):
            time.sleep(3)
            result = transcriber.get_result(id)
            if result["done"]:
                break
        # Delete ogg from temp_dir and object storage
        transcriber.delete_ogg(ogg_path)
        # Compose resulting json path
        json_path = wav_path[:-4] + ".json"
        with open(json_path, "w") as f:
            f.write(json.dumps(result))
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
