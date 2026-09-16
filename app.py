"""
Step 7: Streamlit Demo
--------------------------
Interactive demo over the airline route network: shortest-path finder,
MST builder over a chosen set of airports, and a sidebar of precomputed
network statistics (from outputs/network_summary.json).

Run with:
    streamlit run app.py
"""

import json
import os
import sys

import networkx as nx
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from data_prep import load_clean_dataset
from graph_builder import build_graph
from shortest_path import shortest_route
from mst_builder import DEFAULT_AIRPORTS, build_complete_subgraph, compute_mst


st.set_page_config(page_title="Airline Route Optimization", layout="wide")


@st.cache_resource
def get_graph():
    airports, routes = load_clean_dataset("data")
    return build_graph(airports, routes)


@st.cache_data
def get_airport_options(_G):
    options = []
    for iata, data in _G.nodes(data=True):
        options.append((iata, f"{iata} - {data.get('city', '?')}, {data.get('country', '?')}"))
    return sorted(options, key=lambda x: x[1])


def airport_map_figure(nodes: list, edges: list, G: nx.DiGraph, title: str) -> go.Figure:
    """nodes: list of IATA codes in visual order. edges: list of (u, v) pairs to draw."""
    fig = go.Figure()

    for u, v in edges:
        fig.add_trace(go.Scattergeo(
            lon=[G.nodes[u]["longitude"], G.nodes[v]["longitude"]],
            lat=[G.nodes[u]["latitude"], G.nodes[v]["latitude"]],
            mode="lines",
            line=dict(width=2, color="royalblue"),
            showlegend=False,
            hoverinfo="skip",
        ))

    fig.add_trace(go.Scattergeo(
        lon=[G.nodes[n]["longitude"] for n in nodes],
        lat=[G.nodes[n]["latitude"] for n in nodes],
        mode="markers+text",
        marker=dict(size=8, color="crimson"),
        text=nodes,
        textposition="top center",
        hovertext=[f"{n} - {G.nodes[n].get('city', '?')}" for n in nodes],
        hoverinfo="text",
        showlegend=False,
    ))

    fig.update_layout(
        title=title,
        geo=dict(
            projection_type="natural earth",
            showland=True,
            landcolor="rgb(240, 240, 240)",
            countrycolor="rgb(200, 200, 200)",
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        height=500,
    )
    return fig


G = get_graph()
airport_options = get_airport_options(G)
option_labels = [label for _, label in airport_options]
label_to_iata = {label: iata for iata, label in airport_options}

st.title("Airline Route Network Optimization")

tab1, tab2 = st.tabs(["Shortest Path", "Minimum Spanning Tree"])

with tab1:
    st.header("Shortest Route Finder")
    col1, col2 = st.columns(2)
    with col1:
        origin_label = st.selectbox("Origin", option_labels, index=0, key="sp_origin")
    with col2:
        destination_label = st.selectbox("Destination", option_labels, index=1, key="sp_destination")

    if st.button("Find Shortest Route"):
        origin = label_to_iata[origin_label]
        destination = label_to_iata[destination_label]
        try:
            result = shortest_route(G, origin, destination)
            st.success(
                f"Total distance: {result['total_distance_km']:.1f} km  |  "
                f"Hops: {result['hops']}"
            )
            st.subheader("Leg-by-leg breakdown")
            st.table([
                {
                    "From": f"{leg['from']} ({leg['from_city']})",
                    "To": f"{leg['to']} ({leg['to_city']})",
                    "Distance (km)": f"{leg['distance_km']:.1f}",
                    "Airlines": leg["n_airlines"],
                }
                for leg in result["legs"]
            ])
            fig = airport_map_figure(
                result["path"],
                list(zip(result["path"][:-1], result["path"][1:])),
                G,
                f"{origin} -> {destination}",
            )
            st.plotly_chart(fig, use_container_width=True)
        except ValueError as e:
            st.error(str(e))
        except nx.NetworkXNoPath:
            st.warning(f"No route exists between {origin} and {destination}.")

with tab2:
    st.header("Minimum Spanning Tree")
    default_labels = [
        label for iata, label in airport_options if iata in DEFAULT_AIRPORTS
    ]
    selected_labels = st.multiselect(
        "Select airports to connect (at least 2)",
        option_labels,
        default=default_labels,
        key="mst_airports",
    )

    if st.button("Compute MST", disabled=len(selected_labels) < 2):
        selected_iatas = [label_to_iata[label] for label in selected_labels]

        warnings = []
        import io
        import contextlib

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            H = build_complete_subgraph(G, selected_iatas)
        captured = buf.getvalue()
        for line in captured.splitlines():
            if line.strip():
                warnings.append(line)

        for w in warnings:
            st.warning(w)

        if H.number_of_nodes() >= 2:
            mst = compute_mst(H)
            total = sum(d["weight"] for _, _, d in mst.edges(data=True))
            st.success(
                f"MST connects {mst.number_of_nodes()} airports with "
                f"{mst.number_of_edges()} links, total distance {total:.1f} km"
            )
            st.subheader("MST edges")
            st.table([
                {
                    "From": f"{u} ({G.nodes[u]['city']})",
                    "To": f"{v} ({G.nodes[v]['city']})",
                    "Distance (km)": f"{d['weight']:.1f}",
                    "Route": "direct" if len(d.get("via", [u, v])) == 2
                             else f"via {' -> '.join(d['via'][1:-1])}",
                }
                for u, v, d in sorted(mst.edges(data=True), key=lambda e: e[2]["weight"])
            ])
            fig = airport_map_figure(
                list(mst.nodes()), list(mst.edges()), G, "Minimum Spanning Tree"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Not enough valid, connected airports to build an MST.")

st.sidebar.header("Network Statistics")

stats_path = os.path.join("outputs", "network_summary.json")
if not os.path.exists(stats_path):
    st.sidebar.warning(
        "Run `python src/network_stats.py` first to generate "
        "outputs/network_summary.json."
    )
else:
    with open(stats_path) as f:
        stats = json.load(f)

    st.sidebar.metric("Total airports", f"{stats['total_airports']:,}")
    st.sidebar.metric("Total routes", f"{stats['total_unique_routes']:,}")
    st.sidebar.metric("Total airlines", f"{stats['total_distinct_airlines']:,}")
    st.sidebar.metric("Countries covered", f"{stats['distinct_country_count']:,}")

    st.sidebar.subheader("Top 5 Hubs")
    for hub in stats["top_hubs_total_degree"][:5]:
        st.sidebar.write(f"**{hub['iata']}** ({hub['city']}) — degree {hub['degree']}")

    st.sidebar.subheader("Route Distance Distribution")
    dist_fig = go.Figure(data=[go.Histogram(x=stats["route_distance_km"]["values"], nbinsx=40)])
    dist_fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=250,
        xaxis_title="Distance (km)",
        yaxis_title="Routes",
    )
    st.sidebar.plotly_chart(dist_fig, use_container_width=True)
