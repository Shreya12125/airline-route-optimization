"""
Step 6: Network Statistics
------------------------------
Computes summary statistics for the airline route network, reusing the
existing graph-building pipeline (data_prep.load_clean_dataset +
graph_builder.build_graph) rather than recomputing anything from scratch.

Produces a stats dict, a Markdown report (outputs/network_summary.md),
and a JSON dump (outputs/network_summary.json) so the Streamlit app can
load precomputed stats without rebuilding the graph.
"""

import json
import os
import statistics

import networkx as nx

from data_prep import load_clean_dataset
from graph_builder import build_graph


def compute_stats(G: nx.DiGraph, routes_df) -> dict:
    """Compute all network statistics from the built graph."""
    stats = {}

    # --- Airports ---
    served_nodes = [n for n, d in G.degree() if d > 0]
    stats["total_airports"] = G.number_of_nodes()
    stats["served_airports"] = len(served_nodes)

    # --- Routes / airlines ---
    stats["total_unique_routes"] = G.number_of_edges()
    stats["total_raw_route_rows"] = len(routes_df)
    stats["total_distinct_airlines"] = int(routes_df["airline"].nunique())

    # --- Busiest hubs ---
    def top_by(deg_view, n=10):
        ranked = sorted(deg_view, key=lambda x: x[1], reverse=True)[:n]
        return [
            {
                "iata": iata,
                "city": G.nodes[iata].get("city", "?"),
                "country": G.nodes[iata].get("country", "?"),
                "name": G.nodes[iata].get("name", "?"),
                "degree": deg,
            }
            for iata, deg in ranked
        ]

    stats["top_hubs_total_degree"] = top_by(G.degree())
    stats["top_hubs_in_degree"] = top_by(G.in_degree())
    stats["top_hubs_out_degree"] = top_by(G.out_degree())

    # --- Country coverage ---
    country_counts = {}
    for _, data in G.nodes(data=True):
        c = data.get("country", "?")
        country_counts[c] = country_counts.get(c, 0) + 1
    stats["distinct_country_count"] = len(country_counts)
    stats["top_countries"] = [
        {"country": c, "airport_count": n}
        for c, n in sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    # --- Route distance distribution ---
    distances = [d["distance_km"] for _, _, d in G.edges(data=True)]
    distances_sorted = sorted(distances)
    stats["route_distance_km"] = {
        "min": distances_sorted[0],
        "median": statistics.median(distances_sorted),
        "mean": statistics.fmean(distances_sorted),
        "p90": distances_sorted[int(0.9 * (len(distances_sorted) - 1))],
        "max": distances_sorted[-1],
        "values": distances,
    }

    # --- Most-connected city pairs by n_airlines ---
    top_pairs = sorted(
        G.edges(data=True), key=lambda e: e[2]["n_airlines"], reverse=True
    )[:10]
    stats["top_city_pairs_by_airlines"] = [
        {
            "src": u,
            "dst": v,
            "src_city": G.nodes[u].get("city", "?"),
            "dst_city": G.nodes[v].get("city", "?"),
            "n_airlines": d["n_airlines"],
        }
        for u, v, d in top_pairs
    ]

    # --- Connected components ---
    total_airports = stats["total_airports"]
    served_airports = stats["served_airports"] or 1  # avoid div by zero

    wcc = list(nx.weakly_connected_components(G))
    largest_wcc = max(wcc, key=len)
    scc = list(nx.strongly_connected_components(G))
    largest_scc = max(scc, key=len)

    stats["weakly_connected_components"] = {
        "count": len(wcc),
        "largest_size": len(largest_wcc),
        "largest_pct_of_all": len(largest_wcc) / total_airports * 100,
        "largest_pct_of_served": len(largest_wcc) / served_airports * 100,
    }
    stats["strongly_connected_components"] = {
        "count": len(scc),
        "largest_size": len(largest_scc),
        "largest_pct_of_all": len(largest_scc) / total_airports * 100,
        "largest_pct_of_served": len(largest_scc) / served_airports * 100,
    }

    return stats


def generate_summary_markdown(stats: dict) -> str:
    """Format the stats dict as a clean Markdown report."""
    lines = []
    a = lines.append

    a("# Airline Route Network — Summary Statistics\n")

    a("## Airports\n")
    a(f"- **Total airports:** {stats['total_airports']:,}")
    a(f"- **Served airports (degree > 0):** {stats['served_airports']:,}\n")

    a("## Routes & Airlines\n")
    a(f"- **Total unique routes (edges):** {stats['total_unique_routes']:,}")
    a(f"- **Total raw route rows (before collapse):** {stats['total_raw_route_rows']:,}")
    a(f"- **Total distinct airlines:** {stats['total_distinct_airlines']:,}\n")

    def hub_table(title, hubs):
        a(f"### {title}\n")
        a("| Rank | IATA | City | Country | Degree |")
        a("|---|---|---|---|---|")
        for i, h in enumerate(hubs, start=1):
            a(f"| {i} | {h['iata']} | {h['city']} | {h['country']} | {h['degree']} |")
        a("")

    a("## Top 10 Busiest Hubs\n")
    hub_table("By Total Degree", stats["top_hubs_total_degree"])
    hub_table("By In-Degree", stats["top_hubs_in_degree"])
    hub_table("By Out-Degree", stats["top_hubs_out_degree"])

    a("## Country Coverage\n")
    a(f"- **Distinct countries served:** {stats['distinct_country_count']:,}\n")
    a("| Rank | Country | Airport Count |")
    a("|---|---|---|")
    for i, c in enumerate(stats["top_countries"], start=1):
        a(f"| {i} | {c['country']} | {c['airport_count']} |")
    a("")

    d = stats["route_distance_km"]
    a("## Route Distance Distribution (km)\n")
    a("| Min | Median | Mean | P90 | Max |")
    a("|---|---|---|---|---|")
    a(f"| {d['min']:.1f} | {d['median']:.1f} | {d['mean']:.1f} | {d['p90']:.1f} | {d['max']:.1f} |\n")

    a("## Top 10 Most-Connected City Pairs (by number of airlines)\n")
    a("| Rank | Src | Dst | Src City | Dst City | Airlines |")
    a("|---|---|---|---|---|---|")
    for i, p in enumerate(stats["top_city_pairs_by_airlines"], start=1):
        a(f"| {i} | {p['src']} | {p['dst']} | {p['src_city']} | {p['dst_city']} | {p['n_airlines']} |")
    a("")

    wcc = stats["weakly_connected_components"]
    scc = stats["strongly_connected_components"]
    a("## Connectivity\n")
    a("| Metric | Count | Largest Size | % of All Airports | % of Served Airports |")
    a("|---|---|---|---|---|")
    a(f"| Weakly connected components | {wcc['count']:,} | {wcc['largest_size']:,} | "
      f"{wcc['largest_pct_of_all']:.1f}% | {wcc['largest_pct_of_served']:.1f}% |")
    a(f"| Strongly connected components | {scc['count']:,} | {scc['largest_size']:,} | "
      f"{scc['largest_pct_of_all']:.1f}% | {scc['largest_pct_of_served']:.1f}% |")
    a("")
    a("*Airports with zero routes each form their own singleton component, "
      "which is why the \"% of all airports\" and \"% of served airports\" "
      "columns differ.*\n")

    return "\n".join(lines)


def main():
    print("Loading and cleaning data...")
    airports, routes = load_clean_dataset("data")
    print("Building graph...")
    G = build_graph(airports, routes)

    print("Computing network statistics...")
    stats = compute_stats(G, routes)

    md = generate_summary_markdown(stats)

    os.makedirs("outputs", exist_ok=True)
    md_path = os.path.join("outputs", "network_summary.md")
    json_path = os.path.join("outputs", "network_summary.json")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    md_size = os.path.getsize(md_path)
    json_size = os.path.getsize(json_path)

    print(f"\nWrote {md_path} ({md_size:,} bytes)")
    print(f"Wrote {json_path} ({json_size:,} bytes)")
    print(f"\nTotal airports: {stats['total_airports']:,} "
          f"({stats['served_airports']:,} served)")
    print(f"Total unique routes: {stats['total_unique_routes']:,}")
    print(f"Total distinct airlines: {stats['total_distinct_airlines']:,}")


if __name__ == "__main__":
    main()
