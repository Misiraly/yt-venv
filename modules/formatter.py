# Constants
ABC_FILE = r"modules\abc.txt"
LINE_BREAK_THRESHOLD = 3


def line_breaker(text: str, position: int):
    """Break up a text closest from below to 'position'.

    Parameters
    ----------
    text : str
        The text to be broken up.
    position : int
        The position to break the text at.

    Returns
    -------
    List[str]
        A list of strings representing the broken text.
    """
    if len(text) <= position:
        return [text]

    pretty = []
    string = text
    iteration = (len(text) + 1) // position
    for _ in range(iteration):
        cursor = position
        while cursor > 0 and string[cursor] != " ":
            cursor -= 1
        if cursor == 0:
            cursor = position  # If no space found, break at position
        pretty.append(string[:cursor])
        string = string[cursor + 1 :].strip()
    if string:
        pretty.append(string)
    return pretty


def raw_abc_to_abc():
    """Convert raw ABC data to a dictionary of formatted letters."""
    with open(ABC_FILE, "r", encoding="utf-8") as file:
        raw_forms = file.read().split("#end#")

    letters = {}
    for form in raw_forms[:-1]:
        split_form = [line for line in form.split("\n") if line]
        if len(split_form) > LINE_BREAK_THRESHOLD + 1:
            raise ValueError(
                f"Character is taller than {LINE_BREAK_THRESHOLD} lines in the ABC: {split_form}"
            )
        key = split_form[0][1]
        max_len = max(len(line) for line in split_form[1:])
        letters[key] = [line.ljust(max_len) for line in split_form[1:]]
    return letters


def abc_rower(text, press=False):
    """Convert text to its ABC representation.

    Parameters
    ----------
    text : str
        The text to be converted.
    press : bool, optional
        Whether to print the ABC representation, by default False

    Returns
    -------
        A list of strings representing the ABC rows.
    """
    letters = raw_abc_to_abc()
    line0, line1, line2 = "", "", ""
    for char in text:
        if char in letters:
            line0 += " " + letters[char][0]
            line1 += " " + letters[char][1]
            line2 += " " + letters[char][2]
        else:
            line0 += " " * (
                len(letters["A"][0]) + 1
            )  # Assuming default width based on 'A'
            line1 += " " * (len(letters["A"][1]) + 1)
            line2 += " " * (len(letters["A"][2]) + 1)
    if press:
        print(line0)
        print(line1)
        print(line2)
    return [line0, line1, line2]


def print_rows(three_rows):
    for row in three_rows:
        print(row)
