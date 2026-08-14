"""
Step 3: Shortest-Route Problem
---------------------------------
Given an origin and destination IATA code, finds the minimum-distance
path through the route network using Dijkstra's algorithm
(edge weight = great-circle distance in km).
"""

import argparse
import os
import sys

import networkx as nx

from data_prep import load_clean_dataset
from graph_builder import build_graph


def shortest_route(G: nx.DiGraph, origin: str, destination: str):
    """
    Returns a dict with the shortest path, total distance, hop count,
    and per-leg breakdown between origin and destination (IATA codes).
    Raises ValueError if either airport is missing, or nx.NetworkXNoPath
    if no route connects them.
    """
    origin = origin.upper().strip()
    destination = destination.upper().strip()

    for code in (origin, destination):
        if code not in G:
            raise ValueError(f"Airport code '{code}' not found in the graph.")

    path = nx.shortest_path(G, source=origin, target=destination, weight="weight")
    total_distance = nx.shortest_path_length(G, source=origin, target=destination, weight="weight")

    legs = []
    for u, v in zip(path[:-1], path[1:]):
        edge = G[u][v]
        legs.append({
            "from": u,
            "to": v,
            "from_city": G.nodes[u]["city"],
            "to_city": G.nodes[v]["city"],
            "distance_km": edge["distance_km"],
            "n_airlines": edge["n_airlines"],
        })

    return {
        "path": path,
        "total_distance_km": total_distance,
        "hops": len(path) - 1,
        "legs": legs,
    }


def print_result(result: dict):
    print(f"\nShortest route: {' -> '.join(result['path'])}")
    print(f"Total distance: {result['total_distance_km']:.1f} km")
    print(f"Hops: {result['hops']}")
    print("\nLeg-by-leg breakdown:")
    for leg in result["legs"]:
        print(f"  {leg['from']} ({leg['from_city']}) -> {leg['to']} ({leg['to_city']}): "
              f"{leg['distance_km']:.1f} km, {leg['n_airlines']} airline(s)")


def main():
    parser = argparse.ArgumentParser(description="Find shortest route between two airports (IATA codes).")
    parser.add_argument("origin", nargs="?", default="DEL", help="Origin IATA code (default: DEL)")
    parser.add_argument("destination", nargs="?", default="JFK", help="Destination IATA code (default: JFK)")
    parser.add_argument("--data-dir", default="data", help="Directory containing airports.dat / routes.dat")
    args = parser.parse_args()

    print("Loading and cleaning data...")
    airports, routes = load_clean_dataset(args.data_dir)
    print("Building graph...")
    G = build_graph(airports, routes)

    try:
        result = shortest_route(G, args.origin, args.destination)
        print_result(result)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except nx.NetworkXNoPath:
        print(f"No route exists between {args.origin} and {args.destination}.")
        sys.exit(1)


if __name__ == "__main__":
    main()
