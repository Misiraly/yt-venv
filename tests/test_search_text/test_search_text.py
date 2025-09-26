from pathlib import Path

import pytest
import yaml

from modules import search_text

FIXTURES = Path("tests/test_search_text/fixtures")
EXPECTED = FIXTURES / "expected_output"
INPUTS = FIXTURES / "inputs"


def test_tokenization():
    with open(INPUTS / "song_names.txt") as file:
        song_names = file.read().split("\n")
    tokens_act = [search_text.tokenize_neighbor(name) for name in song_names]
    with open(EXPECTED / "tokens.yaml") as file:
        tokens_exp = yaml.safe_load(file)
    assert tokens_act == tokens_exp
