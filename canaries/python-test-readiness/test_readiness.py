import pytest

from smoke_module import add
from unboundlocal_fixture import trigger_unboundlocal


def test_pytest_runs_a_passing_test() -> None:
    assert add(2, 3) == 5


def test_pytest_surfaces_unboundlocalerror() -> None:
    with pytest.raises(UnboundLocalError):
        trigger_unboundlocal()
