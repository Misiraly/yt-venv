import pandas as pd

import lib_sorter as ls
from modules import search_text as st


def del_a_song():
    """
    Asks for an index corresponding to a song from the library, and makes
    sure the user really wants to delete it (as it is final).
    """
    df = ls.pull_csv_as_df()
    cmd_input = input("Song to delete (via index): ")
    if not cmd_input.isnumeric():
        print(f"[ERROR] wrong index ({cmd_input}), use only integers.")
        return
    if int(cmd_input) not in df.index:
        print(f"[ERROR] index ({cmd_input}) out of bounds.")
        return
    row_index = int(cmd_input)
    title = df.iloc[row_index]["title"]
    print("Are you sure to delete the song: ")
    print(f"> {title}")
    make_sure = input("? [y/N]: ")
    if make_sure in {"y", "Y"}:
        ls.del_from_csv(row_index)
        print(f"[INFO] deleted song: {title}")
    else:
        print("[INFO] deletion stopped.")


def sorted_by_word(s_word: str, lib: pd.DataFrame, cutoff: int = 5):
    """
    s_word :: the string to search for.
    lib :: a dataframe that contains the titles (search pool)
    cutoff :: number matches to display
    """
    df = lib
    df["dis"] = lib.apply(
        lambda row: st.token_distance_list(s_word, row["title"]), axis=1
    )
    if cutoff > len(df.index):
        print(
            f"[WARNING] Cutoff value ({cutoff}) larger than library length,"
            + "defaulting to 5"
        )
        cutoff = 5
    sdf = st.qs_df(df, "dis", st.abc_leq, cutoff=cutoff)
    return sdf


def find_options(cmd_input):
    op_STR = " --cutoff "
    if op_STR in cmd_input:
        return tuple(cmd_input.split(op_STR))
    return cmd_input, 5


def ser_lib(cmd_input=None):
    """
    Asks for a string input and searches the library for the closest
    matching titles.
    """
    lib = ls.pull_csv_as_df()
    if cmd_input is None:
        cmd_input = input("Search [optional: --cutoff {int}]: ")
    s_word, cutoff = find_options(cmd_input)
    s_lib = st.sorted_by_word(s_word, "title", lib, int(cutoff))
    print(s_lib[["title"]])
