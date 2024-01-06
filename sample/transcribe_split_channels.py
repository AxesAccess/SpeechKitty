import os
import json
import pandas as pd
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
    default=".wav",
    show_default=True,
    type=str,
    help="Audio file name extension.",
)
@click.option(
    "left_suffix",
    "--left_suffix",
    default=".wav-in",
    show_default=True,
    type=str,
    help="Left channel's filename suffix.",
)
@click.option(
    "right_suffix",
    "--right_suffix",
    default=".wav-out",
    show_default=True,
    type=str,
    help="Right channel's filename suffix.",
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
    left_suffix,
    right_suffix,
    skip_processed,
    hash_func,
):

    load_dotenv(find_dotenv())

    api = os.environ.get("API")
    language_code = os.environ.get("LANGUAGE_CODE")

    dir = Directory(rec_dir)
    regexp_include = f".+(?:{left_suffix}|{right_suffix})\\{extension}"
    wavs = dir.get_records(regexp_include=regexp_include, skip_processed=skip_processed)

    records = pd.DataFrame(wavs, columns=["filename"])

    records.loc[:, "recordingfile"] = records["filename"].str.replace(left_suffix, "", regex=False)
    records.loc[:, "recordingfile"] = records["recordingfile"].str.replace(
        right_suffix, "", regex=False
    )
    records.loc[:, "channel"] = records["filename"].apply(
        lambda x: "inbound" if left_suffix in x else "outbound"
    )

    records = records.pivot_table(
        index=["recordingfile"],
        values="filename",
        columns=["channel"],
        aggfunc="first",
    )

    transcriber = Transcriber(
        api=api,  # type: ignore
        language_code=language_code,  # type: ignore
        raise_exceptions=False,
    )
    parser = Parser()

    for i, row in enumerate(records.itertuples(), start=1):
        logger = logging.getLogger(__name__)

        logger.info(f"Starting processing record {i} of {len(records)}")

        df = pd.DataFrame()
        # Repeat for both channels' recordings
        for channel, filename in enumerate([row.inbound, row.outbound], start=1):
            logger.info(f"Transcribing {filename}")
            # If there's no filename
            if type(filename) is not str:
                logger.info("Empty filename.")
                continue
            # Process file
            result = transcriber.transcribe_file(filename)
            # Compose resulting json path
            json_path = filename[:-4] + ".json"
            with open(json_path, "w") as f:
                # If result is empty create empty json file
                # to skip the wav during next runs
                if not result:
                    logger.info("Empty result.")
                    f.write("")
                    continue
                else:
                    f.write(json.dumps(result, ensure_ascii=False))
            df_tmp = parser.parse_result(result, channel)
            df = pd.concat([df, df_tmp], ignore_index=True)

        logger.info(f"Combined DataFrame length: {len(df)}")

        if len(df) == 0:
            continue
        df = df.sort_values("startTime")
        html = parser.create_html(df)
        htmlpath = parser.name_html(row.Index, hash_func=hash_func)
        logger.info(f"Writing hmtl to {htmlpath}")
        with open(htmlpath, "w") as f:
            f.write(html)


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    main()
