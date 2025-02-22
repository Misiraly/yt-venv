import os

import numpy as np
from vlc import MediaPlayer
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

import constant_values as cv
import lib_sorter as ls
import ui_first
from modules import search_text as st

EXIT_CHARS = {"q", "exit"}
YES_CHARS = {"y", "Y"}

LIBRARY = "library"
EXT = "ogg"


def _root_prompt(prompt):
    cmd_input = input(prompt)
    if cmd_input.lower() in EXIT_CHARS:
        exit()
    return cmd_input


def not_sure():
    return _root_prompt("Are you sure? [y/N]: ") not in YES_CHARS


def article_decorator(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        kwargs["bu"].show_article()
        kwargs["bu"].print_closer()

    return wrapper


def divide_decorator(func):
    def wrapper(*args, **kwargs):
        print("-" * cv.SCR_L)
        func(*args, **kwargs)
        print("-" * cv.SCR_L)

    return wrapper


def check_title_fix(title, url, s_title):
    if title == "":
        print()
        print("Warning! after renaming the title, we got an empty string!")
        print(s_title)
        print(url)
        new_name = input("Filename to use (if empty, a hash from url will be used): ")
        title = new_name
        if new_name == "":
            title = ls.correct_title(url)
    return title


def playTheSong(url=None):
    """
    Play a video from a given url, and return it as as an object with some
    info about the video.
    """
    ydl_opts = {"format": "bestaudio", "no_check_certificate": True}
    with YoutubeDL(ydl_opts) as ydl:
        song_info = ydl.extract_info(url, download=False)
    media = MediaPlayer(song_info["url"], ":no-video")
    return song_info, media


def playExisting(bu):
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


def playNonExistant(url):
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
    """
    Initiate the playing, and add additional info to the database if needed.
    """
    media, song = playExisting(bu)
    post_vars = ui_first.cli_gui(song["title"], song["duration"], media, isplaylist)
    if post_vars["watched"]:
        ls.increase_watched(song["title"])
    return post_vars["breaker"]


def play_on_list(bu, cmd_input):
    """
    Plays a song that is tracked by our library.
    """
    cmd_num = int(cmd_input)
    if cmd_num not in bu.table.index:
        print("[TRY AGAIN], number not on list")
    else:
        bu.song = bu.table.iloc[cmd_num].copy(deep=True)
        play_add_Song(bu)
        bu.print_closer()
        bu.show_article()


def play_playlist(playlist, bu, info):
    print(info.center(cv.SCR_L, "-"))
    for el in playlist:
        bu.song = bu.table.iloc[el].copy(deep=True)
        title = bu.song["title"]
        print(f"[nepst: {title.lower()}]")
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
    """
    Play a song not yet tracked by our library.
    """
    if "https" not in cmd_input:
        search_table(cmd_input)
    else:
        url = cmd_input
        print(url)
        media, song = playNonExistant(url)
        post_vars = ui_first.cli_gui(
            song["title"], song["duration"], media, isplaylist=False
        )
        if post_vars["watched"]:
            ls.increase_watched(song["title"])
        bu.song = song
        bu.print_closer()
        bu.show_article()


def init_player(bu, cmd_input):
    """
    If we get an integer input, we assume it refers to a song already in our
    library. Otherwise we handle it as a new song that needs to be added to
    the library.
    """
    if cmd_input.isnumeric():
        play_on_list(bu, cmd_input)
    else:
        play_new(bu, cmd_input)


@article_decorator
def play_random_force(bu):
    """
    Plays a random song that is tracked by our library.
    """
    r = np.random.randint(0, len(bu.table.index))
    bu.song = bu.table.iloc[r].copy(deep=True)
    title = bu.song["title"]
    print(f"\nPlaying a random song... [{title}]\n")
    play_add_Song(bu, isplaylist=True)
    # bu.print_closer()
    # bu.show_article()


# @article_decorator
def play_random(bu):
    """
    Plays a song that is tracked by our library.
    """
    while True:
        rand_choice = np.random.choice(
            len(bu.table.index), 5, replace=False
        )  # TODO: non-hard-coded number of choices?
        songs = bu.table.iloc[rand_choice].copy(deep=True)
        titles = songs[["title"]]
        print(titles)
        playit = _root_prompt(f"\n>>Play first song on the list?[y/N/r]> ")
        if playit.lower() in {"r", "random"}:
            continue
        if playit in YES_CHARS:
            playit = str(songs.index[0])
            print(f"\nPlaying a random song... [{songs.iloc[0]["title"]}]\n")
        break
    return playit


@article_decorator
def replay(bu):
    """
    Replays the song saved in the `BaseInterface` object (bu). If it wasn't
    added to the library yet, it means it will be added.
    """
    play_add_Song(bu)
    # bu.print_closer()
    # bu.show_article()


def shuffle(bu):
    playlist = np.copy(bu.table.index.values)
    np.random.shuffle(playlist)
    play_playlist(playlist, bu, "SHUFFLE")


def play_from_newest(bu):
    df = bu.table.sort_values(by="add_date", ascending=False)
    playlist = np.copy(df.index.values)
    info = "PLAYING BY DATE JOE ROGAN PODCAST BY NIGHT ALL DAY"
    play_playlist(playlist, bu, info)


def play_autist(bu, cmd_input):
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
            print()
            print("[WARNING] Faulty element within the list!")
            print(f"Element in question: `{song_no}`")
            print()
    play_playlist(playlist, bu, "MY PLAYLIST. FUCK OFF WE ARE FULL.")


def find_options(cmd_input):
    op_STR = " --cutoff "
    if op_STR in cmd_input:
        return tuple(cmd_input.split(op_STR))
    return cmd_input, 5


@divide_decorator
def search_table(cmd_input=None):
    """
    Asks for a string input and searches the library for the closest
    matching titles.
    """
    lib = ls.pull_csv_as_df()
    if cmd_input is None:
        cmd_input = _root_prompt("Search [optional: --cutoff {int}]: ")
    s_word, cutoff = find_options(cmd_input)
    s_lib = st.sorted_by_word(s_word, "title", lib, int(cutoff))
    print(s_lib[["title"]])


@divide_decorator
def delete_song():
    """
    Asks for an index corresponding to a song from the library, and makes
    sure the user really wants to delete it (as it is final).
    """
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
    if make_sure in {"y", "Y"}:
        ls.del_from_csv(row_index)
        if song["path"] != cv.NO_PATH:
            os.remove(song["path"])
        print(f"[INFO] deleted song: {title}")
    else:
        print("[INFO] deletion stopped.")


def single_play(bu):
    """
    Plays a song but doesn't add it to the list of songs. However it is
    recorded in the `BaseInterface` object (bu), thus will be tracked after
    replay.
    """

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
    """
    Uses the `correct_title()` function from `lib_sorter`. Makes sure
    the user corrects the title it actually wants to correct as it is final.
    """
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
    """
    Rename a title specified by index. Make sure the user corrects the title it
    actually wants to correct as it is final.
    """
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
                new_title = f"__DEFAULT_{str(np.random.randint(0,1000))}"
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
    Decides what to execute given an input from the terminal.
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


def main_loop():
    bu = ui_first.BaseInterface()
    bu.show_article()
    cmd_input = None
    while True:
        cmd_input = decision_tree(bu, cmd_input)


if __name__ == "__main__":
    main_loop()
