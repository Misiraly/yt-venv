abc = r"modules\abc.txt"


def line_breaker(text, position):
    """
    Breaks up a text closest from below to 'position'.
    Returns a list of strings.
    """
    if len(text) <= position:
        return [text]
    pretty = []
    string = text
    cursor = position
    iteration = (len(text) + 1) // position
    for i in range(iteration):
        cursor = position
        while string[cursor] != " ":
            cursor -= 1
        pretty.append(string[:cursor])
        string = string[cursor + 1 :]
    if string != "":
        pretty.append(string)
    return pretty


def raw_abc_to_abc():
    with open(abc, "r", encoding="utf-8") as r:
        raw_forms = r.read()
    raw_forms = raw_forms.split("#end#")
    raw_forms.pop(-1)
    letters = {}
    for form in raw_forms:
        split_form = form.split("\n")
        split_form = [line for line in split_form if line != ""]
        # print(split_form)
        key = split_form[0][1]
        assert (
            len(split_form) < 5
        ), f"Character is taller than 3 lines in the abc {split_form}"
        max_len = max([len(line) for line in split_form[1:]])
        letters[key] = [
            split_form[1] + " " * (max_len - len(split_form[1])),
            split_form[2] + " " * (max_len - len(split_form[2])),
            split_form[3] + " " * (max_len - len(split_form[3])),
        ]
        # print(letters[key])
    return letters


def abc_rower(text, press=False):
    letters = raw_abc_to_abc()
    line0 = ""
    line1 = ""
    line2 = ""
    for char in text:
        line0 += " " + letters[char][0]
        line1 += " " + letters[char][1]
        line2 += " " + letters[char][2]
    if press:
        print(line0)
        print(line1)
        print(line2)
    return [line0, line1, line2]


def print_rows(three_rows):
    for row in three_rows:
        print(row)
