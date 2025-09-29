from pathlib import Path

import yaml

from modules import search_text

FIXTURES = Path("tests/test_search_text/fixtures")
EXPECTED = FIXTURES / "expected_output"
INPUTS = FIXTURES / "inputs"


def test_tokenization(tmpdir):
    # reading the file with utf-8 -- encodings could be problematic
    # song names sourced from "https://www.goldstandardsonglist.com/Pages_Sort_2a/Sort_2a.htm"
    with open(INPUTS / "song_names.txt", encoding="utf-8") as file:
        song_names = file.read().split("\n")
    tokens = [search_text.tokenize_neighbor(name) for name in song_names]
    tokens_act_path = tmpdir / "tokens.yaml"
    tokens_exp_path = EXPECTED / "tokens.yaml"
    # saving the tokens to make manual check possible
    with open(tokens_act_path, "w") as file:
        yaml.safe_dump(tokens, file)
    with open(tokens_exp_path) as f_exp, open(tokens_act_path) as f_act:
        tokens_exp = yaml.safe_load(f_exp)
        tokens_act = yaml.safe_load(f_act)
    assert tokens_act == tokens_exp
