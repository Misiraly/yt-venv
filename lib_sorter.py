from datetime import datetime

import pandas as pd
import regex as re

music_table = "data/music_table.csv"
# should have format as in "data/test-table.csv"


def pull_csv_as_df():
    df = pd.read_csv(music_table, index_col=[0])
    return df


def write_table_to_csv(title_in, url, duration):
    """
    Given the title, url and duration of a song, writes it into the library.
    The library is saved after sorting by titles.
    """
    df = pull_csv_as_df()
    if title_in not in df["title"].values:
        # TODO: do not use a list but a safer dictionary, so if column doesn't exist, it wont throw a hissy fit
        df.loc[len(df.index)] = [title_in, url, duration, str(datetime.now()), 0]
        # sort_values sorts all capital letters before lowercase letters...
        # we do not want this.
        out_df = df.sort_values(
            by=["title"], key=lambda col: col.str.lower(), ignore_index=True
        )
        out_df.to_csv(music_table)


def correct_title(title_in):
    """
    Returns a title-string stripped of non-standard characters.
    """
    title = re.sub(r"[^a-zA-Z0-9 ]", "", title_in)
    title = title.lstrip()
    return title


def del_from_csv(row_index):
    """
    Removes a row from the library given the row index.
    """
    df = pull_csv_as_df()
    new_df = df.drop([row_index]).reset_index(drop=True)
    new_df.to_csv(music_table)


def increase_watched(title):
    """
    Increases the watchedness of a given song identified by row index.
    """
    df = pull_csv_as_df()
    df.loc[df['title'] == title, 'watched'] += 1
    df.to_csv(music_table)