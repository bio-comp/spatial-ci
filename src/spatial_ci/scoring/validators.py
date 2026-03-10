"""Validation helpers shared by internal scoring modules."""

from collections import Counter
from collections.abc import Iterable


def normalize_gene_list(genes: Iterable[str]) -> tuple[str, ...]:
    """Strip whitespace and drop empty gene identifiers."""

    return tuple(gene.strip() for gene in genes if gene.strip())


def duplicate_genes(genes: Iterable[str]) -> tuple[str, ...]:
    """Return duplicate genes in deterministic order."""

    counts = Counter(genes)
    return tuple(sorted(gene for gene, count in counts.items() if count > 1))


def validate_gene_list(genes: Iterable[str], *, label: str) -> tuple[str, ...]:
    """Validate one gene list and return a normalized tuple."""

    normalized = normalize_gene_list(genes)
    if not normalized:
        raise ValueError(f"{label} must contain at least one gene.")

    duplicates = duplicate_genes(normalized)
    if duplicates:
        duplicate_summary = ", ".join(duplicates)
        raise ValueError(f"{label} contains duplicate genes: {duplicate_summary}.")

    return normalized
