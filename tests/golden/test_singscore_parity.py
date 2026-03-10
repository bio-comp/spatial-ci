import pytest

pytestmark = pytest.mark.skip(
    reason=(
        "Golden parity against R/Bioconductor singscore is the extraction gate "
        "and is not implemented yet."
    )
)


def test_bioconductor_parity_placeholder() -> None:
    raise AssertionError("Remove the module skip when parity fixtures exist.")
