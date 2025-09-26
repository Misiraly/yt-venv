import time
from msvcrt import getch, kbhit
from multiprocessing import Process, Value

import constant_values as cv
import lib_sorter as ls
from modules import formatter

# Constants
STATUS_ICON = {
    "p": "(||)",
    "s": "(■) ",
    "l": "(►) ",
    "r": "(►) ",
    "q": "(■) ",
    "x": "(■) ",
}
STATUS_L = 4
STATUS_CHAR = {"p", "s", "l", "r", "q", "n", "x"}
EXIT_CHAR = {"q", "x"}


def check_end(seconds: int, v: Value, t_v: Value) -> None:
    """Check if the playback should end based on user input or duration.

    Parameters
    ----------
    seconds : int
        Duration of the media in seconds.
    v : Value
        Inter-process variable for user input.
    t_v : Value
        Inter-process variable for elapsed time.
    """
    while v.value not in EXIT_CHAR and t_v.value <= seconds - 1:
        time.sleep(0.125)
    key = "q" if v.value != "x" else "x"
    v.value = key


def ask(v: Value) -> None:
    """Check for key press events and pass them to the inter-process variable.

    Parameters
    ----------
    v : Value
        Inter-process variable for user input.
    """
    key = v.value
    while key not in EXIT_CHAR:
        # if we don't check for this below, then the Process actually DOESN'T
        # STOP or FUCKS UP or smth even after TERMINATING IT. Cuh
        if kbhit():
            try:
                key = getch().decode("ASCII").lower()
            except UnicodeDecodeError:
                # Non-ASCII character inputted
                pass
            v.value = key
        time.sleep(0.05)


class ProgressBar:
    """A class to manage and display a progress bar for media playback.

    Parameters
    ----------
    seconds : int
        Duration of the media in seconds.
    media : object
        Media object to track playback.
    title : str
        Title of the media.
    isplaylist : bool
        Indicates if the media is part of a playlist.
    """

    def __init__(self, seconds: int, media, title: str, isplaylist: bool) -> None:
        self.scr_l = cv.PLR_L
        self.seconds = seconds
        self.is_video_long = seconds > 3599
        self.time_bar = formatted_time(0, self.is_video_long)
        self.full_time = formatted_time(seconds, self.is_video_long)
        subtract = STATUS_L + 1 + len(self.time_bar) + len(self.full_time)
        self.bar_l = self.scr_l - subtract

        self._print_header(title, isplaylist)

        self.media = media
        self.start_time = 0
        self.c_time = 0
        assert self.seconds > 0.99, f"Video time too short: {self.seconds}"
        self.key = "l"

    def _print_header(self, title: str, isplaylist: bool) -> None:
        """Print the header information for the progress bar."""
        print("-" * self.scr_l)
        title_list = formatter.line_breaker(str(title), self.scr_l - 2)
        for line in title_list:
            print(line.center(self.scr_l))
        print("\n")

        helper1 = "[||] - p  [►] - l  [■] - q   Replay - r"
        if isplaylist:
            helper1 = "[||] - p  [►] - l  [►|] - q   Replay - r  Exit playlist - x"
        helper2 = "[<<] - g" + " " * (len(helper1) - 2 * 9 - 2) + "h - [>>]"
        print(helper1.center(self.scr_l))
        print(helper2.center(self.scr_l))
        print()

    def print_bar(self, key: str) -> None:
        """Print the progress bar based on the elapsed time."""
        _c_time = self.media.get_time() / 1000
        ratio = _c_time / self.seconds
        ratio = min(ratio, 1)
        bar = "=" * (round((self.bar_l - 1) * ratio)) + "v"
        neg_bar = "-" * (self.bar_l - len(bar))
        if key in STATUS_CHAR and key not in {"n", "np"}:
            self.key = key
        self.time_bar = formatted_time(_c_time, self.is_video_long)
        progress = (
            STATUS_ICON[self.key] + " " + self.time_bar + bar + neg_bar + self.full_time
        )
        print(progress, end="\r")


def get_seconds(formatted_input: str = "0") -> int:
    """Inverse of formatted_time (below), actually used, sadly.

    Parameters
    ----------
    formatted_input : str, optional
        Time in formatted string (HH:MM:SS or MM:SS), by default "0"

    Returns
    -------
    int
        Time in seconds.
    """
    if not isinstance(formatted_input, str):
        return formatted_input
    if formatted_input == "0":
        print("[INFO] This has no length.")
        return 0
    _temp = formatted_input.split(":")
    if len(_temp) > 2:
        return int(_temp[0]) * 3600 + int(_temp[1]) * 60 + int(_temp[2])
    return int(_temp[0]) * 60 + int(_temp[1])


def formatted_time(seconds: int, is_long: bool = False) -> str:
    """eg 123 -> 02:03, 3673 -> 01:01:13

    Parameters
    ----------
    seconds : int
        Time in seconds.
    is_long : bool, optional
        Indicates if the time is more than an hour, by default False

    Returns
    -------
    str
        Formatted time string.
    """
    sec = int(seconds)
    hour = str(sec // 3600).zfill(2)
    minute = str((sec % 3600) // 60).zfill(2)
    sec = str(sec % 60).zfill(2)
    if not is_long and seconds < 3599:
        return f"{minute}:{sec}"
    return f"{hour}:{minute}:{sec}"


def player_loop(
    media, v_title: str, v_duration: int, isplaylist: bool, v: Value, t_v: Value
) -> bool:
    """Main loop to handle media playback and user input.

    Parameters
    ----------
    media : Any
        Media object to control playback.
    v_title : str
        Title of the media.
    v_duration : int
        Duration of the media in seconds.
    isplaylist : bool
        Indicates if the media is part of a playlist.
    v : Value
        Inter-process variable for user input.
    t_v : Value
        Inter-process variable for elapsed time.

    Returns
    -------
    bool
        Indicates if the media was watched.
    """
    bar = ProgressBar(v_duration, media, v_title, isplaylist)
    media.get_instance()
    media.play()
    key = v.value
    watched = False
    tenth = v_duration // 10
    time_spent = 0
    incr = cv.INTERVAL_INCR
    jump = 5  # seconds
    while key not in EXIT_CHAR:
        t_v.value = media.get_time() / 1000
        if time_spent / v_duration > cv.REL_W_LIMIT or time_spent > cv.ABS_W_LIMIT:
            watched = True
        if key == "p":
            # pause
            incr = 0
            media.pause()
        elif key == "s":
            # stop
            incr = 0
            media.stop()
        elif key == "l":
            # play
            incr = cv.INTERVAL_INCR
            media.play()
        elif key == "r":
            # replay
            incr = cv.INTERVAL_INCR
            media.stop()
            media.play()
        elif key == "g":
            media.set_time(max(int((t_v.value - jump) * 1000), 0))
        elif key == "h":
            tiem = min(int((t_v.value + jump) * 1000), int(v_duration * 1000))
            media.set_time(tiem)
        elif key.isnumeric():
            media.set_time(int(key) * tenth * 1000)
        bar.print_bar(key)
        key = v.value
        if v.value not in EXIT_CHAR:
            v.value = "n"
        time.sleep(incr)
        time_spent += incr
    v.value = "q" if key != "x" else "x"
    return watched


def cli_gui(v_title: str, v_duration: int, media, isplaylist: bool) -> dict:
    """Handle user inputs and graphic output for the media being played.

    Parameters
    ----------
    v_title : str
        Title of the media.
    v_duration : int
        Duration of the media in seconds.
    media : Any
        Media object to control playback.
    isplaylist : bool
        Indicates if the media is part of a playlist.

    Returns
    -------
    dict
        Dictionary with playback results.
    """
    key = "n"
    c_time = 0
    post_vars = {}
    # variables accessible by parallel processes
    v = Value("u", key)
    t_v = Value("f", c_time)
    p_ask = Process(target=ask, args=(v,))
    p_check_end = Process(target=check_end, args=(v_duration, v, t_v))
    p_ask.start()
    p_check_end.start()
    post_vars["watched"] = player_loop(media, v_title, v_duration, isplaylist, v, t_v)
    p_ask.terminate()
    p_check_end.terminate()
    p_ask.join()
    p_check_end.join()
    media.stop()
    print("\nstoppeth")
    post_vars["breaker"] = v.value
    return post_vars


class BaseInterface:
    """Engine for managing and displaying the list of songs.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """

    page_width = cv.SCR_L
    wspace = " "
    ell = "..."
    playlist = []
    page = {
        "header": ["\n"] + formatter.abc_rower("    PYTHON MUSIC") + ["\n"],
        "body": [],
        "prompt": ["[>] URL or song Number [>]: "],
        "closer": [
            "***     ..bideo.. emth!!!~` щ(`Д´щ;)    ***".replace(" ", "_").center(
                page_width
            ),
        ],
    }

    def __init__(self):
        self.table = ls.pull_csv_as_df()
        self.song = self.table.iloc[0]

    def print_closer(self):
        """ """
        for entry in self.page["closer"]:
            print(entry)

    def double_table(self):
        """Arranges the library into two columns and returns it as a list."""
        half = len(self.table.index) // 2 + len(self.table.index) % 2
        part_line = self.page_width // 2
        title_l = part_line - len(self.wspace) - len(self.ell)
        tst = ["" for i in range(half)]  # two-side-table
        titles = self.table["title"].values.tolist()
        for i, song in enumerate(titles):
            title = song.ljust(title_l)
            if len(title) > title_l:
                title = title[: title_l - 3] + self.ell
            tst[i % half] = (
                tst[i % half]
                + str(i).ljust(3)
                + self.wspace
                + title
                + self.wspace * (1 - (i // half))
            )
        self.page["body"] = tst

    def refresh_article(self):
        self.table = ls.pull_csv_as_df()

    def show_article(self) -> None:
        """Print the library as arranged in `self.double_table()`."""
        self.refresh_article()
        self.double_table()
        article = self.page["header"] + self.page["body"]
        for line in article:
            print(line)

    def show_article_by_date(self) -> None:
        """Print the library arranged by date added, newest at the bottom."""
        df = self.table.sort_values(by="add_date")
        print(df.to_string(columns=["title"], max_colwidth=cv.SCR_L - 15))

    def show_article_by_watched(self) -> None:
        """Print the library arranged by the most listened to songs."""
        df = self.table.sort_values(by="watched")
        print(df.to_string(columns=["title", "watched"], max_colwidth=cv.SCR_L - 15))

    def show_article_by_least_watched(self) -> None:
        """Print the library arranged by the least listened to songs."""
        df = self.table.sort_values(by="watched", ascending=False)
        print(df.to_string(columns=["title", "watched"], max_colwidth=cv.SCR_L - 15))

    def display_playlists(self) -> None:
        yd = ls.read_playlists()
        for line in formatter.abc_rower("Playlists"):
            print(line)
        print()
        index_map = {str(i): key for i, key in enumerate(yd.keys())}
        for si, key in index_map.items():
            print(" -", si, key)
        print()
        return yd, index_map
