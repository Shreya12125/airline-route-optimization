# Airline Route Network Optimization

Shortest-path routing and minimal-spanning-tree network design over the
OpenFlights global airport/route dataset.

## Project Structure

```
airline-route-optimization/
├── data/
│   ├── airports.dat          # OpenFlights airports table (you provide this)
│   └── routes.dat            # OpenFlights routes table (you provide this)
├── src/
│   ├── data_prep.py          # Step 1: load, clean, compute haversine distances
│   ├── graph_builder.py      # Step 2: build the directed NetworkX graph
│   └── shortest_path.py      # Step 3: Dijkstra shortest-route solver
├── outputs/                  # Generated CSVs / graph files land here
├── notebooks/                # (optional) exploratory notebooks
├── main.py                   # Runs Steps 1-3 end-to-end
├── requirements.txt
└── README.md
```

## Setup

```bash
# from the project root
pip install -r requirements.txt
```

Place your `airports.dat` and `routes.dat` files inside the `data/` folder
(they're already there if you copied this project as-is).

## Running

**Run everything (Steps 1-3) with one command:**
```bash
python main.py DEL JFK
```
(Origin/destination default to `DEL JFK` if omitted.)

**Or run each step individually, from the project root:**

```bash
# Step 1 - clean the data, compute route distances
python src/data_prep.py

# Step 2 - build the graph, print network stats
python src/graph_builder.py

# Step 3 - shortest path between two airports (IATA codes)
python src/shortest_path.py BLR SFO
python src/shortest_path.py COK IXC
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

## Notes / Gotchas

- **Airports without an IATA code or coordinates are dropped** — this
  removes a small number of unlinked airports but keeps every route that
  matters.
- **Distance is airline-independent** — multiple airlines flying the same
  src→dst pair are collapsed into a single graph edge; distance is the
  same regardless of carrier, so we keep it once and just count airlines.
- **The graph is directed** — a route from A→B doesn't guarantee B→A
  exists in the data (though in practice most do). `shortest_path.py`
  respects this directionality.
- If `shortest_path.py` raises `NetworkXNoPath`, the two airports fall in
  different weakly-connected components (see Step 2 stats — about 53% of
  airports are in the single largest component; small regional airports
  can be isolated).

## Next Steps (Step 4 onward)

- `src/mst_builder.py` — minimal spanning tree over a user-chosen airport
  subset (e.g. Indian metros), using shortest-path distances as edge
  weights for pairs without a direct route.
- `src/max_flow.py` (stretch) — max-flow between two hubs using
  `n_airlines` as a capacity proxy.
- `app.py` — Streamlit demo with map visualization (Plotly/Folium).
