import json
from pathlib import Path
from subprocess import CompletedProcess
from typing import Callable

import pytest

FIXTURES_PATH = Path(__file__).parent / "fixtures"


@pytest.fixture
def load_audio_test_fixture() -> Callable[[str], object]:
    def load(relative_path: str) -> object:
        return json.loads((FIXTURES_PATH / relative_path).read_text())

    return load


@pytest.fixture
def make_completed_process() -> Callable[
    [str, int, str], CompletedProcess[str]
]:
    def build(
        stdout: str, returncode: int = 0, stderr: str = ""
    ) -> CompletedProcess[str]:
        return CompletedProcess(
            args=["pw-dump"],
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )

    return build
