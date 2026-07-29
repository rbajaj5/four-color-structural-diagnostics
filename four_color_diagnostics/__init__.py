"""Proof-guided planar graph coloring diagnostics."""

from .audit import audit_graph_atlas, independent_bruteforce_chromatic
from .coloring import ColoringResult, solve_k_coloring, verify_coloring
from .diagnose import Diagnosis, diagnose_planar_graph, generic_exact_chromatic
from .graph import Graph
from .spectral import (
    PartitionResult,
    SpectralFeatures,
    articulation_separator_partition,
    bfs_balanced_partition,
    connected_component_partition,
    fiedler_partition,
    spectral_features,
    verify_coalescence_identity,
    verify_disjoint_union_identity,
)
from .tait import (
    TaitGraph,
    TaitPair,
    faces_from_pd_code,
    fox_coloring_determinant,
    tait_graphs_from_pd_code,
)

__all__ = [
    "ColoringResult",
    "Diagnosis",
    "Graph",
    "PartitionResult",
    "SpectralFeatures",
    "TaitGraph",
    "TaitPair",
    "articulation_separator_partition",
    "audit_graph_atlas",
    "bfs_balanced_partition",
    "connected_component_partition",
    "diagnose_planar_graph",
    "fiedler_partition",
    "faces_from_pd_code",
    "fox_coloring_determinant",
    "generic_exact_chromatic",
    "independent_bruteforce_chromatic",
    "solve_k_coloring",
    "spectral_features",
    "tait_graphs_from_pd_code",
    "verify_coalescence_identity",
    "verify_disjoint_union_identity",
    "verify_coloring",
]
