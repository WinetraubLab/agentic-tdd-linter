def add(left: int, right: int) -> int:
    return left + right


def test_adds_positive_numbers() -> None:
    """Test Path: happy path

    Requirement Tested:
    add returns the arithmetic sum for two positive integers.

    Verification Method: verify public function output

    Verification Detail:
    by asserting the returned numeric total.
    """

    assert add(1, 2) == 3
