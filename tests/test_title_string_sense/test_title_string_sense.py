import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import yt

# Test constants
TEMP_LIBRARY = "tests/test_title_string_sense/temp_library"


@pytest.fixture(autouse=True)
def setup_teardown():
    """Create and clean up temporary library directory."""
    os.makedirs(TEMP_LIBRARY, exist_ok=True)
    yield
    # Cleanup
    for file in Path(TEMP_LIBRARY).glob("*"):
        file.unlink()
    Path(TEMP_LIBRARY).rmdir()


def test_title_string_sense_valid_title():
    """Test with a valid title that passes all checks."""
    with patch("yt.LIBRARY", TEMP_LIBRARY):
        result = yt.title_string_sense("Test Song Title", check_path=False)
        assert result == "Test Song Title"


def test_title_string_sense_empty_title():
    """Test that empty title prompts user for input."""
    with patch("yt.LIBRARY", TEMP_LIBRARY):
        with patch("builtins.input", return_value="Valid Song Name"):
            result = yt.title_string_sense("", check_path=False)
            assert result == "Valid Song Name"


def test_title_string_sense_short_title_user_accepts():
    """Test short title warning where user declines to rename."""
    with patch("yt.LIBRARY", TEMP_LIBRARY):
        with patch("builtins.input", return_value="n"):
            result = yt.title_string_sense("abc", check_path=False)
            assert result == "abc"


def test_title_string_sense_short_title_user_renames():
    """Test short title warning where user accepts rename."""
    with patch("yt.LIBRARY", TEMP_LIBRARY):
        # first input says "rename", second provides the new filename
        with patch("builtins.input", side_effect=["y", "longer name"]):
            result = yt.title_string_sense("abc", check_path=False)
            assert result == "longer name"


def test_title_string_sense_duplicate_path():
    """Test that duplicate file paths are rejected."""
    with patch("yt.LIBRARY", TEMP_LIBRARY):
        # Create a mock file
        dummy_file = Path(TEMP_LIBRARY) / "Existing Song.ogg"
        dummy_file.touch()

        with patch("builtins.input", return_value="Different Name"):
            result = yt.title_string_sense("Existing Song", check_path=True)
            assert result == "Different Name"


def test_title_string_sense_corrects_special_chars():
    """Test that special characters are stripped from title."""
    with patch("yt.LIBRARY", TEMP_LIBRARY):
        result = yt.title_string_sense("Song @#$% Title!", check_path=False)
        # ls.correct_title removes special chars
        assert result == "Song  Title"


def test_title_string_sense_multiple_empty_retries():
    """Test multiple empty inputs require multiple re-prompts."""
    with patch("yt.LIBRARY", TEMP_LIBRARY):
        with patch("builtins.input", side_effect=["", "  ", "Valid Title"]):
            result = yt.title_string_sense("", check_path=False)
            assert result == "Valid Title"


def test_title_string_sense_check_path_false():
    """Test that check_path=False skips path existence checks."""
    with patch("yt.LIBRARY", TEMP_LIBRARY):
        # Create a file that would normally conflict
        dummy_file = Path(TEMP_LIBRARY) / "Test Song.ogg"
        dummy_file.touch()

        # Should return without prompting about the duplicate path
        result = yt.title_string_sense("Test Song", check_path=False)
        assert result == "Test Song"
