import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rhe.l0_rules.loader import load_ruleset  # noqa: E402


@pytest.fixture(scope="session")
def ruleset():
    return load_ruleset()


@pytest.fixture(scope="session")
def root():
    return ROOT
