import os

import pytest


@pytest.fixture(autouse=True)
def acoupi_home(tmp_path):
    os.environ["ACOUPI_HOME"] = str(tmp_path)
    return tmp_path
