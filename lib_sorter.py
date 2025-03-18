from datetime import datetime

import pandas as pd
import regex as re

import constant_values as cv

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
        df.loc[len(df.index)] = [
            title_in,
            url,
            duration,
            str(datetime.now()),
            0,
            cv.NO_PATH,
        ]
        # sort_values sorts all capital letters before lowercase letters...
        # we do not want this.
        out_df = df.sort_values(
            by=["title"], key=lambda col: col.str.lower(), ignore_index=True
        )
        out_df.to_csv(music_table)


def is_path_occupied(path):
    df = pull_csv_as_df()
    return path in df['path'].values


def song_to_table_csv(song):
    """
    Given the title, url and duration of a song, writes it into the library.
    The library is saved after sorting by titles.
    """
    df = pull_csv_as_df()
    if song["title"] not in df["title"].values:
        if "add_date" not in song:
            song["add_date"] = str(datetime.now())
        if "watched" not in song:
            song["watched"] = 0
        df.loc[len(df.index)] = song
        # sort_values sorts all capital letters before lowercase letters...
        # we do not want this.
        out_df = df.sort_values(
            by=["title"], key=lambda col: col.str.lower(), ignore_index=True
        )
        out_df.to_csv(music_table)
    # return song


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
    df.loc[df["title"] == title, "watched"] += 1
    df.to_csv(music_table)


def add_attribute(title, attribute, attribute_col):
    """
    Adds path of download to song.
    """
    df = pull_csv_as_df()
    df.loc[df["title"] == title, attribute_col] = attribute
    df.to_csv(music_table)


def fill_attributes(song, cols, values):
    df = pull_csv_as_df()
    for col, val in zip(cols, values):
        df.loc[df["title"] == song["title"], col] = val
    df.to_csv(music_table)
