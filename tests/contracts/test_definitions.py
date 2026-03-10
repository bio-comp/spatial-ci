from hypothesis import given
from hypothesis import strategies as st

from spatial_ci.contracts.definitions import TargetDefinition


def test_target_definition_basic() -> None:
    """Basic sanity check for TargetDefinition."""
    programs = {
        "HALLMARK_HYPOXIA": ["GENE1", "GENE2"],
        "HALLMARK_G2M_CHECKPOINT": ["GENE3", "GENE4"],
    }
    target = TargetDefinition(target_definition_id="test_v1", programs=programs)
    assert target.target_definition_id == "test_v1"
    assert target.programs == programs
    assert target.missing_gene_policy_threshold == 0.1


@given(
    target_id=st.text(min_size=1),
    programs=st.dictionaries(
        keys=st.text(min_size=1),
        values=st.lists(st.text(min_size=1), min_size=1),
        min_size=1,
    ),
    threshold=st.floats(min_value=0.0, max_value=1.0),
)
def test_target_definition_hypothesis(
    target_id: str,
    programs: dict[str, list[str]],
    threshold: float,
) -> None:
    """Property-based test for TargetDefinition."""
    target = TargetDefinition(
        target_definition_id=target_id,
        programs=programs,
        missing_gene_policy_threshold=threshold,
    )
    assert target.target_definition_id == target_id
    assert target.programs == programs
    assert target.missing_gene_policy_threshold == threshold
