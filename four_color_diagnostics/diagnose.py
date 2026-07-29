"""Theorem-directed exact chromatic diagnosis for planar graphs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .coloring import (
    ColoringResult,
    bipartite_coloring,
    solve_k_coloring,
    verify_coloring,
)
from .graph import Graph


@dataclass(frozen=True)
class Diagnosis:
    chromatic_number: int
    route: str
    theorem: str
    coloring: tuple[int, ...]
    certificate_valid: bool
    planar: bool
    triangle_free: bool
    sphere_triangulation: bool
    all_degrees_even: bool
    structural_search_nodes: int
    structural_backtracks: int

    def as_dict(self) -> dict[str, Any]:
        row = asdict(self)
        row["coloring"] = " ".join(map(str, self.coloring))
        return row


def _planar_facts(graph: Graph) -> dict[str, Any]:
    import networkx as nx

    nx_graph = graph.to_networkx()
    planar, embedding = nx.check_planarity(nx_graph, counterexample=True)
    if not planar:
        return {
            "planar": False,
            "triangle_free": False,
            "sphere_triangulation": False,
            "all_degrees_even": False,
        }
    embedding.check_structure()
    triangle_free = sum(nx.triangles(nx_graph).values()) == 0
    connected = (
        graph.vertex_count > 0 and nx.is_connected(nx_graph)
    )
    sphere_triangulation = (
        graph.vertex_count >= 3
        and connected
        and len(graph.edges) == 3 * graph.vertex_count - 6
    )
    return {
        "planar": True,
        "triangle_free": triangle_free,
        "sphere_triangulation": sphere_triangulation,
        "all_degrees_even": all(
            degree % 2 == 0 for degree in graph.degrees
        ),
    }


def _checked_diagnosis(
    graph: Graph,
    *,
    chromatic_number: int,
    route: str,
    theorem: str,
    coloring: tuple[int, ...],
    facts: dict[str, Any],
    search: ColoringResult | None,
) -> Diagnosis:
    valid = verify_coloring(graph, coloring, chromatic_number)
    if not valid:
        raise AssertionError("invalid explicit coloring certificate")
    return Diagnosis(
        chromatic_number=chromatic_number,
        route=route,
        theorem=theorem,
        coloring=coloring,
        certificate_valid=True,
        planar=True,
        triangle_free=bool(facts["triangle_free"]),
        sphere_triangulation=bool(facts["sphere_triangulation"]),
        all_degrees_even=bool(facts["all_degrees_even"]),
        structural_search_nodes=0 if search is None else search.search_nodes,
        structural_backtracks=0 if search is None else search.backtracks,
    )


def diagnose_planar_graph(graph: Graph) -> Diagnosis:
    """Return exact ``chi`` and an independently checkable coloring."""

    facts = _planar_facts(graph)
    if not facts["planar"]:
        raise ValueError("the structural hierarchy requires a planar graph")
    if not graph.edges:
        coloring = tuple(0 for _ in range(graph.vertex_count))
        return _checked_diagnosis(
            graph,
            chromatic_number=1,
            route="edgeless",
            theorem="direct inspection",
            coloring=coloring,
            facts=facts,
            search=None,
        )

    two_coloring = bipartite_coloring(graph)
    if two_coloring is not None:
        return _checked_diagnosis(
            graph,
            chromatic_number=2,
            route="bipartite",
            theorem="odd-cycle characterization",
            coloring=two_coloring,
            facts=facts,
            search=None,
        )

    if facts["triangle_free"]:
        search = solve_k_coloring(graph, 3)
        if not search.feasible or search.coloring is None:
            raise AssertionError("Groetzsch certificate search failed")
        return _checked_diagnosis(
            graph,
            chromatic_number=3,
            route="triangle_free_non_bipartite",
            theorem="Groetzsch plus odd-cycle lower bound",
            coloring=search.coloring,
            facts=facts,
            search=search,
        )

    if facts["sphere_triangulation"]:
        chromatic_number = 3 if facts["all_degrees_even"] else 4
        search = solve_k_coloring(graph, chromatic_number)
        if not search.feasible or search.coloring is None:
            raise AssertionError("triangulation certificate search failed")
        return _checked_diagnosis(
            graph,
            chromatic_number=chromatic_number,
            route=(
                "eulerian_sphere_triangulation"
                if facts["all_degrees_even"]
                else "non_eulerian_sphere_triangulation"
            ),
            theorem="Heawood parity criterion plus Four Color",
            coloring=search.coloring,
            facts=facts,
            search=search,
        )

    three = solve_k_coloring(graph, 3)
    if three.feasible and three.coloring is not None:
        return _checked_diagnosis(
            graph,
            chromatic_number=3,
            route="generic_planar_three_color_yes",
            theorem="fixed 3-color decision",
            coloring=three.coloring,
            facts=facts,
            search=three,
        )

    four = solve_k_coloring(graph, 4)
    if not four.feasible or four.coloring is None:
        raise AssertionError("Four Color certificate search failed")
    combined = ColoringResult(
        feasible=True,
        coloring=four.coloring,
        search_nodes=three.search_nodes + four.search_nodes,
        backtracks=three.backtracks + four.backtracks,
        color_count=4,
    )
    return _checked_diagnosis(
        graph,
        chromatic_number=4,
        route="generic_planar_three_color_no",
        theorem="3-color obstruction plus Four Color",
        coloring=four.coloring,
        facts=facts,
        search=combined,
    )


def generic_exact_chromatic(
    graph: Graph,
    maximum_colors: int = 4,
) -> tuple[int, ColoringResult, int, int]:
    """Blindly test palettes in increasing order for benchmark comparison."""

    total_nodes = 0
    total_backtracks = 0
    for color_count in range(1, maximum_colors + 1):
        result = solve_k_coloring(graph, color_count)
        total_nodes += result.search_nodes
        total_backtracks += result.backtracks
        if result.feasible:
            return color_count, result, total_nodes, total_backtracks
    raise ValueError("graph exceeds the requested color ceiling")
