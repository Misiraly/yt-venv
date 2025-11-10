import re

import pandas as pd
from Levenshtein import distance as lev

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


def tokenize_neighbor(streeng: str):
    """
    Tokenize the string and generate neighboring word concatenations.
    ie
    "what are# yoű)dö^ing?"
    -->
    ["what","are","you","doing","whatare","areyou","youdoing"]
    """
    pr_string = streeng.lower()
    pr_string = re.sub(r"[;:\-\+\.\?!,\[\]\(\)\{\}<>\*\~\|=_]", " ", pr_string)
    pr_string = re.sub(r"[\'\"\”\/\\#\$%&@\^`]", "", pr_string)
    for char, replacement in REPLACE_CHAR.items():
        pr_string = pr_string.replace(char, replacement)
    tokens = pr_string.split()
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
    s_word: str, col: str, lib: pd.DataFrame, cutoff: int = 5, depth: int = 6
) -> pd.DataFrame:
    """Sort the DataFrame by Levenshtein distance of tokens from the search word."""
    df = lib.copy(deep=True)
    df["dis"] = df[col].apply(lambda text: token_distance_list(s_word, text, depth))
    sdf = df.sort_values("dis")
    return sdf[:cutoff]
