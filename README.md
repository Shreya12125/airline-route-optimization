# Airline Route Network Optimization

Shortest-path routing and minimal-spanning-tree network design over the
OpenFlights global airport/route dataset.

## Project Structure

```
airline-route-optimization/
├── data/
│   ├── airports.dat          # OpenFlights airports table
│   └── routes.dat            # OpenFlights routes table
├── src/
│   ├── data_prep.py          # Step 1: load, clean, compute haversine distances
│   ├── graph_builder.py      # Step 2: build the directed NetworkX graph
│   ├── shortest_path.py      # Step 3: Dijkstra shortest-route solver
│   └── mst_builder.py        # Step 4: minimum spanning tree over a chosen airport set
├── outputs/                  # Generated CSVs / graph files land here
├── notebooks/                # (optional) exploratory notebooks
├── main.py                   # Runs Steps 1-3 end-to-end
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
```

Place your `airports.dat` and `routes.dat` files inside the `data/` folder
(they're already there if you copied this project as-is).

## Running

**Run Steps 1-3 with one command:**
```bash
python main.py DEL JFK
```

**Or run each step individually, from the project root:**

```bash
# Step 1 - clean the data, compute route distances
python src/data_prep.py

# Step 2 - build the graph, print network stats
python src/graph_builder.py

# Step 3 - shortest path between two airports (IATA codes)
python src/shortest_path.py BLR SFO
python src/shortest_path.py COK IXC

# Step 4 - minimum spanning tree over a set of airports
python src/mst_builder.py                              # default: major Indian metros
python src/mst_builder.py DEL JFK LHR CDG DXB SIN       # custom set via CLI args
```

## What Each Step Does

**Step 1 — `data_prep.py`**
Loads the raw `.dat` files (no header row, `\N` = null per OpenFlights
convention), drops routes/airports with missing IATA codes or coordinates,
and computes the great-circle (haversine) distance in km for every route.
Outputs `outputs/airports_clean.csv` and `outputs/routes_with_distance.csv`.

**Step 2 — `graph_builder.py`**
Builds a directed, weighted `networkx.DiGraph`: nodes are airports (IATA
code + name/city/country/coords), edges are routes (weight = distance_km,
plus a count of distinct airlines serving that route — this doubles as a
capacity proxy for a later max-flow extension). Prints busiest hubs,
country coverage, and connected-component stats. Saves `outputs/route_graph.gml`.

**Step 3 — `shortest_path.py`**
Runs Dijkstra's algorithm between a chosen origin/destination IATA code
pair, returning the full path, total distance, hop count, and a
leg-by-leg breakdown (including which airlines fly each leg).

**Step 4 — `mst_builder.py`**
Takes a set of airports (default: major Indian metros, or pass your own
via CLI args) and finds the minimum-cost set of links connecting all of
them. Since a direct route may not exist between every pair, it first
builds a complete graph over just the chosen airports using shortest-path
distance (through the full network) as each pairwise edge weight, then
runs Kruskal's algorithm on that complete graph. Reports each MST edge,
whether it's a direct route or routed via an intermediate airport, and
skips/warns on invalid or unreachable codes. Saves `outputs/mst_result.gml`.

## Notes / Gotchas

- **Airports without an IATA code or coordinates are dropped.**
- **Distance is airline-independent** — multiple airlines flying the same
  src→dst pair are collapsed into a single graph edge.
- **The graph is directed** — `shortest_path.py` respects this.
- If `shortest_path.py` raises `NetworkXNoPath`, the two airports fall in
  different weakly-connected components (~53% of airports are in the
  single largest component).
- `mst_builder.py` builds an *undirected* complete graph over the chosen
  subset since MST is inherently undirected — pairwise weights use the
  shortest directed path distance in either direction.

## Next Steps

- `src/max_flow.py` (stretch) — max-flow between two hubs using
  `n_airlines` as a capacity proxy.
- `app.py` — Streamlit demo with map visualization (Plotly/Folium).
