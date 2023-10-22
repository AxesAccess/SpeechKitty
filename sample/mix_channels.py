# Given the phone call recording consists of two files for each part a conversation
# and these files have suffixes .wav-in and .wav-out (inbound and outbound)
# the script combines two records into a stereo file

import sys
import pandas as pd
from pydub import AudioSegment
from speechkitty import Directory


def main():
    try:
        rec_dir = sys.argv[1]
    except Exception:
        print("Not enough arguments.")
        return 1

    dir = Directory(rec_dir)

    include = "(?:-in|-out)\\.wav"
    wavs = dir.get_wavs(regexp_include=include, skip_processed=True)

    df = pd.DataFrame(wavs, columns=["filename"])

    df.loc[:, "recordingfile"] = df["filename"].str.replace(".wav-in", "")
    df.loc[:, "recordingfile"] = df["recordingfile"].str.replace(".wav-out", "")
    df.loc[:, "channel"] = df["filename"].apply(
        lambda x: "inbound" if "wav-in" in x else "outbound"
    )

    if len(df) == 0:
        return

    df = df.pivot_table(
        index=["recordingfile"],
        values="filename",
        columns=["channel"],
        aggfunc="first",
    )

    for row in df.itertuples():
        inbound = AudioSegment.from_wav(row.inbound)
        outbound = AudioSegment.from_wav(row.outbound)
        inbound = inbound.pan(-1)
        outbound = outbound.pan(1)
        mix = inbound.overlay(outbound)
        mix.export(row.Index, format="wav")


if __name__ == "__main__":
    main()
