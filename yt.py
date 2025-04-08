import os

import numpy as np
from vlc import MediaPlayer
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

import constant_values as cv
import lib_sorter as ls
import ui_first
from modules import search_text as st

# Constants
EXIT_CHARS = {"q", "exit"}
YES_CHARS = {"y", "Y"}
LIBRARY = "library"
EXT = "ogg"


def _root_prompt(prompt: str) -> str:
    """Prompt the user for input and handle exit conditions."""
    cmd_input = input(prompt)
    if cmd_input.lower() in EXIT_CHARS:
        exit()
    return cmd_input


def not_sure() -> bool:
    return _root_prompt("Are you sure? [y/N]: ") not in YES_CHARS


def article_decorator(func):
    """Decorator to show article and print closer after function execution."""

    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        kwargs["bu"].show_article()
        kwargs["bu"].print_closer()

    return wrapper


def divide_decorator(func):
    """Decorator to print divider lines before and after function execution."""

    def wrapper(*args, **kwargs):
        print("-" * cv.SCR_L)
        func(*args, **kwargs)
        print("-" * cv.SCR_L)

    return wrapper


def check_title_fix(title: str, url: str, s_title: str) -> str:
    """Check and fix the title if it already exists or is empty."""
    if ls.is_path_occupied(f"{LIBRARY}/{title}.{EXT}"):
        print("\nWarning! The title already exists in the library!")
        print(s_title)
        print(url)
        new_name = input("Filename to use (if empty, a hash from url will be used): ")
        title = new_name

    if title == "":
        print("\nWarning! The title is empty!")
        print(s_title)
        print(url)
        new_name = input("Filename to use (if empty, a hash from url will be used): ")
        title = new_name
        if new_name == "":
            title = ls.correct_title(url)
            print(
                "Warning! Empty string given! Using video url hash as music file name!"
            )
    return title


def playTheSong(url: str):
    """Play the song from the given URL."""
    ydl_opts = {"format": "bestaudio", "no_check_certificate": True}
    with YoutubeDL(ydl_opts) as ydl:
        song_info = ydl.extract_info(url, download=False)
    media = MediaPlayer(song_info["url"], ":no-video")
    return song_info, media


def playExisting(bu):
    """Play an existing song from the library."""
    song = dict(bu.song)
    extract = song["duration"] == cv.NO_DURATION
    download = song["path"] == cv.NO_PATH
    if download:
        title = ls.correct_title(song["title"])
        title = check_title_fix(title, song["url"], song["title"])
        path = f"{LIBRARY}/{title}.{EXT}"
    else:
        path = song["path"]
    ydl_opts = {
        "extract_audio": True,
        "format": "bestaudio",
        "no_check_certificate": True,
        "outtmpl": path,
    }
    if extract or download:
        with YoutubeDL(ydl_opts) as ydl:
            song_info = ydl.extract_info(song["url"], download)
            if download:
                song["path"] = path
                ls.add_attribute(song["title"], path, "path")
        if extract:
            song["duration"] = song_info["duration"]
            ls.add_attribute(song["title"], song["duration"], "duration")
    bu.song = song
    return MediaPlayer(path), song


def playNonExistent(url: str):
    """Play a song that is not in the library."""
    song = {}
    path = f"{LIBRARY}/{cv.TEMPORARY}.{EXT}"
    ydl_opts = {
        "extract_audio": True,
        "format": "bestaudio",
        "no_check_certificate": True,
        "outtmpl": path,
    }
    with YoutubeDL(ydl_opts) as ydl:
        song_info = ydl.extract_info(url, download=True)
    song["title"] = ls.correct_title(song_info["title"])
    title = ls.correct_title(song_info["title"])
    title = check_title_fix(title, url, song_info["title"])
    n_path = f"{LIBRARY}/{title}.{EXT}"
    song = {
        "title": song_info["title"],
        "duration": song_info["duration"],
        "path": n_path,
        "url": url,
    }
    ls.song_to_table_csv(song)
    os.rename(path, n_path)
    print(f"File saved to {n_path}")
    return MediaPlayer(n_path), song


def play_add_Song(bu, isplaylist=False):
    """Play a song, add it to the library if not yet there."""
    media, song = playExisting(bu)
    post_vars = ui_first.cli_gui(song["title"], song["duration"], media, isplaylist)
    if post_vars["watched"]:
        ls.increase_watched(song["title"])
    return post_vars["breaker"]


def play_on_list(bu, cmd_input):
    """Play a song tracked by the library."""
    cmd_num = int(cmd_input)
    if cmd_num not in bu.table.index:
        print("[TRY AGAIN], number not on list")
    else:
        bu.song = bu.table.iloc[cmd_num].copy(deep=True)
        play_add_Song(bu)
        bu.print_closer()
        bu.show_article()


def play_playlist(playlist, bu, info):
    """Play a playlist of songs."""
    print(info.center(cv.SCR_L, "-"))
    for el in playlist:
        bu.song = bu.table.iloc[el].copy(deep=True)
        title = bu.song["title"]
        print(f"[nepst: {title.lower()}]".center(cv.SCR_L))
        # have to handle it here otherwise the playlist breaks
        try:
            breaker = play_add_Song(bu, isplaylist=True)
        except DownloadError:
            print(f"\ncant play this fucking song: {title}!")
            print("Error in the pleilist... going further!!...")
            continue
        bu.print_closer()
        if breaker == "x":
            break
    print("\nthe pleilist... it is so over...\n")
    bu.show_article()


# TODO: ALMOS SAME AS ABOVE!
def autist_shuffle(song_no, bu):
    """Play a song repeatedly until the user exits."""
    print("AUTIST SHUFFLE".center(cv.SCR_L, "-"))
    bu.song = bu.table.iloc[song_no].copy(deep=True)
    title = bu.song["title"]
    print(f"[run: {title.lower()}]")
    tries = 0
    while True:
        # have to handle it here otherwise the playlist breaks
        try:
            breaker = play_add_Song(bu, isplaylist=True)
        except DownloadError:
            print(f"\ncant play this fucking song: {title}!")
            print("Error in the autist pleilist... !!...")
            tries += 1
            if tries > 2:
                print("song gives error 3 times, it's over".center(cv.SCR_L, "*"))
                break
            continue
        bu.print_closer()
        if breaker == "x":
            break
    print("\nwestphalen... its over...\n")


def play_new(bu, cmd_input):
    """Play a song not yet tracked by our library."""
    if "https" not in cmd_input:
        search_table(cmd_input)
    else:
        url = cmd_input
        print(url)
        media, song = playNonExistent(url)
        post_vars = ui_first.cli_gui(
            song["title"], song["duration"], media, isplaylist=False
        )
        if post_vars["watched"]:
            ls.increase_watched(song["title"])
        bu.song = song
        bu.print_closer()
        bu.show_article()


def init_player(bu, cmd_input):
    """Initialize the player with a song from the library or a new song."""
    if cmd_input.isnumeric():
        play_on_list(bu, cmd_input)
    else:
        play_new(bu, cmd_input)


@article_decorator
def play_random_force(bu):
    """Play a random song from the library."""
    r = np.random.randint(0, len(bu.table.index))
    bu.song = bu.table.iloc[r].copy(deep=True)
    title = bu.song["title"]
    print(f"\nPlaying a random song... [{title}]\n")
    play_add_Song(bu, isplaylist=True)


# @article_decorator
def play_random(bu):
    """Prompt the user to play a random song from a list of options."""
    while True:
        rand_choice = np.random.choice(
            len(bu.table.index), 5, replace=False
        )  # TODO: non-hard-coded number of choices?
        songs = bu.table.iloc[rand_choice].copy(deep=True)
        titles = songs[["title"]]
        print(titles)
        playit = _root_prompt("\n>>Play first song on the list?[y/N/r]> ")
        if playit.lower() in {"r", "random"}:
            continue
        if playit in YES_CHARS:
            playit = str(songs.index[0])
            print(f"\nPlaying a random song... [{songs.iloc[0]["title"]}]\n")
        break
    return playit


@article_decorator
def replay(bu):
    """Replay the current song."""
    play_add_Song(bu)


def shuffle(bu):
    """Shuffle and play all songs in the library."""
    playlist = np.copy(bu.table.index.values)
    np.random.shuffle(playlist)
    play_playlist(playlist, bu, "SHUFFLE")


def play_from_newest(bu):
    """Play songs from the newest to the oldest."""
    df = bu.table.sort_values(by="add_date", ascending=False)
    playlist = np.copy(df.index.values)
    info = "PLAYING BY DATE JOE ROGAN PODCAST BY NIGHT ALL DAY"
    play_playlist(playlist, bu, info)


def play_autist(bu, cmd_input):
    """Play a song repeatedly based on user input."""
    song_no = cmd_input[7:]  # TODO length constant???
    if song_no.isnumeric():
        autist_shuffle(int(song_no), bu)
    else:
        print("\n")
        print(f'Parsed value "{song_no}" is not numeric!'.center(cv.SCR_L, "*"))
        print("\n")


def play_manual_playlist(bu, cmd_input):
    songs = cmd_input.replace(" ", "").split(",")
    playlist = []
    for song_no in songs:
        if song_no.isnumeric() and int(song_no) in bu.table.index.values:
            playlist.append(int(song_no))
        else:
            print("\n[WARNING] Faulty element within the list!")
            print(f"Element in question: `{song_no}`\n")
    play_playlist(playlist, bu, "MY PLAYLIST. FUCK OFF WE ARE FULL.")


def find_options(cmd_input):
    """Find and return search options from the command input."""
    op_STR = " --cutoff "
    if op_STR in cmd_input:
        return tuple(cmd_input.split(op_STR))
    return cmd_input, 5


@divide_decorator
def search_table(cmd_input=None):
    """Search the library for a song based on user input."""
    lib = ls.pull_csv_as_df()
    if cmd_input is None:
        cmd_input = _root_prompt("Search [optional: --cutoff {int}]: ")
    s_word, cutoff = find_options(cmd_input)
    s_lib = st.sorted_by_word(s_word, "title", lib, int(cutoff))
    print(s_lib[["title"]])


@divide_decorator
def delete_song():
    """Delete a song from the library."""
    df = ls.pull_csv_as_df()
    cmd_input = _root_prompt("Song to delete (via index): ")
    if not cmd_input.isnumeric():
        print(f"[ERROR] wrong index ({cmd_input}), use only integers.")
        return
    if int(cmd_input) not in df.index:
        print(f"[ERROR] index ({cmd_input}) out of bounds.")
        return
    row_index = int(cmd_input)
    song = df.iloc[row_index]
    title = song["title"]
    print("! Are you sure to delete the song: ")
    print(f"! > {title}")
    if song["path"] != cv.NO_PATH:
        print("! This will also delete the file: ")
        print(f"! > {os.path.abspath(song['path'])}")
    make_sure = _root_prompt("? [y/N]: ")
    if make_sure in YES_CHARS:
        ls.del_from_csv(row_index)
        if song["path"] != cv.NO_PATH:
            os.remove(song["path"])
        print(f"[INFO] deleted song: {title}")
    else:
        print("[INFO] deletion stopped.")


@divide_decorator
def redownload_song(bu):
    """Redownload a song from the library."""
    df = bu.table
    cmd_input = _root_prompt("Song to re-download (via index): ")
    if not cmd_input.isnumeric():
        print(f"[ERROR] wrong index ({cmd_input}), use only integers.")
        return
    row_index = int(cmd_input)
    if row_index not in df.index:
        print(f"[ERROR] index ({row_index}) out of bounds.")
        return
    song = dict(df.iloc[row_index])
    title = song["title"]
    print("! Are you sure to re-download the song: ")
    print(f"! > {title}")
    make_sure = _root_prompt("? [y/N]: ")
    if make_sure not in YES_CHARS:
        print("[INFO] re-download aborted.")
        return
    if song["path"] != cv.NO_PATH:
        os.remove(song["path"])
        print(f"[INFO] deleted song: {title}")
        song["path"] = cv.NO_PATH
    print(f"[INFO] attempting to re-download song: {title}")
    bu.song = song
    ls.add_attribute(song["title"], cv.NO_PATH, "path")
    playExisting(bu)


def single_play(bu):
    """Play a song from a URL only once. Doesn't add it to the library."""

    cmd_input = _root_prompt("[>] song URL [played only once]: ")
    if "https" not in cmd_input:
        print("[TRY AGAIN], can't comprehend")
    else:
        url = cmd_input
        song_info, media = playTheSong(url)
        v_title = song_info["title"]
        v_duration = song_info["duration"]
        bu.song = {
            "title": song_info["title"],
            "url": url,
            "duration": song_info["duration"],
            "path": cv.NO_PATH,
            "watched": 0,
            "add_date": "0",
        }
        ui_first.cli_gui(v_title, v_duration, media, False)
        bu.print_closer()
        bu.show_article()


def correct_title(bu):
    """Correct the title of a song in the library."""
    cmd_input = _root_prompt("[>] index of title to correct: ")
    if cmd_input.isnumeric():
        cmd_num = int(cmd_input)
        if cmd_num not in bu.table.index:
            print("[ERROR], number not on list")
        print("Song to be corrected: ")
        song = bu.table.iloc[cmd_num].copy(deep=True)
        ole_title = song["title"]
        print(f"> {ole_title}")
        if not_sure():
            return
        else:
            ls.del_from_csv(cmd_num)
            title = ls.correct_title(song["title"])
            ls.write_table_to_csv(title, song["url"], song["duration"])
            bu.show_article()


def rename_title(bu):
    """Rename the title of a song in the library."""
    cmd_input = _root_prompt("[>] index of title to rename: ")
    if cmd_input.isnumeric():
        cmd_num = int(cmd_input)
        if cmd_num not in bu.table.index:
            print("[ERROR], number not on list")
        print("Song to be renamed: ")
        song = bu.table.iloc[cmd_num].copy(deep=True)
        ole_title = song["title"]
        print(f"> {ole_title}")
        if not_sure():
            return
        else:
            song = bu.table.iloc[cmd_num].copy(deep=True)
            new_title = _root_prompt("New title >")
            if new_title == "":
                new_title = f"__DEFAULT_{str(np.random.randint(0, 1000))}"
            ls.del_from_csv(cmd_num)
            ls.write_table_to_csv(new_title, song["url"], song["duration"])
            bu.show_article()


def command_help():
    print("Command list: ")
    print("  - ser :: search for song")
    print("  - del :: delete a song")
    print("  - correct title :: remove unusual characters from title")
    print("  - rename title :: rename title")
    print("  - tab :: print the list of songs")
    print("  - date :: print songs are by date, descending")
    print("  - freq :: print songs arranged by popularity, descending")
    print("  - re-freq :: print songs arranged by popularity, ascending")
    print("  - r :: replay a song")
    print("  - single :: play a url without adding it to the library")
    print("  - random :: play a random song. Use '--force' to play it automatically")
    print("  - shuffle :: shuffles all the songs into one playlist, plays it")
    print("  - by_date :: play the songs by date of addition to the list")
    print("  - `,` :: playlist of song numbers divided by a comma, eg `12, 3, 8`")
    print("  - autist :: play the same song over and over again")
    print("  - help :: prints this list")


def decision_tree(bu, cmd_input):
    """
    Handle user commands and navigate the decision tree.
    Could be implemented with a dict... but it is pretty fast anyway,
    doesn't get executed much.
    """
    if cmd_input is None:
        bu.refresh_article()
        print("[ser : del : correct title : rename title : tab : date : freq]")
        print("[re-freq : r : single : random : shuffle : autist : `,` : help]")
        prompt = "[>] URL or song Number /quit - 'q'/ [>]: "
        cmd_input = _root_prompt(prompt)
    to_pass = None
    if cmd_input == "ser":
        search_table()
    elif cmd_input == "del":
        delete_song()
    elif cmd_input == "correct title":
        correct_title(bu)
    elif cmd_input == "rename title":
        rename_title(bu)
        correct_title(bu)
    elif cmd_input == "redownload":
        redownload_song(bu)
    elif cmd_input == "tab":
        bu.show_article()
    elif cmd_input == "date":
        bu.show_article_by_date()
    elif cmd_input == "freq":
        bu.show_article_by_watched()
    elif cmd_input == "re-freq":
        bu.show_article_by_least_watched()
    elif cmd_input == "help":
        command_help()
    else:
        try:
            if cmd_input == "r":
                replay(bu=bu)
            elif cmd_input == "single":
                single_play(bu)
            elif cmd_input == "random":
                to_pass = play_random(bu=bu)
            elif cmd_input == "random --force":
                play_random_force(bu=bu)
            elif cmd_input == "shuffle":
                shuffle(bu)
            elif cmd_input == "by_date":
                play_from_newest(bu)
            elif "," in cmd_input:
                play_manual_playlist(bu, cmd_input)
            elif "autist" in cmd_input[: len("autist")]:
                play_autist(bu, cmd_input)
            else:
                init_player(bu, cmd_input)
        except DownloadError:
            print(f"cent lpay this: {bu.song['title']}... fuuuuU!")
            print("\nGoing further down the road...")
            return None
    return to_pass


def main_loop() -> None:
    """Main loop to handle user input and commands."""
    try:
        bu = ui_first.BaseInterface()
        bu.show_article()
        cmd_input = None
        while True:
            cmd_input = decision_tree(bu, cmd_input)
    except Exception as e:
        print(e)
        input("\n\nif you do anything this will close...")


if __name__ == "__main__":
    main_loop()
