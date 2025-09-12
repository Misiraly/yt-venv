import os
import sys

import numpy as np

os.environ["VLC_VERBOSE"] = "-1"
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
NAY_CHARS = {"n", "N"}
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


def title_warning(msg, new_name, old_title):
    print(f"\nWarning! {msg}")
    print("old name:", old_title)
    print("new name:", new_name)


def force_simple_name(title, url) -> str:
    problematic = False
    title_for_path = ls.correct_title(title)
    if len(title) < 5:
        problematic = True
        title_for_path = title_for_path + url
    if os.path.exists(f"{LIBRARY}/{title_for_path}.{EXT}"):
        problematic = True
        title_for_path = title_for_path + "x"
    return title_for_path, problematic


def title_string_sense(title: str, check_path: bool) -> str:
    """Check and fix the title if it already exists or is empty."""
    new_name = title
    filename_prompt = "New filename to use:"
    print("checking path...")
    if check_path and os.path.exists(f"{LIBRARY}/{new_name}.{EXT}"):
        title_warning("This title already exists!", new_name, title)
        new_name = input(filename_prompt)
    if 0 < len(new_name) < cv.TITLE_MIN:
        title_warning("The title is VERY SHORT!", new_name, title)
        answer = input("Do you want to rename? [Y/n]: ")
        if answer not in NAY_CHARS:
            new_name = input(filename_prompt)
    if new_name == "":
        title_warning("The title string is EMPTY!", new_name, title)
        new_name = input(filename_prompt)
    print(
        "-",
        new_name,
        "-",
        title,
        "-",
    )
    if new_name == title:
        return new_name
    return title_string_sense(new_name, check_path)


def playTheSong(url: str):
    """Play the song from the given URL."""
    ydl_opts = {
        "format": "bestaudio",
        "no_check_certificate": True,
        "abort_on_unavailable_fragments": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        song_info = ydl.extract_info(url, download=False)
    media = MediaPlayer(song_info["url"], ":no-video")
    return song_info, media


def playExisting(bu):
    """Play an existing song from the library."""
    song = dict(bu.song)
    extract = song["duration"] == cv.NO_DURATION
    download = not os.path.exists(song["path"])
    if download:
        print(f"Did not find file at: {song['path']} for song {song["title"]}")
        title_for_path = ls.correct_title(song["title"])
        title_for_path = title_string_sense(title_for_path, check_path=True)
        path = f"{LIBRARY}/{title_for_path}.{EXT}"
    else:
        path = song["path"]
    ydl_opts = {
        "extract_audio": True,
        "format": "bestaudio",
        "no_check_certificate": True,
        "outtmpl": path,
        "abort_on_unavailable_fragments": True,
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


def remove_temporary_file():
    for filename in os.listdir(LIBRARY):
        if filename.startswith(f"{cv.TEMPORARY}.{EXT}"):
            file_path = os.path.join(LIBRARY, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Removed: {file_path}")


def tryDownloadFiveTimes(ydl_opts, videos, path):
    full_list = [(video, 0) for video in videos]
    retry = []
    problematics = []
    uids = []
    failed = []
    timeline = []
    while full_list:
        with YoutubeDL(ydl_opts) as ydl:
            for idx, element in enumerate(full_list, start=1):
                video = element[0]
                try:
                    video_url = f"https://www.youtube.com/watch?v={video['id']}"
                    print(f"Downloading video {idx}: {video.get('title', 'N/A')}")
                    ydl.download([video_url])
                    title_for_path, problematic = force_simple_name(
                        video["title"], video_url
                    )
                    if problematic:
                        problematics.append(video["title"])
                    n_path = f"{LIBRARY}/{title_for_path}.{EXT}"
                    song = {
                        "title": video["title"],
                        "duration": video["duration"],
                        "path": n_path,
                        "url": video_url,
                    }
                    uid = ls.song_to_table_csv(song)
                    uids.append(uid)
                    os.rename(path, n_path)
                    print(f"File saved to {n_path}")
                except DownloadError:
                    remove_temporary_file()
                    trial = (element[0], element[1] + 1)
                    timeline.append(trial)
                    if trial[1] < 5:
                        retry.append(trial)
                    else:
                        failed.append(video.get("title", "N/A"))
        full_list = retry
        retry = []
        timeline.append(('',999))
    print("Failed to download these songs after 5 attempts: ")
    for el in failed:
        print(el)
    print()
    return problematics, uids


def downloadPlaylist(playlist_url: str):
    """Download full playlist."""
    ydl_extract_opts = {
        "quiet": True,
        "extract_flat": True,  # Only get metadata, not media
    }

    print("\nExtracting playlist information...")
    with YoutubeDL(ydl_extract_opts) as ydl:
        playlist_dict = ydl.extract_info(playlist_url, download=False)
        playlist_name = playlist_dict.get("title", "N/A")
        videos = playlist_dict.get("entries", [])
    print(f"Attempting to download {playlist_name}")

    path = f"{LIBRARY}/{cv.TEMPORARY}.{EXT}"
    ydl_opts = {
        "extract_audio": True,
        "format": "bestaudio",
        "no_check_certificate": True,
        "outtmpl": path,
        "abort_on_unavailable_fragments": True,
    }
    problematics, uids = tryDownloadFiveTimes(ydl_opts, videos, path)
    if problematics:
        print(
            "There was a problem finding a suitable filename for the following titles: "
        )
        for el in problematics:
            print(el)
    print("Creating new playlist with new songs...")
    ls.manipulate_playlist_uids(playlist_name, uids, "create")


def playNonExistent(url: str):
    """Play a song that is not in the library."""
    song = {}
    path = f"{LIBRARY}/{cv.TEMPORARY}.{EXT}"
    ydl_opts = {
        "extract_audio": True,
        "format": "bestaudio",
        "no_check_certificate": True,
        "outtmpl": path,
        "abort_on_unavailable_fragments": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        song_info = ydl.extract_info(url, download=True)
    title_for_path = ls.correct_title(song_info["title"])
    title_for_path = title_string_sense(title_for_path, check_path=True)
    n_path = f"{LIBRARY}/{title_for_path}.{EXT}"
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
            remove_temporary_file()
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
            remove_temporary_file()
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
    elif "playlist" in cmd_input:
        print("\nThis action will download a whole playlist.")
        if not_sure():
            return
        downloadPlaylist(cmd_input)
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
    playlist = ls.clean_playlist_input(cmd_input)
    play_playlist(playlist, bu, "MY PLAYLIST. FUCK OFF WE ARE FULL.")


def retrieve_command(text):
    if "--" in text.split(" ")[-1]:
        cmd = text.split(" ")[-1].replace("--", "")
        pos = text.index("--")
        name = text[:pos].strip()
        return name, cmd
    return text, None


def playlist_loop(bu):
    while True:
        yd, index_map = bu.display_playlists()
        print("| Choose playlist (index/name) to play, `--show`  |")
        print("| `--create`, `--delete`, `--add`, or `--remove`  |")
        key = input("[>] ")
        cur_playlist = []
        key, is_command = retrieve_command(key)
        if key.lower() in EXIT_CHARS.union({""}):
            break
        if key in yd:
            name = key
            cur_playlist = yd[key]
        elif key in index_map:
            name = index_map[key]
            cur_playlist = yd[name]
        else:
            print("\nNo such playlist.")
        if is_command in ["create", "delete", "add", "remove"]:
            info = is_command + " with" if is_command == "create" else is_command
            if is_command != "delete":
                to_add = input(f"Song indices to {info}> ")
            new_name = None
            if is_command == "rename":
                new_name = input(f"New name for the playlist `{name}` > ")
            if not_sure():
                print("Aborting operation.")
                continue
            ls.manipulate_playlist(name, to_add, is_command, new_name=new_name)
            cur_playlist = []
        elif cur_playlist:
            df = ls.retrieve_single_pl(cur_playlist)
            if is_command == "show":
                print(f"\nPLAYLIST: {name}")
                print(df["title"].to_string())
            else:
                ids = df.index
                play_playlist(ids, bu, f"Playing the beautiful {name} collection.")
                break


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
    print("! This will also remove the song from all playlists.")
    if song["path"] != cv.NO_PATH:
        print("! This will also delete the file: ")
        print(f"! > {os.path.abspath(song['path'])}")
    make_sure = _root_prompt("? [y/N]: ")
    if make_sure in YES_CHARS:
        ls.del_from_csv(row_index)
        ls.manipulate_playlist("ALL", str(row_index), "remove_from_all")
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
        old_title = song["title"]
        print(f"> {old_title}")
        if not_sure():
            return
        else:
            title = title_string_sense(
                ls.correct_title(song["title"]), check_path=False
            )
            ls.add_attribute(song["title"], title, "title")
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
        old_title = song["title"]
        print(f"> {old_title}")
        if not_sure():
            return
        else:
            song = bu.table.iloc[cmd_num].copy(deep=True)
            new_title = _root_prompt("New title >")
            new_title = title_string_sense(new_title, check_path=False)
            ls.add_attribute(song["title"], new_title, "title")
            bu.show_article()
    else:
        print("Not an integer, renaming aborted.")


def command_help():
    print("Command list: ")
    print("  - ser :: search for song")
    print("  - del :: delete a song")
    print("  - correct title :: remove unusual characters from title")
    print("  - rename title :: rename title")
    print("  - redownload :: redownload song")
    print("  - tab :: print the list of songs")
    print("  - date :: print songs are by date, descending")
    print("  - freq :: print songs arranged by popularity, descending")
    print("  - re-freq :: print songs arranged by popularity, ascending")
    print("  - playlist :: show playlist actions")
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
        print(
            "[ ser : del : correct title : rename title : redownload : tab : date : playlist]"
        )
        print("[freq : re-freq : r : single : random : shuffle : autist : `,` : help]")
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
    elif cmd_input == "playlist":
        playlist_loop(bu)
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
            remove_temporary_file()
            print(f"cent lpay this: {bu.song['title']}... fuuuuU!")
            print("\nGoing further down the road...")
            return None
    return to_pass


def core() -> None:
    bu = ui_first.BaseInterface()
    bu.show_article()
    cmd_input = None
    while True:
        cmd_input = decision_tree(bu, cmd_input)


def main() -> None:
    """Main loop to handle user input and commands."""
    if len(sys.argv) > 1:
        try:
            core()
        except Exception as e:
            print("~ " * 40)
            print(sys.argv[1])
            print(e)
            input("\n\nif you do anything this will close...")
    else:
        core()


if __name__ == "__main__":
    main()
