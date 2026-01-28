import asyncio
import json
import os
import sys
import traceback
import aiohttp
import click
from speechkitty import Directory, Transcriber, Parser
from dotenv import find_dotenv, load_dotenv


async def process_file(wav_path, transcriber, parser, session, semaphore, filename_hash_func):
    async with semaphore:
        try:
            result = await transcriber.transcribe_file_async(wav_path, session)

            # Compose resulting json path
            json_path = wav_path[:-4] + ".json"

            # Create empty json to skip the wav during next runs
            if not result:
                with open(json_path, "w") as f:
                    f.write("")
                return

            with open(json_path, "w") as f:
                f.write(json.dumps(result, ensure_ascii=False))

            # Parse json into pandas dataframe
            try:
                # cpu bound, but fast enough for now, or run in executor
                df = parser.parse_result(result)
            except Exception:
                print("exception in parse_result():", wav_path)
                print(traceback.format_exc())
                return

            # Create html table
            if df is None:
                return
            html = parser.create_html(df)
            html_path = parser.name_html(wav_path, hash_func=filename_hash_func)
            # Write table
            with open(html_path, "w") as f:
                f.write(html)
        except Exception:
            print(f"Error processing {wav_path}: {traceback.format_exc()}")


async def run_processing(wavs, api, language_code, filename_hash_func, limit):
    transcriber = Transcriber(
        api=api,  # type: ignore
        language_code=language_code,  # type: ignore
        raise_exceptions=False,
    )
    parser = Parser()

    semaphore = asyncio.Semaphore(limit)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for wav_path in wavs:
            task = process_file(
                wav_path, transcriber, parser, session, semaphore, filename_hash_func
            )
            tasks.append(task)

        await asyncio.gather(*tasks)


@click.command()
@click.argument("rec_dir", type=click.Path(exists=True))
@click.option("--hash-func", default="", help="Hash function for filenames")
@click.option("--limit", default=10, help="Max simultaneous API requests")
def main(rec_dir, hash_func, limit):
    load_dotenv(find_dotenv())

    api = os.environ.get("API")
    language_code = os.environ.get("LANGUAGE_CODE")

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
        print("No files found.")
        return

    wavs = list(set(wavs))

    # If you want to limit number of records processed
    # wavs = random.choices(wavs, k=min(len(wavs), 10))

    asyncio.run(run_processing(wavs, api, language_code, hash_func, limit))


if __name__ == "__main__":
    main()
