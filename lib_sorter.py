from datetime import datetime

import pandas as pd
import regex as re

import constant_values as cv

# Constants
MUSIC_TABLE = "data/music_table.csv"
# should have format as in "data/test-table.csv"


def pull_csv_as_df() -> pd.DataFrame:
    """Pull the music library from a CSV file into a DataFrame."""
    df = pd.read_csv(MUSIC_TABLE, index_col=[0])
    return df


def write_table_to_csv(title_in: str, url: str, duration: int) -> None:
    """Write a new song into the library and save the library sorted by titles.

    Parameters
    ----------
    title_in : str
        Title of the song.
    url : str
        URL of the song.
    duration : int
        Duration of the song in seconds.
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
        out_df.to_csv(MUSIC_TABLE)


def is_path_occupied(path: str) -> bool:
    """Check if a given path is occupied in the library.

    Parameters
    ----------
    path : str
        Path to check.

    Returns
    -------
    bool
        True if the path is occupied, False otherwise.
    """
    df = pull_csv_as_df()
    return path in df["path"].values


def song_to_table_csv(song) -> None:
    """Write a new song into the library and save the library sorted by titles.

    Parameters
    ----------
    song : dict
        Dictionary containing song attributes.
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
        out_df.to_csv(MUSIC_TABLE)


def correct_title(title_in: str) -> str:
    """Return a title string stripped of non-standard characters.

    Parameters
    ----------
    title_in : str
        Input title string.

    Returns
    -------
    str
        Corrected title string.
    """
    title = re.sub(r"[^a-zA-Z0-9 ]", "", title_in).strip()
    return title


def del_from_csv(row_index: int) -> None:
    """Remove a row from the library given the row index.

    Parameters
    ----------
    row_index : int
        Index of the row to remove.
    """
    df = pull_csv_as_df()
    new_df = df.drop([row_index]).reset_index(drop=True)
    new_df.to_csv(MUSIC_TABLE)


def increase_watched(title: str) -> None:
    """Increase the watched count of a given song.

    Parameters
    ----------
    title : str
        Title of the song.
    """
    df = pull_csv_as_df()
    df.loc[df["title"] == title, "watched"] += 1
    df.to_csv(MUSIC_TABLE)


def add_attribute(title: str, attribute: str, attribute_col: str) -> None:
    """Add an attribute to a song in the library.

    Parameters
    ----------
    title : str
        Title of the song.
    attribute : str
        Attribute value to add.
    attribute_col : str
        Column name of the attribute.
    """
    df = pull_csv_as_df()
    df.loc[df["title"] == title, attribute_col] = attribute
    df.to_csv(MUSIC_TABLE)


def fill_attributes(song, cols, values) -> None:
    """Fill multiple attributes for a song in the library.

    Parameters
    ----------
    song : dict
        Dictionary containing song attributes.
    cols : list
        List of column names to update.
    values : list
        List of values to update in the corresponding columns.
    """
    df = pull_csv_as_df()
    for col, val in zip(cols, values):
        df.loc[df["title"] == song["title"], col] = val
    df.to_csv(MUSIC_TABLE)
