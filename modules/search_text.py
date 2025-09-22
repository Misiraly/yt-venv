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
    """Partition the list into elements less than or equal to the pivot and elements greater than the pivot."""
    pivot = tosort[-1]
    left = [el for el in tosort[:-1] if leq(el[1], pivot[1])]
    right = [el for el in tosort if not leq(el[1], pivot[1])]
    return left, [pivot], right


def qs_eng(tosort, leq):
    """Recursively sort the list using quicksort algorithm."""
    if len(tosort) <= 1:
        return tosort
    left, pivot, right = qsp(tosort, leq)
    left = qs_eng(left, leq)
    right = qs_eng(right, leq)
    return left + pivot + right


def qs_df(df, col, leq, cutoff=5) -> pd.DataFrame:
    """Apply the quicksort algorithm to a DataFrame by one of its columns."""
    ilist = df.index.values.tolist()
    dislist = df[col].values.tolist()
    tosort = list(zip(ilist, dislist))
    sortlist = qs_eng(tosort, leq)
    ilist = [el[0] for el in sortlist[:cutoff]]
    sdf = df.loc[ilist]
    return sdf


def abc_leq(list_1, list_2) -> bool:  # == (list_1 <= list_2)
    """Check if list_1 is less than or equal to list_2 lexicographically."""
    least = min(len(list_1), len(list_2))
    for i in range(least):
        if list_1[i] == list_2[i]:
            continue
        return list_1[i] < list_2[i]
    return len(list_1) <= len(list_2)


def tokenize_neighbor(streeng: str):
    """
    Tokenize the string and generate neighboring word concatenations.
    ie
    "what are# yoű)dö^ing?"
    -->
    ["what","are","you","doing","whatare","areyou","youdoing"]
    """
    string = streeng.lower()
    for char in SEP_CHAR:
        string = string.replace(char, " ")
    for char in IGNORE_CHAR:
        string = string.replace(char, "")
    for char, replacement in REPLACE_CHAR.items():
        string = string.replace(char, replacement)
    tokens = string.split()
    tokens = [token for token in tokens if token != ""]
    neigh_tokens = [tokens[i] + tokens[i + 1] for i in range(len(tokens) - 1)]
    return tokens + neigh_tokens


def token_distance_list(search_value, text, cutoff=5):
    """Calculate the Levenshtein distance between tokens and return sorted distances."""
    search_tokens = tokenize_neighbor(search_value)
    text_tokens = tokenize_neighbor(text)
    distance_list = []

    for token1 in search_tokens:
        if token1 in text.lower():
            distance_list.append(1)  # very close match
        for token2 in text_tokens:
            distance_list.append(lev(token1, token2))

    distance_list.sort()
    return distance_list[:cutoff]


def sorted_by_word(
    s_word: str, col: str, lib: pd.DataFrame, cutoff: int = 5
) -> pd.DataFrame:
    """Sort the DataFrame by Levenshtein distance of tokens from the search word."""
    df = lib.copy(deep=True)
    df["dis"] = df[col].apply(lambda text: token_distance_list(s_word, text, cutoff))
    if cutoff > len(df.index):
        print(
            f"[WARNING] Cutoff value ({cutoff}) larger than library length,"
            + "defaulting to 5"
        )
        cutoff = 5
    sdf = qs_df(df, "dis", abc_leq, cutoff=cutoff)
    return sdf
