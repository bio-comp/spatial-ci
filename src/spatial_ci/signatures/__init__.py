"""Signature definitions used by internal scoring code."""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass


def _normalize_gene_list(genes: Iterable[str]) -> tuple[str, ...]:
    return tuple(gene.strip() for gene in genes if gene.strip())


def _validate_gene_list(genes: Iterable[str], *, label: str) -> tuple[str, ...]:
    normalized = _normalize_gene_list(genes)
    if not normalized:
        raise ValueError(f"{label} must contain at least one gene.")

    counts = Counter(normalized)
    duplicates = tuple(sorted(gene for gene, count in counts.items() if count > 1))
    if duplicates:
        duplicate_summary = ", ".join(duplicates)
        raise ValueError(f"{label} contains duplicate genes: {duplicate_summary}.")

    return normalized


@dataclass(frozen=True)
class GeneSignature:
    """General-purpose gene signature with optional down genes."""

    name: str
    up_genes: tuple[str, ...]
    down_genes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("name must be non-empty.")

        normalized_up = _validate_gene_list(self.up_genes, label="up_genes")
        object.__setattr__(self, "up_genes", normalized_up)

        if self.down_genes:
            normalized_down = _validate_gene_list(self.down_genes, label="down_genes")
            overlap = tuple(sorted(set(normalized_up) & set(normalized_down)))
            if overlap:
                overlap_summary = ", ".join(overlap)
                raise ValueError(
                    f"up_genes and down_genes must be disjoint: {overlap_summary}."
                )
            object.__setattr__(self, "down_genes", normalized_down)


__all__ = ["GeneSignature"]
