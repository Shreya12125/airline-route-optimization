"""
Step 5: Maximum Flow (optional stretch)
-------------------------------------------
Given a source and target airport, finds the maximum flow through the
route network using n_airlines (distinct carriers per route) as a
capacity proxy, via the "capacity" edge alias added in graph_builder.py.

CAVEAT: n_airlines (airline count) is a rough proxy for capacity, not a
true seat/frequency figure - OpenFlights has no real capacity field.
Treat this result as illustrative, not authoritative.
"""

import argparse
import json
import os
import sys

import networkx as nx

from data_prep import load_clean_dataset
from graph_builder import build_graph

# Default example: two of the busiest hubs in the network (see
# outputs/network_summary.json -> top_hubs_total_degree / top_city_pairs_by_airlines).
DEFAULT_SOURCE = "FRA"
DEFAULT_TARGET = "JFK"


def validate_airports(G: nx.DiGraph, source: str, target: str):
    """Check both airports exist in the graph. Raises ValueError if not."""
    source = source.upper().strip()
    target = target.upper().strip()
    missing = [a for a in (source, target) if a not in G]
    if missing:
        raise ValueError(
            f"Warning: these codes were not found in the graph and cannot be used: {missing}"
        )
    return source, target


def compute_max_flow(G: nx.DiGraph, source: str, target: str):
    """
    Runs nx.maximum_flow using the "capacity" edge attribute (= n_airlines,
    aliased in graph_builder.py). Returns (flow_value, flow_dict).
    Raises nx.NetworkXUnbounded if any edge on a path lacks a capacity
    (this is a real possible outcome here, not just an edge case).
    """
    flow_value, flow_dict = nx.maximum_flow(G, source, target, capacity="capacity")
    return flow_value, flow_dict


def print_max_flow(source: str, target: str, flow_value: float, flow_dict: dict, G: nx.DiGraph, top_n: int = 30):
    print(f"\nMaximum flow {source} -> {target}: {flow_value:.0f} (airline-count units)\n")
    print("CAVEAT: n_airlines is a rough capacity proxy, not a true seat/frequency")
    print("figure - OpenFlights has no real capacity field. Treat this result as")
    print("illustrative, not authoritative.\n")

    nonzero = [
        (u, v, flow) for u, targets in flow_dict.items()
        for v, flow in targets.items() if flow > 0
    ]
    nonzero.sort(key=lambda e: e[2], reverse=True)

    print(f"Edges carrying nonzero flow ({len(nonzero)} total"
          + (f", top {top_n} shown by flow amount" if len(nonzero) > top_n else "") + "):")
    for u, v, flow in nonzero[:top_n]:
        capacity = G[u][v]["capacity"]
        print(f"  {u} -> {v}: {flow:.0f} out of {capacity} (airlines)")
    if len(nonzero) > top_n:
        print(f"  ... {len(nonzero) - top_n} more - see outputs/max_flow_result.json for the full list")


def save_result(path: str, source: str, target: str, flow_value: float, flow_dict: dict):
    nonzero_edges = sorted(
        (
            {"from": u, "to": v, "flow": flow}
            for u, targets in flow_dict.items()
            for v, flow in targets.items()
            if flow > 0
        ),
        key=lambda e: e["flow"], reverse=True,
    )
    result = {
        "source": source,
        "target": target,
        "max_flow_value": flow_value,
        "capacity_key": "capacity (alias of n_airlines)",
        "caveat": (
            "n_airlines (airline count) is a rough proxy for capacity, not a "
            "true seat/frequency figure - OpenFlights has no real capacity "
            "field. Treat this result as illustrative, not authoritative."
        ),
        "nonzero_flow_edges": nonzero_edges,
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Compute maximum flow between two airports using n_airlines as a capacity proxy."
    )
    parser.add_argument("source", nargs="?", default=DEFAULT_SOURCE, help=f"Source IATA code (default: {DEFAULT_SOURCE})")
    parser.add_argument("target", nargs="?", default=DEFAULT_TARGET, help=f"Target IATA code (default: {DEFAULT_TARGET})")
    parser.add_argument("--data-dir", default="data", help="Directory containing airports.dat / routes.dat")
    args = parser.parse_args()

    print("Loading and cleaning data...")
    airports, routes = load_clean_dataset(args.data_dir)
    print("Building graph...")
    G = build_graph(airports, routes)

    try:
        source, target = validate_airports(G, args.source, args.target)
    except ValueError as e:
        print(e)
        sys.exit(1)

    print(f"\nComputing maximum flow {source} -> {target}...")
    try:
        flow_value, flow_dict = compute_max_flow(G, source, target)
    except nx.NetworkXUnbounded:
        print(
            f"\nMax flow {source} -> {target} is unbounded: at least one edge "
            "on a path between them is missing a capacity value, so "
            "nx.maximum_flow treats it as infinite. No result to report."
        )
        sys.exit(1)
    except nx.NetworkXNoPath:
        print(f"\nNo path exists between {source} and {target}; max flow is 0.")
        sys.exit(1)

    print_max_flow(source, target, flow_value, flow_dict, G)

    out_path = os.path.join("outputs", "max_flow_result.json")
    save_result(out_path, source, target, flow_value, flow_dict)
    print(f"\nSaved max-flow result to {out_path}")


if __name__ == "__main__":
    main()
