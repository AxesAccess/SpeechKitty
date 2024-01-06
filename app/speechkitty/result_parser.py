from __future__ import annotations
import hashlib
import os
import warnings
import pandas as pd


class Parser:
    # Header to put in the html file
    header = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
"https://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="https://www.w3.org/1999/xhtml">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
        <title>Recording</title>
        <style>
            table {max-width: 800px; border-collapse: collapse; border: 0px; margin-left: auto;
            margin-right: auto; font-family: sans-serif; font-size: small;}
            th {padding: 4px; border-left: 0px; border-right: 0px; border-bottom: 1px solid #ddd;
            text-align: center; font-weight: normal!important; font-family: monospace, monospace;}
            td {padding: 4px; border-left: 0px; border-right: 0px; border-bottom: 1px solid #ddd;
            font-weight: normal!important; width: 45%;}
        </style>
    </head>
    <body style="padding:0px; margin:0px; word-break: normal;">
"""
    # Footer
    footer = """
    </body>
</html>
"""

    def __init__(self) -> None:
        pass

    def parse_result(self, result, channel_tag: int = 1) -> pd.DataFrame:
        """Parses resulting json into a dataframe"""
        df = pd.DataFrame()
        # whisperX API
        if "segments" in result:
            if len(result["segments"]) == 0:
                return df
            for chunk in result["segments"]:
                row = dict()
                row["startTime"] = [chunk["start"]]
                row["endTime"] = [chunk["end"]]
                row["channelTag"] = [chunk["speaker"]] if "speaker" in chunk else [channel_tag]
                row["text"] = [chunk["text"]]
                df = pd.concat([df, pd.DataFrame(row)], ignore_index=True)
            df.loc[:, "startTime"] = pd.to_numeric(df["startTime"])
            df.loc[:, "endTime"] = pd.to_numeric(df["endTime"])
            df = df.sort_values("startTime")
            return df.reset_index(drop=True)

        if "chunks" not in result["response"]:
            return df

        # SpeechKit API
        for chunk in result["response"]["chunks"]:
            row = dict()
            row["startTime"] = [chunk["alternatives"][0]["words"][0]["startTime"].replace("s", "")]
            row["endTime"] = [chunk["alternatives"][0]["words"][-1]["endTime"].replace("s", "")]
            row["channelTag"] = [chunk["channelTag"]]
            row["text"] = [chunk["alternatives"][0]["text"]]
            df = pd.concat([df, pd.DataFrame(row)], ignore_index=True)

        df.loc[:, "startTime"] = pd.to_numeric(df["startTime"])
        df.loc[:, "endTime"] = pd.to_numeric(df["endTime"])
        df = df.sort_values("startTime")

        return df.reset_index(drop=True)

    def create_html(self, df: pd.DataFrame) -> str:
        if df.empty:
            return ""
        df = df.pivot_table(
            index=["startTime", "endTime"],
            values="text",
            columns=["channelTag"],
            aggfunc="first",
            fill_value="",
        )
        table = df.to_html(index=True)
        return self.header + table + self.footer

    def name_html(self, wav_path: str, hash_func: str = "") -> str:
        wav_name = os.path.basename(wav_path)
        # Exclude variable length digest algorithms
        algorithms_exclude = {"shake_128", "shake_256"}
        algorithms = hashlib.algorithms_guaranteed - algorithms_exclude
        if hash_func in algorithms:
            h = getattr(hashlib, hash_func)
            wav_name = os.path.basename(wav_path)
            html_name = h(wav_name.encode()).hexdigest() + ".html"
        else:
            if hash_func in algorithms_exclude:
                warnings.warn("Hash_func is not supported. Filename won't change.")
            html_name = wav_name[:-4] + ".html"
        return os.path.dirname(wav_path) + "/" + html_name
