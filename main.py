"""
Entry point: runs Steps 1-3 end-to-end.
  Step 1: load & clean data, compute route distances
  Step 2: build the directed route graph, print summary stats
  Step 3: run an example shortest-path query

Usage:
    python main.py                     # uses default DEL -> JFK example
    python main.py BLR SFO             # custom origin/destination
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from data_prep import load_clean_dataset
from graph_builder import build_graph, graph_stats
from shortest_path import shortest_route, print_result

import networkx as nx


def main():
    origin = sys.argv[1] if len(sys.argv) > 1 else "DEL"
    destination = sys.argv[2] if len(sys.argv) > 2 else "JFK"

    print("=" * 60)
    print("STEP 1: Data Preparation")
    print("=" * 60)
    airports, routes = load_clean_dataset("data")
    print(f"Cleaned airports: {len(airports):,}")
    print(f"Cleaned routes (with valid distance): {len(routes):,}")

    print("\n" + "=" * 60)
    print("STEP 2: Graph Construction")
    print("=" * 60)
    G = build_graph(airports, routes)
    graph_stats(G)

    print("\n" + "=" * 60)
    print(f"STEP 3: Shortest Route ({origin} -> {destination})")
    print("=" * 60)
    try:
        result = shortest_route(G, origin, destination)
        print_result(result)
    except ValueError as e:
        print(f"Error: {e}")
    except nx.NetworkXNoPath:
        print(f"No route exists between {origin} and {destination}.")

    os.makedirs("outputs", exist_ok=True)
    airports.to_csv("outputs/airports_clean.csv", index=False)
    routes.to_csv("outputs/routes_with_distance.csv", index=False)
    nx.write_gml(G, "outputs/route_graph.gml")
    print("\nAll outputs saved to outputs/")


if __name__ == "__main__":
    main()
