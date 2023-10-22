# Re-creates html files in a directory.
# Run it after changing html template to make html files uniform.

import json
import sys
import traceback
from speechkitty import Directory, Parser


def main():
    try:
        rec_dir = sys.argv[1]
    except Exception:
        print("Not enough arguments.")
        return 1

    try:
        filename_hash_func = str(sys.argv[2])
    except Exception:
        filename_hash_func = ""

    # Set up directory
    directory = Directory(rec_dir)

    # Find files recursively
    jsons = directory.get_wavs(regexp_include=".+\\.json", skip_processed=False)

    parser = Parser()

    for filename in jsons:
        with open(filename, "r") as f:
            result = f.read()
        result = json.loads(result)
        wav_path = filename[:-5] + ".wav"
        try:
            df = parser.parse_result(result)
        except Exception:
            print("exception in parse_result():", wav_path)
            print(traceback.format_exc())
            continue

        if df is None:
            continue
        html = parser.create_html(df)
        html_path = parser.name_html(wav_path, hash_func=filename_hash_func)
        # Write table
        with open(html_path, "w") as f:
            f.write(html)


if __name__ == "__main__":
    main()
