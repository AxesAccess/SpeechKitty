import os
import json
import traceback
from dotenv import find_dotenv, load_dotenv
import click
import logging
from speechkitty import Directory, Transcriber, Parser


@click.command()
@click.option(
    "rec_dir",
    "-d",
    "--dir",
    required=True,
    type=click.Path(),
    help="Path to records directory.",
)
@click.option(
    "extension",
    "--extension",
    default="wav",
    show_default=True,
    type=str,
    help="Audio file name extension.",
)
@click.option(
    "min_speakers",
    "--min_speakers",
    default=2,
    show_default=True,
    type=int,
    help="Minimum number of speakers. Used for diarization.",
)
@click.option(
    "max_speakers",
    "--max_speakers",
    default=3,
    show_default=True,
    type=int,
    help="Maximum number of speakers. Used for diarization.",
)
@click.option(
    "skip_processed",
    "--skip_processed",
    default=True,
    show_default=True,
    type=bool,
    help="Whether to skip already processed files.",
)
@click.option(
    "hash_func",
    "-h",
    "--hash_func",
    default=None,
    show_default=True,
    type=str,
    help="Hash function to encode resulting html files' names.",
)
def main(
    rec_dir,
    extension,
    min_speakers,
    max_speakers,
    skip_processed,
    hash_func,
):
    load_dotenv(find_dotenv())

    # Provides diarization
    api = "whisperX"
    language_code = os.environ.get("LANGUAGE_CODE")

    # Set up directory
    dir = Directory(rec_dir)

    include = f"^.+\\.{extension}$"
    # This is business specific, delete it from your production code
    exclude = "^.+(:?-in|-out)\\.wav$"

    # Find files recursively
    wavs = dir.get_records(
        regexp_include=include, regexp_exclude=exclude, skip_processed=skip_processed
    )

    wavs = list(set(wavs))

    transcriber = Transcriber(
        api=api,  # type: ignore
        language_code=language_code,  # type: ignore
        raise_exceptions=False,
    )

    transcriber.whisper_endpoint = (
        transcriber.whisper_endpoint  # type: ignore
        + f"&diarize=%20&min_speakers={min_speakers}&max_speakers={max_speakers}"
    )

    parser = Parser()

    for i, wav_path in enumerate(wavs, start=1):
        logger = logging.getLogger(__name__)
        logger.info(f"Starting processing record {i} of {len(wavs)}")
        logger.info(f"Transcribing {wav_path}")
        result = transcriber.transcribe_file(wav_path)

        # Compose resulting json path
        json_path = wav_path[:-4] + ".json"

        # Create empty json to skip the wav during next runs
        if not result:
            logger.info("Empty result.")
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
        htmlpath = parser.name_html(wav_path, hash_func=hash_func)
        logger.info(f"Writing hmtl to {htmlpath}")
        # Write table
        with open(htmlpath, "w") as f:
            f.write(html)


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    main()
