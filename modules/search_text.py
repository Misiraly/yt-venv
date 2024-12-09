import pandas as pd
from Levenshtein import distance as lev

# from unidecode import unidecode

SEP_CHAR = {
    ";",
    ":",
    "-",
    "+",
    ".",
    "?",
    "!",
    ",",
    "[",
    "]",
    "(",
    ")",
    "{",
    "}",
    "<",
    ">",
    "*",
    "~",
}
IGNORE_CHAR = {"'", '"', "”", "/", "\\", "#", "$", "%", "&", "@", "^"}
REPLACE_CHAR = {
    "á": "a",
    "é": "e",
    "í": "i",
    "ó": "o",
    "ö": "o",
    "ő": "o",
    "ú": "u",
    "ü": "u",
    "ű": "u",
}


def qsp(tosort, leq):
    """
    tosort :: a list of two-entry lists, where the first entry is an index,
    and the second entry is a value to sort by.
    leq :: a function defining a less-than-or-equal relation

    Chooses a pivot element from the list, and assigns all elements less-
    -than-or-equal to a list by its "left" (`l`) and all the elements
    strictly greater to a list by its "right" (`r`). Returns "left" list,
    pivot element (as a list) and the "right" list.
    """
    l, r = [], []
    pivot = tosort[-1]
    l = [el for el in tosort[:-1] if leq(el[1], pivot[1])]
    r = [el for el in tosort if not leq(el[1], pivot[1])]
    return l, [pivot], r


def qs_eng(tosort, leq):
    """
    tosort :: a list of two-entry lists, where the first entry is an index,
    and the second entry is a value to sort by.
    leq :: a function defining a less-than-or-equal relation

    Uses recursion to return a list with indices sorted by values.
    """
    if len(tosort) <= 1:
        return tosort
    l, pivot, r = qsp(tosort, leq)
    l = qs_eng(l, leq)
    r = qs_eng(r, leq)
    return l + pivot + r


def qs_df(df, col, leq, cutoff=5):
    """
    df :: pandas.DataFrame object
    col :: column to sort by
    leq :: a function defining a less-than-or-equal relation for two values,
    ie, leq(a,b) -> True if a <= b etc... reason is that this allows for
    user defined relation.
    cutoff :: the number of elements that we want to return from the `top`
    of the list.

    Applies the quick-sort algorithm to a DataFrame by on one of it's
    columns and based on a user defined less-than-or-equal relation. The
    algorithm actually runs on an array to speed up sorting. DataFrames are
    slower to iterate through and to change rows.
    """
    ilist = df.index.values.tolist()
    dislist = df[col].values.tolist()
    tosort = [[ilist[i], dislist[i]] for i in range(len(ilist))]
    sortlist = qs_eng(tosort, leq)
    ilist = [el[0] for el in sortlist[:cutoff]]
    sdf = df.loc[ilist]
    return sdf


def abc_leq(list_1, list_2):  # == (list_1 <= list_2)
    l = min(len(list_1), len(list_2))
    for i in range(l):
        if list_1[i] == list_2[i]:
            continue
        elif list_1[i] > list_2[i]:
            return False
        else:
            return True
    # this rewards shorter lists
    return True


def tokenize_neighbor(streeng):
    """
    Replaces a list of strings where:
    Replaces characters that usually cannot be understood as part of a word
    with a whitespace
    Replaces quirky characters with empty string as they
    are usually part of a word, just not meaningful in a search...hmm I
    might revisit this...they are not unintelligable for python after all.
    Replaces characters with diacritics with non-diacritic equivalent.
    Splits the string by whitespaces and returns as a list, and concatenates
    a list of neighboring words concatenated (no empty strings allowed)
    ie
    "what are# yoű)dö^ing?"
    -->
    ["what","are","you",doing","whatare","areyou","youdoing"]
    """
    string = streeng.lower()
    for char in SEP_CHAR:
        string = string.replace(char, " ")
    for char in IGNORE_CHAR:
        string = string.replace(char, "")
    for char in REPLACE_CHAR:
        string = string.replace(char, REPLACE_CHAR[char])
    tokens = string.split(" ")
    tokens = [token for token in tokens if token != ""]
    neigh_tokens = [tokens[i] + tokens[i + 1] for i in range(len(tokens) - 1)]
    return tokens + neigh_tokens


def token_distance_list(search_value, text, cutoff=5):
    """
    Calculate the levensthein distance between all the possible pairs of words,
    and all the possible concatenations of neighboring words. Order the
    distances.
    """
    search_tokens = tokenize_neighbor(search_value)
    text_tokens = tokenize_neighbor(text)
    distance_list = []
    for token1 in search_tokens:
        if token1 in text.lower():
            distance_list.append(1)  # very close match
        for token2 in text_tokens:
            distance_list.append(lev(token1, token2))
    distance_list.sort()
    return distance_list


def sorted_by_word(s_word: str, col: str, lib: pd.DataFrame, cutoff: int = 5):
    """
    s_word :: the string to search for.
    col :: column name of the dataframe based on which the sorting applies
    lib :: a dataframe that contains the titles (search pool)
    cutoff :: number matches to display
    """
    df = lib
    df["dis"] = lib.apply(
        lambda row: token_distance_list(s_word, row[col]), axis=1
    )
    if cutoff > len(df.index):
        print(
            f"[WARNING] Cutoff value ({cutoff}) larger than library length,"
            + "defaulting to 5"
        )
        cutoff = 5
    sdf = qs_df(df, "dis", abc_leq, cutoff=cutoff)
    return sdf