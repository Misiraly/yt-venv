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


def test_playlist_manipulation(tmpdir):
    pl_file_name = "playlists.yaml"
    input_pl_path = FIXTURES / "inputs" / pl_file_name
    expected_pl_path = FIXTURES / "expected_output" / pl_file_name
    tmp_pl_path = tmpdir / pl_file_name
    add_list = "6,1,11332, 4,, 32, 3,,, ,  ,apple, 39,00, 00,pear, 12"
    # create, using input yaml to initate playlists file
    lib_sorter.manipulate_playlist(
        "test_list", add_list, "create", test_table, input_pl_path, tmp_pl_path
    )
    # delete
    lib_sorter.manipulate_playlist(
        "groovy", "", "delete", test_table, tmp_pl_path, tmp_pl_path
    )
    # add
    lib_sorter.manipulate_playlist(
        "rock", add_list, "add", test_table, tmp_pl_path, tmp_pl_path
    )
    # remove
    lib_sorter.manipulate_playlist(
        "rock", "0, 4", "remove", test_table, tmp_pl_path, tmp_pl_path
    )
    # remove_from_all
    lib_sorter.manipulate_playlist(
        "ALL", "  1", "remove_from_all", test_table, tmp_pl_path, tmp_pl_path
    )
    # rename
    lib_sorter.manipulate_playlist(
        "test_list", "", "rename", test_table, tmp_pl_path, tmp_pl_path, "funky"
    )
    yd_exp = lib_sorter.read_playlists(expected_pl_path)
    yd_act = lib_sorter.read_playlists(tmp_pl_path)
    assert yd_exp == yd_act
