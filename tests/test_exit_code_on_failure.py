#!/usr/bin/env python3
"""Failed files must produce a nonzero exit code (not a silent success)."""

from pathlib import Path
from unittest.mock import patch

import pytest

from ordnung.file_sorter import main


def test_main_exits_nonzero_when_processing_fails(tmp_path, caplog):
    """An unreadable/invalid file must exit 1 instead of reporting success."""
    bad_file = tmp_path / "broken.json"
    bad_file.write_text('{"a": 1,}')

    with patch("sys.argv", ["ordnung", str(bad_file)]), pytest.raises(
        SystemExit,
    ) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_main_still_processes_valid_file_and_exits_zero(tmp_path, caplog):
    """A valid file keeps exiting 0 with the success message."""
    good_file = tmp_path / "good.json"
    good_file.write_text('{"b": 1, "a": 2}')

    with patch("sys.argv", ["ordnung", str(good_file)]), caplog.at_level("INFO"):
        main()

    assert "Successfully processed 1 file(s)." in caplog.text
    assert '"a": 2' in good_file.read_text(encoding="utf-8")


def test_main_mixed_valid_and_broken_file_exits_nonzero(tmp_path):
    """One broken file among valid ones must still fail the run."""
    good_file = tmp_path / "good.json"
    good_file.write_text('{"b": 1, "a": 2}')
    bad_file = tmp_path / "broken.json"
    bad_file.write_text("not json at all {")

    with patch(
        "sys.argv", ["ordnung", str(good_file), str(bad_file)],
    ), pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    # The valid file was still sorted before the failure was reported.
    assert '"a": 2' in good_file.read_text(encoding="utf-8")
