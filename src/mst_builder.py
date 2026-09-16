"""
Step 4: Minimal Spanning Tree (MST)
--------------------------------------
Given a set of airports (IATA codes), find the minimum-cost set of edges
that connects all of them.

Since a direct route may not exist between every pair of chosen airports,
we first build a COMPLETE graph over just the chosen subset, where the
edge weight between any two airports is their shortest-path distance
through the FULL route network (Dijkstra). Kruskal's algorithm is then
run on this complete graph to get the MST.

This answers: "what's the cheapest way to connect all these cities,
using the real route network to get between them?"
"""

import argparse
import itertools
import os
import sys

import networkx as nx

from data_prep import load_clean_dataset
from graph_builder import build_graph

# Default subset: major Indian metro airports
DEFAULT_AIRPORTS = ["DEL", "BOM", "BLR", "MAA", "CCU", "HYD", "AMD", "COK"]


def build_complete_subgraph(G: nx.DiGraph, airports: list) -> nx.Graph:
    """
    Build an undirected complete graph over `airports`, where each edge
    weight is the shortest-path distance (km) between that pair through
    the full route network G. Missing/unreachable airports are reported
    and skipped.
    """
    airports = [a.upper().strip() for a in airports]
    valid = [a for a in airports if a in G]
    missing = [a for a in airports if a not in G]
    if missing:
        print(f"Warning: these codes were not found in the graph and will be skipped: {missing}")

    if len(valid) < 2:
        raise ValueError("Need at least 2 valid airports to build an MST.")

    H = nx.Graph()
    H.add_nodes_from(valid)

    for a, b in itertools.combinations(valid, 2):
        try:
            dist = nx.shortest_path_length(G, source=a, target=b, weight="weight")
            path = nx.shortest_path(G, source=a, target=b, weight="weight")
            H.add_edge(a, b, weight=dist, via=path)
        except nx.NetworkXNoPath:
            print(f"Warning: no path exists between {a} and {b} - they cannot both be in the MST.")

    return H


def compute_mst(H: nx.Graph) -> nx.Graph:
    """Run Kruskal's algorithm (networkx default) on the complete subgraph."""
    return nx.minimum_spanning_tree(H, weight="weight", algorithm="kruskal")


def print_mst(mst: nx.Graph, G: nx.DiGraph):
    total = sum(d["weight"] for _, _, d in mst.edges(data=True))
    print(f"\nMinimum Spanning Tree connects {mst.number_of_nodes()} airports "
          f"with {mst.number_of_edges()} links, total distance {total:.1f} km\n")

    for u, v, d in sorted(mst.edges(data=True), key=lambda e: e[2]["weight"]):
        u_city = G.nodes[u]["city"] if u in G else u
        v_city = G.nodes[v]["city"] if v in G else v
        via = d.get("via", [u, v])
        direct = "(direct route)" if len(via) == 2 else f"(via {' -> '.join(via[1:-1])})"
        print(f"  {u} ({u_city}) -- {v} ({v_city}): {d['weight']:.1f} km  {direct}")


def main():
    parser = argparse.ArgumentParser(
        description="Compute minimal spanning tree connecting a set of airports."
    )
    parser.add_argument(
        "airports", nargs="*",
        help=f"IATA codes to connect (default: {' '.join(DEFAULT_AIRPORTS)})"
    )
    parser.add_argument("--data-dir", default="data", help="Directory containing airports.dat / routes.dat")
    args = parser.parse_args()

    airport_set = args.airports if args.airports else DEFAULT_AIRPORTS
    if len(airport_set) < 2:
        print("Error: provide at least 2 airport codes, or omit args to use the default set.")
        sys.exit(1)

    print(f"Airport set: {airport_set}\n")
    print("Loading and cleaning data...")
    airports_df, routes_df = load_clean_dataset(args.data_dir)
    print("Building graph...")
    G = build_graph(airports_df, routes_df)

    print("Computing pairwise shortest-path distances...")
    H = build_complete_subgraph(G, airport_set)

    print("Running Kruskal's algorithm...")
    mst = compute_mst(H)

    print_mst(mst, G)

    os.makedirs("outputs", exist_ok=True)
    nx.write_gml(mst, "outputs/mst_result.gml")
    print("\nSaved MST to outputs/mst_result.gml")


if __name__ == "__main__":
    main()
