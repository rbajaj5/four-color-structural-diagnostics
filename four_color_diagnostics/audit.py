"""Independent exhaustive checks for small planar graphs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import itertools
from typing import Any

from .diagnose import diagnose_planar_graph
from .graph import Graph


@dataclass(frozen=True)
class AtlasAuditRow:
    atlas_index: int
    graph_fingerprint: str
    vertex_count: int
    edge_count: int
    route: str
    structural_chromatic_number: int
    independent_chromatic_number: int
    certificate_valid: bool
    exact_match: bool
    independent_assignments_tested: int
    dual_parity_agreement: bool | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def graph_fingerprint(graph: Graph) -> str:
    """Return a stable content fingerprint for an already labeled graph."""

    payload = (
        f"{graph.vertex_count}|"
        + ";".join(f"{first}-{second}" for first, second in graph.edges)
    )
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def independent_bruteforce_chromatic(
    graph: Graph,
    maximum_colors: int = 4,
) -> tuple[int, tuple[int, ...], int]:
    """Compute chi by direct assignment enumeration for tiny graphs.

    This deliberately does not call the DSATUR implementation. Global color
    symmetry permits fixing vertex zero to color zero.
    """

    if graph.vertex_count == 0:
        return 0, (), 1
    assignments_tested = 0
    for color_count in range(1, maximum_colors + 1):
        for suffix in itertools.product(
            range(color_count),
            repeat=graph.vertex_count - 1,
        ):
            coloring = (0, *suffix)
            assignments_tested += 1
            if all(
                coloring[first] != coloring[second]
                for first, second in graph.edges
            ):
                return color_count, coloring, assignments_tested
    raise ValueError("graph exceeds the requested color ceiling")


def audit_graph_atlas(
    maximum_vertices: int = 7,
) -> tuple[AtlasAuditRow, ...]:
    """Audit every nonempty planar graph in the NetworkX graph atlas."""

    import networkx as nx

    rows = []
    for atlas_index, nx_graph in enumerate(nx.graph_atlas_g()):
        vertex_count = nx_graph.number_of_nodes()
        if not 0 < vertex_count <= maximum_vertices:
            continue
        planar, _ = nx.check_planarity(nx_graph)
        if not planar:
            continue
        graph = Graph.from_networkx(nx_graph)
        diagnosis = diagnose_planar_graph(graph)
        independent_chi, _, assignments = independent_bruteforce_chromatic(
            graph
        )
        dual_parity_agreement = (
            diagnosis.dual_bipartite == diagnosis.all_degrees_even
            if diagnosis.sphere_triangulation
            else None
        )
        rows.append(
            AtlasAuditRow(
                atlas_index=atlas_index,
                graph_fingerprint=graph_fingerprint(graph),
                vertex_count=graph.vertex_count,
                edge_count=len(graph.edges),
                route=diagnosis.route,
                structural_chromatic_number=diagnosis.chromatic_number,
                independent_chromatic_number=independent_chi,
                certificate_valid=diagnosis.certificate_valid,
                exact_match=(
                    diagnosis.chromatic_number == independent_chi
                ),
                independent_assignments_tested=assignments,
                dual_parity_agreement=dual_parity_agreement,
            )
        )
    return tuple(rows)
