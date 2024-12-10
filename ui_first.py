import msvcrt
import time
from multiprocessing import Process, Value

import lib_sorter as ls
from modules import formatter
import constant_values as cv

STATUS_ICON = {
    "p": "(||)",
    "s": "(■) ",
    "l": "(►) ",
    "r": "(►) ",
    "status_l": 4,
    "q": "(■) ",
    "x": "(■)",
}
STATUS_CHAR = {"p", "s", "l", "r", "q", "n", "x"}
EXIT_CHAR = {"q", "x"}


def count(seconds, v: Value):
    """Count down and pass exit code to inter-process variable.

    Parameters
    ----------
    seconds : int
        number of seconds to count down

    v: Value :
        inter-process variable carrying the state of playing
    """
    i = seconds
    while v.value not in EXIT_CHAR and i > 0:
        time.sleep(0.125)
        if v.value != "b":
            i -= 0.125
    key = "q"
    v.value = key


def check_end(seconds, v: Value, t_v: Value):
    """

    Parameters
    ----------
    seconds :

    v: Value :

    t_v: Value :

    """
    while v.value not in EXIT_CHAR and t_v.value <= seconds - 1:
        time.sleep(0.125)
    key = "q" if v.value != "x" else "x"
    v.value = key


def ask(v: Value):
    """Check for key push event and pass it to the inter-process variable.

    Parameters
    ----------
    v: Value :
        inter-process variable


    Returns
    -------

    """
    key = v.value
    while key not in EXIT_CHAR:
        # if we don't check for this below, then the Process actually DOESN'T
        # STOP or FUCKS UP or smth even after TERMINATING IT. Cuh
        if msvcrt.kbhit():
            try:
                key = msvcrt.getch().decode("ASCII").lower()
            except:
                # non-ascii char inputted
                pass
            v.value = key
        time.sleep(0.05)


class ProgressBar:
    """A class to showcase and modify a progress bar that keeps track of
    time.

    Parameters
    ----------

    Returns
    -------

    """

    def __init__(self, seconds, media):
        self.scr_l = 60
        left_side = ""
        right_side = ""
        self.seconds = seconds
        self.is_video_long = seconds > 3599
        self.time_bar = formatted_time(0)
        self.full_time = formatted_time(seconds, self.is_video_long)
        subtract = (
            len(left_side)
            + STATUS_ICON["status_l"]
            + 1
            + len(right_side)
            + len(self.time_bar)
            + len(self.full_time)
        )
        self.bar_l = self.scr_l - subtract

        self.media = media
        self.start_time = 0
        self.c_time = 0
        assert self.seconds > 0.99, f"Video time too short: {self.seconds}"
        self.key = "l"

    def print_bar(self, key):
        """Print a progress bar based on the elapsed time.

        Parameters
        ----------
        key :
            the last key pressed by the user


        Returns
        -------

        """
        _c_time = self.media.get_time() / 1000
        ratio = _c_time / self.seconds
        if ratio > 1:
            ratio = 1
        bar = "=" * (round((self.bar_l - 1) * ratio)) + "v"
        neg_bar = "-" * (self.bar_l - len(bar))
        if key in STATUS_CHAR and key not in {"n", "np"}:
            self.key = key
        self.time_bar = formatted_time(_c_time)
        progress = STATUS_ICON[self.key] + " " + self.time_bar + bar + neg_bar
        progress = progress + self.full_time
        print(progress, end="\r")


def get_seconds(formatted_input: str = 0):
    """Inverse of formatted_time (below), not actually used.

    Parameters
    ----------
    formatted_input: str :
         (Default value = 0)

    Returns
    -------

    """
    if formatted_input == 0:
        print("[INFO] This has no length.")
        return 0
    _temp = formatted_input.split(":")
    return int(_temp[0]) * 3600 + int(_temp[1]) * 60 + int(_temp[2])


def formatted_time(seconds, is_long=False):
    """eg 123 -> 02:03, 3673 -> 01:01:13

    Parameters
    ----------
    seconds : integer
        whether seconds are more than an hour

    is_long : boolean
         (Default value = False)

    Returns
    -------

    """
    sec = int(seconds)
    hour = str(sec // 3600)
    hour = "0" * (2 - len(hour)) + hour
    minute = str((sec % 3600) // 60)
    minute = "0" * (2 - len(minute)) + minute
    sec = str(sec % 60)
    sec = "0" * (2 - len(sec)) + sec
    if not is_long:
        return f"{minute}:{sec}"
    return f"{hour}:{minute}:{sec}"


def player_info(title, seconds, isplaylist, info_length=60):
    """Prints necessary info about a song.

    Parameters
    ----------
    title :

    seconds :

    info_length :
         (Default value = 60)

    Returns
    -------

    """
    print("-" * info_length)
    title_list = formatter.line_breaker(str(title), info_length - 2)
    for line in title_list:
        print(line.center(info_length))
    print()
    print()
    helper = "[||] - p  [►] - l  [■] - q   Replay - r"
    if isplaylist:
        helper = "[||] - p  [►] - l  [►|] - q   Replay - r  Exit playlist - x"
    print(helper.center(info_length))
    print()


def player_loop(media, v_duration, v: Value, t_v: Value):
    """While media is playing, checks for user input and executes accordingly.

    Parameters
    ----------
    media :

    v_duration :

    v: Value :

    t_v: Value :


    Returns
    -------

    """
    media.play()
    key = v.value
    watched = False
    Bar = ProgressBar(v_duration, media)
    while key not in EXIT_CHAR:
        t_v.value = media.get_time() / 1000
        if t_v.value / v_duration > cv.REL_W_LIMIT or t_v.value > cv.ABS_W_LIMIT:
            watched = True
        if key == "p":
            # pause
            media.pause()
            v.value = "b"
        elif key == "s":
            # stop
            media.stop()
            v.value = "n"
        elif key == "l":
            # play
            media.play()
            v.value = "n"
        elif key == "r":
            # replay
            media.stop()
            media.play()
            v.value = "n"
        Bar.print_bar(key)
        key = v.value
        time.sleep(0.1)
    v.value = "q" if key != "x" else "x"
    return watched


def cli_gui(v_title, v_duration, media, isplaylist):
    """This handles user inputs and graphic output for the song being played.

    Parameters
    ----------
    v_title :

    v_duration :

    media :


    Returns
    -------

    """
    player_info(v_title, v_duration, isplaylist)
    key = "n"
    c_time = 0
    post_vars = {}
    # variable accessible by parallel processes
    v = Value("u", key)
    t_v = Value("f", c_time)
    p_ask = Process(target=ask, args=(v,))
    p_check_end = Process(
        target=check_end,
        args=(
            v_duration,
            v,
            t_v,
        ),
    )
    p_ask.start()
    p_check_end.start()
    post_vars['watched'] = player_loop(media, v_duration, v, t_v)
    p_ask.terminate()
    p_check_end.terminate()
    p_ask.join()
    p_check_end.join()
    media.stop()
    print("\nstoppeth")
    post_vars['breaker'] = v.value
    return post_vars


class BaseInterface:
    """The engine for all the stuff related to the list of songs. Mainly
    concerned about printing info, but retains some song info as well.

    Parameters
    ----------

    Returns
    -------

    """

    page = dict()
    page["header"] = ["\n"] + formatter.abc_rower("  PYTHON MUSIC") + ["\n"]
    page["body"] = list()
    page["prompt"] = ["[>] URL or song Number [>]: "]
    page["closer"] = [
        "\n***     ..bideo.. emth!!!~` щ(`Д´щ;)    ***",
        "-" * cv.SCR_L + "\n",
    ]
    page_width = cv.SCR_L
    song = {
        "title": "dummy",
        "url": "https://www.youtube.com/watch?v=fWh6J5Tg274",
    }
    wspace = " "
    ell = "..."
    nell = "   "
    playlist = list()

    def __init__(self):
        self.table = ls.pull_csv_as_df()

    def print_closer(self):
        """ """
        for entry in self.page["closer"]:
            print(entry)

    def double_table(self):
        """Arranges the library into two columns and returns it as a list."""
        half = len(self.table.index) // 2 + len(self.table.index) % 2
        part_line = self.page_width // 2
        title_l = part_line - len(self.wspace) - len(self.ell)
        tst = ["" for i in range(half)]  # two-side-table :3
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

    def show_article(self):
        """Prints the library as arranged in `self.double_table()`, and assigns
        it to the object.

        Parameters
        ----------

        Returns
        -------

        """
        self.table = ls.pull_csv_as_df()
        self.double_table()
        article = (
            self.page["header"] + self.page["body"]
        )  # + _page["prompt"] + _page["closer"]
        for line in article:
            print(line)

    def show_article_by_date(self):
        """Prints the library arranged from latest and newest based on the date
        they were added to the library. The newest is thus on the bottom.

        Parameters
        ----------

        Returns
        -------

        """
        df = self.table.sort_values(by="add_date")
        print(df.to_string(columns=["title"], max_colwidth=cv.SCR_L - 15))

    def show_article_by_watched(self):
        """Prints the library arranged from latest and newest based on the date
        they were added to the library. The newest is thus on the bottom.

        Parameters
        ----------

        Returns
        -------

        """
        df = self.table.sort_values(by="watched")
        print(df.to_string(columns=["title", "watched"], max_colwidth=cv.SCR_L - 15))
