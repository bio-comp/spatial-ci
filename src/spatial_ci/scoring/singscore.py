"""Internal-first singscore boundary for Spatial-CI.

The scorer stays inside Spatial-CI until R parity, contract behavior, and
reuse demand justify extraction into a standalone package.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from spatial_ci.signatures import GeneSignature


class MissingGenePolicy(str, Enum):
    """How the scorer should behave when signature genes are absent."""

    INTERSECT = "intersect"
    ERROR = "error"
    DROP_SAMPLE = "drop_sample"


class TiePolicy(str, Enum):
    """Explicit tie-handling controls for future Python scoring parity work."""

    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    DENSE = "dense"


@dataclass(frozen=True)
class ScoreResult:
    """Minimal score artifact returned by the internal scorer."""

    score: float | None
    n_genes_total: int
    n_genes_matched: int
    missing_genes: tuple[str, ...]
    tie_policy: TiePolicy
    missing_gene_policy: MissingGenePolicy


def singscore(
    expression_by_gene: Mapping[str, float],
    signature: GeneSignature,
    *,
    tie_policy: TiePolicy = TiePolicy.AVERAGE,
    missing_gene_policy: MissingGenePolicy = MissingGenePolicy.INTERSECT,
) -> ScoreResult:
    """Score one sample against one signature.

    The stable public boundary lands now; the numerical implementation follows
    once parity fixtures against R/Bioconductor `singscore` are in place.
    """

    raise NotImplementedError(
        "Python singscore remains internal-first until Bioconductor parity and "
        "contract behavior are implemented and verified."
    )
