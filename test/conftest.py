"""pytest configuration file."""
from pathlib import Path

import pytest


@pytest.fixture
def in_temp_dir(tmpdir):
    """Create a temporary directory and change to it for the duration of the test."""
    with tmpdir.as_cwd():
        yield Path(str(tmpdir))
