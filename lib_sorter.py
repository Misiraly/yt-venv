import hashlib
from datetime import datetime

import pandas as pd
import regex as re
import yaml

import constant_values as cv

# Constants
MUSIC_TABLE = "data/music_table.csv"
PLAYLISTS = "data/playlists.yaml"
# should have format as in "data/test-table.csv"


def create_playlist_file(pl_path=PLAYLISTS):
    yd = {}
    with open(pl_path, "w") as file:
        yaml.dump(yd, file)


def read_playlists(pl_path=PLAYLISTS) -> dict:
    with open(pl_path) as file:
        yd = yaml.safe_load(file)
    return yd


def get_playlist(playlist_name, pl_path=PLAYLISTS):
    yd = read_playlists(pl_path)
    if playlist_name in yd:
        return yd[playlist_name]
    print("Playlist doesn't exist or is empty.")
    return []


def write_to_playlist(pl_path, yd):
    with open(pl_path, "w") as file:
        yaml.dump(yd, file, default_flow_style=False, sort_keys=False, indent=2)


def _validate_song_list(song_list):
    if not isinstance(song_list, list):
        raise ValueError("The list of songs specified is not a list.", song_list)
    for uid in song_list:
        if not isinstance(uid, str) or len(uid) != cv.UID_LENGTH:
            raise ValueError("Each song UID must be a string of correct length.", uid)


def clean_playlist_input(numbers_list: str, available_indeces: list):
    raw_list = numbers_list.replace(" ", "").split(",")
    indeces = []
    for i in raw_list:
        if len(i) > 0 and i.isnumeric() and int(i) in available_indeces:
            indeces.append(int(i))
        elif len(i) > 0:
            print(f"Faulty index: {i}")
    return indeces


def manipulate_playlist_uids(
    playlist_name,
    uids,
    option,
    pl_path=PLAYLISTS,
    pl_out=PLAYLISTS,
    new_name=None,
):
    yd = read_playlists(pl_path)
    if option not in {"delete", "rename"}:
        _validate_song_list(uids)
    if option not in {"create", "remove_from_all"} and playlist_name not in yd:
        print(f"Playlist specified ({playlist_name}) doesn't exist.")
        return
    if option == "create":
        if playlist_name in yd:
            print(f"Playlist by this name ({playlist_name}) already exists.")
            return
        yd[playlist_name] = uids
    elif option == "delete":
        del yd[playlist_name]
    elif option == "add":
        yd[playlist_name] = yd[playlist_name] + uids
    elif option == "remove":
        yd[playlist_name] = [el for el in yd[playlist_name] if el not in uids]
    elif option == "remove_from_all":
        for key, playlist in yd.items():
            yd[key] = [el for el in playlist if el not in uids]
    elif option == "rename":
        yd[new_name] = yd.pop(playlist_name)
    else:
        print(f"Action '{option}' not possible for playlist manipulation.")
    write_to_playlist(pl_out, yd)


def manipulate_playlist(
    playlist_name,
    numbers_list,
    option,
    table_path=MUSIC_TABLE,
    pl_path=PLAYLISTS,
    pl_out=PLAYLISTS,
    new_name=None,
):
    df = pull_csv_as_df(table_path)
    indeces = clean_playlist_input(numbers_list, df.index.values)
    uids = df.iloc[indeces]["uid"].values.tolist()
    print(
        f"Attempting to {option} with input: {numbers_list}, playlist: {playlist_name}"
    )
    manipulate_playlist_uids(playlist_name, uids, option, pl_path, pl_out, new_name)


def retrieve_single_pl(cur_playlist) -> pd.DataFrame:
    df = pull_csv_as_df()
    ndf = pd.concat([df[df["uid"] == uid] for uid in cur_playlist], ignore_index=False)
    return ndf


def pull_csv_as_df(table_path=MUSIC_TABLE) -> pd.DataFrame:
    """Pull the music library from a CSV file into a DataFrame."""
    df = pd.read_csv(table_path, index_col=[0])
    return df


def generate_uid(title, url, path):
    base = f"{title}-{url}-{path}"
    return hashlib.sha1(base.encode()).hexdigest()[: cv.UID_LENGTH]


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
        song["uid"] = generate_uid(song["title"], song["url"], song["path"])
        df.loc[len(df.index)] = song
        # sort_values sorts all capital letters before lowercase letters...
        # we do not want this.
        out_df = df.sort_values(
            by=["title"], key=lambda col: col.str.lower(), ignore_index=True
        )
        out_df.to_csv(MUSIC_TABLE)
        return song["uid"]


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
    print(f"Deleting index {row_index} from music table.")
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
