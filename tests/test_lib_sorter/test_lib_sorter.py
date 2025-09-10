from pathlib import Path

import pytest

import lib_sorter

FIXTURES = Path("tests/test_lib_sorter/fixtures")
EMPTY = "empty_pl_file.yaml"
empty_pl_file = f"tests/test_lib_sorter/fixtures/expected_output/{EMPTY}"
test_table = "data/test-table.csv"


def test_pl_file_creation(tmpdir):
    new_empty_file = tmpdir / EMPTY
    lib_sorter.create_playlist_file(new_empty_file)
    yd_expected = lib_sorter.read_playlists(empty_pl_file)
    print(yd_expected, empty_pl_file)
    yd_actual = lib_sorter.read_playlists(new_empty_file)
    assert yd_actual == yd_expected


def test_uid_validation():
    valid_list = ["662b307cf5121b6a", "6ce30a3874668de7", "d71f9658af5f5b6c"]
    bad_list = ["662b307cf5121b6a", "bad_example", "d71f9658af5f5b6c"]
    lib_sorter._validate_song_list(valid_list)
    with pytest.raises(Exception):
        lib_sorter._validate_song_list(bad_list)


@pytest.mark.parametrize("option", ["create", "add", "remove"])
def test_playlist_manipulation(option, tmpdir):
    playlist_file_name = option + "_playlist.yaml"
    playlist_path = FIXTURES / "inputs/playlists.yaml"
    expected_pl_path = FIXTURES / "expected_output" / playlist_file_name
    tmp_pl_path = tmpdir / playlist_file_name
    playlist_name = "test_list" if option == "create" else "rock"
    number_list = "1,11332, 4,, 32, 3,,, ,  ,apple, 39,00, 00,pear, 12"
    lib_sorter.manipulate_playlist(
        playlist_name, number_list, option, test_table, playlist_path, tmp_pl_path
    )
    yd_exp = lib_sorter.read_playlists(expected_pl_path)
    yd_act = lib_sorter.read_playlists(tmp_pl_path)
    assert yd_exp == yd_act
