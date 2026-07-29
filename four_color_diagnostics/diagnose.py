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
    dual_bipartite: bool | None
    odd_degree_vertices: tuple[int, ...]
    block_count: int
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
            "dual_bipartite": None,
            "odd_degree_vertices": (),
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
    odd_degree_vertices = tuple(
        vertex
        for vertex, degree in enumerate(graph.degrees)
        if degree % 2
    )
    dual_bipartite = (
        _triangulation_dual_is_bipartite(graph, embedding)
        if sphere_triangulation
        else None
    )
    if (
        sphere_triangulation
        and dual_bipartite != (not odd_degree_vertices)
    ):
        raise AssertionError(
            "triangulation parity and dual-bipartiteness disagree"
        )
    return {
        "planar": True,
        "triangle_free": triangle_free,
        "sphere_triangulation": sphere_triangulation,
        "all_degrees_even": not odd_degree_vertices,
        "dual_bipartite": dual_bipartite,
        "odd_degree_vertices": odd_degree_vertices,
    }


def _triangulation_dual_is_bipartite(
    graph: Graph,
    embedding: Any,
) -> bool:
    """Construct the planar dual from an embedding and test bipartiteness."""

    import networkx as nx

    visited: set[tuple[int, int]] = set()
    face_for_half_edge: dict[tuple[int, int], int] = {}
    face_count = 0
    for first, second in embedding.edges():
        if (first, second) in visited:
            continue
        boundary = embedding.traverse_face(first, second, visited)
        for index, vertex in enumerate(boundary):
            following = boundary[(index + 1) % len(boundary)]
            face_for_half_edge[(vertex, following)] = face_count
        face_count += 1

    dual = nx.Graph()
    dual.add_nodes_from(range(face_count))
    for first, second in graph.edges:
        left = face_for_half_edge[(first, second)]
        right = face_for_half_edge[(second, first)]
        if left != right:
            dual.add_edge(left, right)
    return nx.is_bipartite(dual)


def _checked_diagnosis(
    graph: Graph,
    *,
    chromatic_number: int,
    route: str,
    theorem: str,
    coloring: tuple[int, ...],
    facts: dict[str, Any],
    search: ColoringResult | None,
    block_count: int = 1,
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
        dual_bipartite=facts["dual_bipartite"],
        odd_degree_vertices=tuple(facts["odd_degree_vertices"]),
        block_count=block_count,
        structural_search_nodes=0 if search is None else search.search_nodes,
        structural_backtracks=0 if search is None else search.backtracks,
    )


def _induced_block(
    graph: Graph,
    vertices: frozenset[int],
) -> tuple[Graph, tuple[int, ...]]:
    ordered = tuple(sorted(vertices))
    local_index = {
        vertex: index for index, vertex in enumerate(ordered)
    }
    edges = (
        (local_index[first], local_index[second])
        for first, second in graph.edges
        if first in vertices and second in vertices
    )
    return Graph.from_edges(len(ordered), edges), ordered


def _block_decomposition(
    graph: Graph,
) -> tuple[tuple[frozenset[int], ...], tuple[int, ...]] | None:
    import networkx as nx

    nx_graph = graph.to_networkx()
    blocks = tuple(
        sorted(
            (
                frozenset(component)
                for component in nx.biconnected_components(nx_graph)
            ),
            key=lambda block: (min(block), len(block), tuple(sorted(block))),
        )
    )
    isolates = tuple(
        vertex for vertex, degree in enumerate(graph.degrees) if degree == 0
    )
    if len(blocks) + len(isolates) <= 1:
        return None
    return blocks, isolates


def _diagnose_by_blocks(
    graph: Graph,
    facts: dict[str, Any],
    blocks: tuple[frozenset[int], ...],
    isolates: tuple[int, ...],
) -> Diagnosis:
    local_data = []
    for block in blocks:
        local_graph, original_vertices = _induced_block(graph, block)
        local_data.append(
            (
                block,
                original_vertices,
                diagnose_planar_graph(local_graph),
            )
        )

    chromatic_number = max(
        [1 if isolates else 0]
        + [diagnosis.chromatic_number for _, _, diagnosis in local_data]
    )
    coloring = [-1] * graph.vertex_count
    for vertex in isolates:
        coloring[vertex] = 0

    remaining = set(range(len(local_data)))
    while remaining:
        frontier = [
            index
            for index in remaining
            if sum(
                coloring[vertex] >= 0
                for vertex in local_data[index][0]
            )
            == 1
        ]
        index = min(frontier) if frontier else min(remaining)
        block, original_vertices, diagnosis = local_data[index]
        shared = [
            vertex for vertex in block if coloring[vertex] >= 0
        ]
        if len(shared) > 1:
            raise AssertionError("block traversal is not a block-cut forest")

        local_to_global: dict[int, int] = {}
        if shared:
            articulation = shared[0]
            local_vertex = original_vertices.index(articulation)
            local_to_global[diagnosis.coloring[local_vertex]] = coloring[
                articulation
            ]
        available = [
            color
            for color in range(chromatic_number)
            if color not in local_to_global.values()
        ]
        for local_color in range(diagnosis.chromatic_number):
            if local_color not in local_to_global:
                local_to_global[local_color] = available.pop(0)
        for local_vertex, original_vertex in enumerate(original_vertices):
            mapped = local_to_global[diagnosis.coloring[local_vertex]]
            if coloring[original_vertex] not in (-1, mapped):
                raise AssertionError("inconsistent articulation color")
            coloring[original_vertex] = mapped
        remaining.remove(index)

    if any(color < 0 for color in coloring):
        raise AssertionError("block gluing left an uncolored vertex")
    search = ColoringResult(
        feasible=True,
        coloring=tuple(coloring),
        search_nodes=sum(
            diagnosis.structural_search_nodes
            for _, _, diagnosis in local_data
        ),
        backtracks=sum(
            diagnosis.structural_backtracks
            for _, _, diagnosis in local_data
        ),
        color_count=chromatic_number,
    )
    return _checked_diagnosis(
        graph,
        chromatic_number=chromatic_number,
        route="block_decomposition",
        theorem="chromatic number is the maximum over graph blocks",
        coloring=tuple(coloring),
        facts=facts,
        search=search,
        block_count=len(blocks) + len(isolates),
    )


def diagnose_planar_graph(
    graph: Graph,
    *,
    use_block_decomposition: bool = True,
) -> Diagnosis:
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

    decomposition = (
        _block_decomposition(graph)
        if use_block_decomposition
        else None
    )
    if decomposition is not None:
        blocks, isolates = decomposition
        return _diagnose_by_blocks(
            graph,
            facts,
            blocks,
            isolates,
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
