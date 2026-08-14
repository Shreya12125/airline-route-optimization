"""
Step 2: Graph Construction
----------------------------
Builds a directed NetworkX graph from the cleaned airports/routes data.

Nodes  = airports (IATA code), with lat/long/name/city/country as attributes.
Edges  = routes, with distance_km as weight and airline count as an attribute
         (multiple airlines flying src->dst are collapsed into ONE edge,
         keeping the minimum distance and counting distinct airlines --
         this airline count later serves as a capacity proxy for max-flow).
"""

import os
import networkx as nx

from data_prep import load_clean_dataset


def build_graph(airports_df, routes_df) -> nx.DiGraph:
    """Construct a directed, weighted airport route graph."""
    G = nx.DiGraph()

    # Add nodes with attributes
    for _, row in airports_df.iterrows():
        G.add_node(
            row["iata"],
            name=row["name"],
            city=row["city"],
            country=row["country"],
            latitude=row["latitude"],
            longitude=row["longitude"],
        )

    # Collapse multiple airline entries per src-dst pair into a single
    # edge: weight = distance (same regardless of airline), airlines =
    # count of distinct carriers serving that route.
    grouped = routes_df.groupby(["src_airport", "dst_airport"]).agg(
        distance_km=("distance_km", "first"),
        n_airlines=("airline", "nunique"),
    ).reset_index()

    for _, row in grouped.iterrows():
        G.add_edge(
            row["src_airport"], row["dst_airport"],
            weight=row["distance_km"],
            distance_km=row["distance_km"],
            n_airlines=row["n_airlines"],
        )

    return G


def graph_stats(G: nx.DiGraph):
    """Print key summary statistics about the network."""
    print(f"Nodes (airports in graph): {G.number_of_nodes():,}")
    print(f"Edges (unique routes): {G.number_of_edges():,}")

    degrees = sorted(G.degree(), key=lambda x: x[1], reverse=True)
    print("\nTop 10 busiest hubs (by total degree = in+out routes):")
    for iata, deg in degrees[:10]:
        name = G.nodes[iata].get("name", "?")
        city = G.nodes[iata].get("city", "?")
        print(f"  {iata:4s}  {city:25s} {name:35s} degree={deg}")

    countries = set(nx.get_node_attributes(G, "country").values())
    print(f"\nCountries covered: {len(countries)}")

    weakly_connected = nx.number_weakly_connected_components(G)
    largest_wcc = max(nx.weakly_connected_components(G), key=len)
    print(f"Weakly connected components: {weakly_connected}")
    print(f"Largest connected component size: {len(largest_wcc)} airports "
          f"({len(largest_wcc)/G.number_of_nodes()*100:.1f}% of all airports)")


if __name__ == "__main__":
    airports, routes = load_clean_dataset("data")
    G = build_graph(airports, routes)
    graph_stats(G)

    os.makedirs("outputs", exist_ok=True)
    nx.write_gml(G, "outputs/route_graph.gml")
    print("\nSaved graph to outputs/route_graph.gml (reload anytime with nx.read_gml)")
