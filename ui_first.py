import time
from msvcrt import getch, kbhit
from multiprocessing import Process, Value

import constant_values as cv
import lib_sorter as ls
from modules import formatter

STATUS_ICON = {
    "p": "(||)",
    "s": "(■) ",
    "l": "(►) ",
    "r": "(►) ",
    "q": "(■) ",
    "x": "(■)",
}
STATUS_L = 4
STATUS_CHAR = {"p", "s", "l", "r", "q", "n", "x"}
EXIT_CHAR = {"q", "x"}


def check_end(seconds, v, t_v):
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


def ask(v):
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
        if kbhit():
            try:
                key = getch().decode("ASCII").lower()
            except UnicodeDecodeError:
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

    def __init__(self, seconds, media, title, isplaylist):
        self.scr_l = cv.PLR_L
        scr_l = self.scr_l
        self.seconds = seconds
        self.is_video_long = seconds > 3599
        self.time_bar = formatted_time(0, self.is_video_long)
        self.full_time = formatted_time(seconds, self.is_video_long)
        subtract = STATUS_L + 1 + len(self.time_bar) + len(self.full_time)
        self.bar_l = scr_l - subtract
        bar_l = self.bar_l

        print("-" * scr_l)
        title_list = formatter.line_breaker(str(title), scr_l - 2)
        for line in title_list:
            print(line.center(scr_l))
        print()
        print()
        helper1 = "[||] - p  [►] - l  [■] - q   Replay - r"
        if isplaylist:
            helper1 = "[||] - p  [►] - l  [►|] - q   Replay - r  Exit playlist - x"
        helper2 = "[<<] - g" + " " * (len(helper1) - 2 * 9 - 2) + "h - [>>]"
        print(helper1.center(scr_l))
        print(helper2.center(scr_l))
        # quot = bar_l / 10
        # marks = [int(i * quot) for i in range(10)]
        # marked = "".join(
        #     (str(round(i / quot)) if i in marks else " " for i in range(bar_l))
        # )
        #
        # To demonstrate that I would have been able to define this string in
        # a self-conained formula, I leave this code snippet here:
        #
        # marked = "".join(
        #     [
        #         (
        #             str(int((i + 1) * 10 / bar_l) - 1)
        #             if (int(i * 10 / bar_l) != int((i + 1) * 10 / bar_l))
        #             else " "
        #         )
        #         for i in range(bar_l // 10, bar_l + bar_l // 10)
        #     ]
        # )
        #
        #
        #
        # marked = "".join([str(int((i)*10/bar_l)) if not int((i )% (bar_l / 10)) else " " for i in range(-1, bar_l - 1)])
        print()
        # print(" " * (STATUS_L + 1 + len(self.time_bar)) + marked)

        self.media = media
        self.start_time = 0
        self.c_time = 0
        assert self.seconds > 0.99, f"Video time too short: {self.seconds}"
        self.key = "l"

    def print_bar(self, key):
        """
        Print a progress bar based on the elapsed time.
        """
        _c_time = self.media.get_time() / 1000
        ratio = _c_time / self.seconds
        if ratio > 1:
            ratio = 1
        bar = "=" * (round((self.bar_l - 1) * ratio)) + "v"
        neg_bar = "-" * (self.bar_l - len(bar))
        if key in STATUS_CHAR and key not in {"n", "np"}:
            self.key = key
        self.time_bar = formatted_time(_c_time, self.is_video_long)
        progress = STATUS_ICON[self.key] + " " + self.time_bar + bar + neg_bar
        progress = progress + self.full_time
        print(progress, end="\r")


def get_seconds(formatted_input: str = 0):
    """Inverse of formatted_time (below), actually used, sadly.

    Parameters
    ----------
    formatted_input: str :
         (Default value = 0)

    Returns
    -------

    """
    if not isinstance(formatted_input, str):
        return formatted_input
    if formatted_input == 0:
        print("[INFO] This has no length.")
        return 0
    _temp = formatted_input.split(":")
    if len(_temp) > 2:
        return int(_temp[0]) * 3600 + int(_temp[1]) * 60 + int(_temp[2])
    return int(_temp[0]) * 60 + int(_temp[1])


def formatted_time(seconds, is_long=False):
    """eg 123 -> 02:03, 3673 -> 01:01:13

    Parameters
    ----------
    seconds : integer

    is_long : boolean
         (Default value = False)
        whether seconds are more than an hour

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
    if not is_long and seconds < 3599:
        return f"{minute}:{sec}"
    return f"{hour}:{minute}:{sec}"


def player_loop(media, v_title, v_duration, isplaylist, v, t_v):
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
    bar = ProgressBar(v_duration, media, v_title, isplaylist)
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
            v.value = "b"
        elif key == "s":
            # stop
            incr = 0
            media.stop()
            v.value = "n"
        elif key == "l":
            # play
            incr = cv.INTERVAL_INCR
            media.play()
            v.value = "n"
        elif key == "r":
            # replay
            incr = cv.INTERVAL_INCR
            media.stop()
            media.play()
            v.value = "n"
        elif key == "g":
            media.set_time(max(int((t_v.value - jump) * 1000), 0))
            v.value = "n"
        elif key == "h":
            tiem = min(int(t_v.value + jump) * 1000, int(v_duration * 1000))
            media.set_time(tiem)
            v.value = "n"
        elif key.isnumeric():
            media.set_time(int(key) * tenth * 1000)
            v.value = "n"
        bar.print_bar(key)
        key = v.value
        time.sleep(incr)
        time_spent += incr
    v.value = "q" if key != "x" else "x"
    return watched


def cli_gui(v_title, v_duration, media, isplaylist):
    """Handles user inputs and graphic output for the song being played."""
    key = "n"
    c_time = 0
    post_vars = {}
    # variables accessible by parallel processes
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
    post_vars["watched"] = player_loop(media, v_title, v_duration, isplaylist, v, t_v)  # TODO: media.play() is hidden inside this func, but media.stop() is outside!
    p_ask.terminate()
    p_check_end.terminate()
    p_ask.join()
    p_check_end.join()
    media.stop()
    print("\nstoppeth")
    post_vars["breaker"] = v.value
    return post_vars


class BaseInterface:
    """The engine for all the stuff related to the list of songs. Mainly
    concerned about printing info, but retains some song info as well.

    Parameters
    ----------

    Returns
    -------

    """

    page = {}
    page["header"] = ["\n"] + formatter.abc_rower("    PYTHON MUSIC") + ["\n"]
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
    playlist = []

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

    def show_article(self):
        """
        Prints the library as arranged in `self.double_table()`, and assigns
        it to the object.
        """
        self.table = ls.pull_csv_as_df()
        self.double_table()
        article = (
            self.page["header"] + self.page["body"]
        )  # + _page["prompt"] + _page["closer"]
        for line in article:
            print(line)

    def show_article_by_date(self):
        """
        Prints the library arranged from latest and newest based on the date
        they were added to the library. The newest is thus on the bottom.
        """
        df = self.table.sort_values(by="add_date")
        print(df.to_string(columns=["title"], max_colwidth=cv.SCR_L - 15))

    def show_article_by_watched(self):
        """
        Prints the library arranged from latest and newest based on the date
        they were added to the library. The newest is thus on the bottom.
        """
        df = self.table.sort_values(by="watched")
        print(df.to_string(columns=["title", "watched"], max_colwidth=cv.SCR_L - 15))

    def show_article_by_least_watched(self):
        """
        Prints the library arranged from latest and newest based on the date
        they were added to the library. The newest is thus on the bottom.
        """
        df = self.table.sort_values(by="watched", ascending=False)
        print(df.to_string(columns=["title", "watched"], max_colwidth=cv.SCR_L - 15))
