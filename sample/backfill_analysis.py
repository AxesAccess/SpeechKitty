import os
import json
import pandas as pd
from dotenv import find_dotenv, load_dotenv
import click
import logging
import requests
from speechkitty import Directory


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
    "webhook_url",
    "--webhook-url",
    default="",
    show_default=True,
    type=str,
    help="URL to send JSON results to.",
)
@click.option(
    "left_suffix",
    "--left_suffix",
    default=".wav-in",
    show_default=True,
    type=str,
    help="Left channel's filename suffix. Used to exclude from search.",
)
@click.option(
    "right_suffix",
    "--right_suffix",
    default=".wav-out",
    show_default=True,
    type=str,
    help="Right channel's filename suffix. Used to exclude from search.",
)
@click.option(
    "extension",
    "-e",
    "--extension",
    default=".json",
    show_default=True,
    type=str,
    help="File extension to look for.",
)
@click.option(
    "limit",
    "-l",
    "--limit",
    default=10,
    show_default=True,
    type=int,
    help="Limit the number of files to process.",
)
@click.option(
    "dry_run",
    "--dry-run",
    default=False,
    show_default=True,
    type=bool,
    help="Enable dry run mode.",
)
def main(
    rec_dir,
    extension,
    limit,
    left_suffix,
    right_suffix,
    webhook_url,
    dry_run,
):
    logger = logging.getLogger(__name__)

    load_dotenv(find_dotenv())

    dir = Directory(rec_dir)
    regexp_include = ".+\\.json"
    json_files = dir.get_records(
        regexp_include=regexp_include, regexp_exclude=f"{right_suffix}|{left_suffix}"
    )

    records = pd.DataFrame(json_files, columns=["filename"]).tail(limit)

    for i, row in enumerate(records.iterrows(), start=1):
        logger.info(f"Starting processing transcription {i} of {len(records)}")

        with open(row[1].filename, "r") as f:
            result = json.load(f)

        # Send webhook if URL is provided
        if webhook_url and result.get("segments"):
            try:
                logger.info(f"Sending webhook to {webhook_url}")
                # Add file name to payload
                file_name = os.path.basename(row[1].filename)
                result["file_name"] = file_name.replace(".json", ".wav")
                result["transcript_id"] = ".".join(file_name.split(".")[:-1])
                result["quiet"] = True
                if not dry_run:
                    sales_signals_api_key = os.environ.get("WEBHOOK_API_KEY")
                    headers = {"Authorization": f"Bearer {sales_signals_api_key}"}
                    response = requests.post(webhook_url, json=result, headers=headers, timeout=10)
                    response.raise_for_status()
                    logger.info(f"Webhook sent successfully: {response.status_code}")
            except Exception as e:
                logger.error(f"Webhook error: {e}")


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    main()
