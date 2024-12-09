import numpy as np
import vlc
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

import lib_sorter as ls
import side_functions as sf
import ui_first

EXIT_CHARS = {"q", "exit"}
YES_CHARS = {"y", "Y"}

COMMAND_EXECUTABLES = {}


def not_sure():
    return input("Are you sure? [y/N]: ") not in YES_CHARS


def article_decorator(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        kwargs['bu'].show_article()
        kwargs['bu'].print_closer()
    return wrapper


def divider():
    """
    Use it to visually divide blocks on the terminal.
    """
    print("-" * 80)


def divide_decorator(func):
    def wrapper(*args, **kwargs):
        divider()
        func(*args, **kwargs)
        divider()
    return wrapper


def playTheSong(url):
    """
    Play a video from a given url, and return it as as an object with some
    info about the video.
    """

    ydl_opts = {"format": "bestaudio", "no_check_certificate": True}
    with YoutubeDL(ydl_opts) as ydl:
        song_info = ydl.extract_info(url, download=False)
    media = vlc.MediaPlayer(song_info["url"], ":no-video")
    return song_info, media


def play_on_list(cmd_input, bu):
    """
    Plays a song that is tracked by our library.
    """
    cmd_num = int(cmd_input)
    if cmd_num not in bu.table.index:
        print("[TRY AGAIN], number not on list")
    else:
        bu.song = bu.table.iloc[cmd_num]
        song_info, media = playTheSong(bu.song["url"])
        ui_first.cli_gui(bu.song["title"], song_info["duration"], media)
        bu.print_closer()
        bu.show_article()


def play_playlist(playlist, bu, info):
    print(info.center(80, "-"))
    for el in playlist:
        bu.song = bu.table.iloc[el]
        title = bu.song["title"]
        print(f"[nepst: {title.lower()}]")
        # has to handle it here otherwise the playlist breaks
        try:
            song_info, media = playTheSong(bu.song["url"])
        except DownloadError:
            print(f"\ncant play this fucking song: {title}!")
            print("Error in the pleilist... going further!!...")
            continue
        breaker = ui_first.cli_gui(
            bu.song["title"], song_info["duration"], media, isplaylist=True
        )
        bu.print_closer()
        if breaker == "x":
            break
    print("\nthe pleilist... it is so over...\n")
    bu.show_article()


# TODO: ALMOS SAME AS ABOVE!
def autist_shuffle(song_no, bu):
    print("AUTIST SHUFFLE".center(80, "-"))
    bu.song = bu.table.iloc[song_no]
    title = bu.song["title"]
    print(f"[run: {title.lower()}]")
    tries = 0
    while True:
        # has to handle it here otherwise the playlist breaks
        try:
            song_info, media = playTheSong(bu.song["url"])
        except DownloadError:
            print(f"\ncant play this fucking song: {title}!")
            print("Error in the autist pleilist... !!...")
            tries += 1
            if tries > 2:
                print("song gives error 3 times, it's over".center(80,"*"))
                break
            continue
        breaker = ui_first.cli_gui(
            bu.song["title"], song_info["duration"], media, isplaylist=True
        )
        bu.print_closer()
        if breaker == "x":
            break
    print("\nthe westphalen... its over...\n")



def play_new(cmd_input, bu):
    """
    Play a song not yet tracked by our library.
    """
    if "https" not in cmd_input:
        search_table(cmd_input)
    else:
        url = cmd_input
        song_info, media = playTheSong(url)
        v_title = song_info["title"]
        v_duration = song_info["duration"]
        bu.song = {"title": v_title, "url": url, "duration": v_duration}
        ui_first.cli_gui(v_title, v_duration, media)
        ls.write_table_to_csv(v_title, url, ui_first.formatted_time(v_duration))
        bu.print_closer()
        bu.show_article()


def init_player(cmd_input, bu):
    """
    If we get an integer input, we assume it refers to a song already in our
    library. Otherwise we handle it as a new song that needs to be added to
    the library.
    """
    if cmd_input.isnumeric():
        play_on_list(cmd_input, bu)
    else:
        play_new(cmd_input, bu)


@article_decorator
def play_random_force(bu):
    """
    Plays a random song that is tracked by our library.
    """
    r = np.random.randint(0, len(bu.table.index))
    bu.song = bu.table.iloc[r]
    title = bu.song["title"]
    print(f"\nPlaying a random song... [{title}]\n")
    song_info, media = playTheSong(bu.song["url"])
    ui_first.cli_gui(bu.song["title"], song_info["duration"], media)
    # bu.print_closer()
    # bu.show_article()


# @article_decorator
def play_random(bu):
    """
    Plays a song that is tracked by our library.
    """
    while True:
        rand_choice = np.random.choice(len(bu.table.index), 5) # TODO: non-hard-coded number of choices?
        songs = bu.table.iloc[rand_choice]
        titles = songs[["title"]]
        print(titles)
        playit = input(f"\n>>Play first song on the list?[y/N/r]> ")
        if playit.lower() in {"r", "random"}:
            continue
        if playit in YES_CHARS:
            playit = str(songs.index[0])
            print(f"\nPlaying a random song... [{songs.iloc[0]["title"]}]\n")
        break
    init_player(playit, bu)


@article_decorator
def replay(bu):
    """
    Replays the song saved in the `BaseInterface` object (bu). If it wasn't
    added to the library yet, it means it will be added.
    """
    song_info, media = playTheSong(bu.song["url"])
    ui_first.cli_gui(bu.song["title"], song_info["duration"], media)
    # bu.print_closer()
    # bu.show_article()


def shuffle(bu):
    playlist = np.copy(bu.table.index.values)
    np.random.shuffle(playlist)
    play_playlist(playlist, bu, "SHUFFLE")


# TODO: ALMOST THE SAME AS ABOVE!!!
def play_from_newest(bu):
    df = bu.table.sort_values(by="add_date", ascending=False)
    playlist = np.copy(df.index.values)
    info = "PLAYING BY DATE JOE ROGAN PODCAST BY NIGHT ALL DAY"
    play_playlist(playlist, bu, info)


# TODO: ALMOST THE SAME AS ABOVE!!!
def play_autist(bu, cmd_input):
    song_no = cmd_input[7:]  # TODO length constant???
    if song_no.isnumeric():
        autist_shuffle(int(song_no), bu)
    else:
        print("\n")
        print(f"Parsed value \"{song_no}\" is not numeric!".center(80, "*"))
        print("\n")


def play_manual_playlist(bu, cmd_input):
    songs = cmd_input.replace(" ", "").split(",")
    playlist = []
    for song_no in songs:
        if song_no.isnumeric() and int(song_no) in bu.table.index.values:
            playlist.append(int(song_no))
    play_playlist(playlist, bu, "MY PLAYLIST. FUCK OFF WE ARE FULL.")


@divide_decorator
def search_table(cmd_input=None):
    sf.ser_lib(cmd_input)


@divide_decorator
def delete_song():
    sf.del_a_song()


def single_play(bu):
    """
    Plays a song but doesn't add it to the list of songs. However it is
    recorded in the `BaseInterface` object (bu), thus will be tracked after
    replay.
    """

    cmd_input = input("[>] song URL [played only once]: ")
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
        }
        ui_first.cli_gui(v_title, v_duration, media)
        bu.print_closer()
        bu.show_article()


def correct_title(bu):
    """
    Uses the `correct_title()` function from `lib_sorter`. Makes sure
    the user corrects the title it actually wants to correct as it is final.
    """
    cmd_input = input("[>] index of title to correct: ")
    if cmd_input.isnumeric():
        cmd_num = int(cmd_input)
        if cmd_num not in bu.table.index:
            print("[ERROR], number not on list")
        print("Song to be corrected: ")
        song = bu.table.iloc[cmd_num]
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
    cmd_input = input("[>] index of title to rename: ")
    if cmd_input.isnumeric():
        cmd_num = int(cmd_input)
        if cmd_num not in bu.table.index:
            print("[ERROR], number not on list")
        print("Song to be renamed: ")
        song = bu.table.iloc[cmd_num]
        ole_title = song["title"]
        print(f"> {ole_title}")
        if not_sure():
            return
        else:
            song = bu.table.iloc[cmd_num]
            new_title = input("New title >")
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
    print("  - date :: print a list where the songs are arranged by date, descending")
    print("  - r :: replay a song")
    print("  - single :: play a url without adding it to the library")
    print("  - help :: prints this list")
    print("  - random :: play a random song. Use '--force' to play it automatically")
    print("  - shuffle :: shuffles all the songs into one playlist, plays it")
    print("  - by_date :: play the songs by date of addition to the list")
    print("  - autist :: play the same song over and over again")


def decision_tree(bu):
    """
    Decides what to execute given an input from the terminal.
    """
    print("[ser : del : correct title : rename title : tab : date]")
    print("[r : single : random : shuffle : autist : `,` : help]")
    prompt = "[>] URL or song Number /quit - 'q'/ [>]: "
    cmd_input = input(prompt)
    if cmd_input in EXIT_CHARS:
        exit()
    elif cmd_input == "ser":
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
    else:
        try:
            if cmd_input == "r":
                replay(bu=bu)
            elif cmd_input == "single":
                single_play(bu)
            elif cmd_input == "help":
                command_help()
            elif cmd_input == "random":
                play_random(bu=bu)
            elif cmd_input == "random --force":
                play_random_force(bu=bu)
            elif cmd_input == "shuffle":
                shuffle(bu)
            elif cmd_input == "by_date":
                play_from_newest(bu)
            elif "," in cmd_input:
                play_manual_playlist(bu, cmd_input)            
            elif "autist" in cmd_input[:len("autist")]:
                play_autist(bu, cmd_input)
            else:
                init_player(cmd_input, bu)
        except DownloadError:
            print(f"cent lpay this: {bu.song['title']}... fuuuuU!")
            print("\nGoing further down the road...")
            return


def main_loop():
    bu = ui_first.BaseInterface()
    bu.show_article()
    while True:
        decision_tree(bu)


if __name__ == "__main__":
    main_loop()
