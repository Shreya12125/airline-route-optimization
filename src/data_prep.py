"""
Step 1: Data Preparation
-------------------------
Loads OpenFlights airports.dat and routes.dat, cleans nulls ('\\N'),
and computes the great-circle (haversine) distance for every route.

OpenFlights files ship with NO header row, so column names are
defined manually below, per the official schema:
https://openflights.org/data.php
"""

import math
import os
import pandas as pd

# ---------------------------------------------------------------------
# Column schemas (OpenFlights official format)
# ---------------------------------------------------------------------
AIRPORT_COLS = [
    "airport_id", "name", "city", "country", "iata", "icao",
    "latitude", "longitude", "altitude", "timezone", "dst",
    "tz_database_timezone", "type", "source"
]

ROUTE_COLS = [
    "airline", "airline_id", "src_airport", "src_airport_id",
    "dst_airport", "dst_airport_id", "codeshare", "stops", "equipment"
]


def load_airports(path: str) -> pd.DataFrame:
    """Load airports.dat into a cleaned DataFrame."""
    df = pd.read_csv(
        path, header=None, names=AIRPORT_COLS,
        na_values=["\\N"], quotechar='"', encoding="utf-8"
    )
    # Keep only airports with valid IATA codes and coordinates -
    # these are the ones routes.dat actually references.
    df = df.dropna(subset=["iata", "latitude", "longitude"])
    df = df[df["iata"].str.len() == 3]
    df = df.drop_duplicates(subset=["iata"], keep="first")
    df["latitude"] = df["latitude"].astype(float)
    df["longitude"] = df["longitude"].astype(float)
    return df.reset_index(drop=True)


def load_routes(path: str) -> pd.DataFrame:
    """Load routes.dat into a cleaned DataFrame."""
    df = pd.read_csv(
        path, header=None, names=ROUTE_COLS,
        na_values=["\\N"], quotechar='"', encoding="utf-8"
    )
    # Drop routes missing a source or destination IATA code
    df = df.dropna(subset=["src_airport", "dst_airport"])
    # Drop self-loop routes (shouldn't exist, but just in case)
    df = df[df["src_airport"] != df["dst_airport"]]
    df = df.drop_duplicates(subset=["src_airport", "dst_airport", "airline"])
    return df.reset_index(drop=True)


def haversine(lat1, lon1, lat2, lon2) -> float:
    """
    Great-circle distance between two points on Earth, in kilometers.
    """
    R = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def build_routes_with_distance(routes: pd.DataFrame, airports: pd.DataFrame) -> pd.DataFrame:
    """
    Merge routes with airport coordinates and compute haversine
    distance (km) for every route. Routes referencing airports not
    present in the cleaned airports table are dropped.
    """
    airport_lookup = airports.set_index("iata")[["latitude", "longitude", "name", "city", "country"]]

    merged = routes.merge(
        airport_lookup, left_on="src_airport", right_index=True, how="inner"
    ).rename(columns={
        "latitude": "src_lat", "longitude": "src_lon",
        "name": "src_name", "city": "src_city", "country": "src_country"
    })

    merged = merged.merge(
        airport_lookup, left_on="dst_airport", right_index=True, how="inner"
    ).rename(columns={
        "latitude": "dst_lat", "longitude": "dst_lon",
        "name": "dst_name", "city": "dst_city", "country": "dst_country"
    })

    merged["distance_km"] = merged.apply(
        lambda r: haversine(r["src_lat"], r["src_lon"], r["dst_lat"], r["dst_lon"]),
        axis=1
    )

    return merged.reset_index(drop=True)


def load_clean_dataset(data_dir: str = "data"):
    """
    Convenience wrapper: loads airports + routes, cleans both,
    and returns (airports_df, routes_with_distance_df).
    """
    airports_path = os.path.join(data_dir, "airports.dat")
    routes_path = os.path.join(data_dir, "routes.dat")

    airports = load_airports(airports_path)
    routes = load_routes(routes_path)
    routes_with_dist = build_routes_with_distance(routes, airports)

    return airports, routes_with_dist


if __name__ == "__main__":
    airports, routes = load_clean_dataset("data")

    print(f"Cleaned airports: {len(airports):,}")
    print(f"Cleaned routes (with valid distance): {len(routes):,}")
    print(f"Countries covered: {airports['country'].nunique():,}")
    print(f"Distance range (km): {routes['distance_km'].min():.1f} - {routes['distance_km'].max():.1f}")
    print(f"Average route distance (km): {routes['distance_km'].mean():.1f}")

    os.makedirs("outputs", exist_ok=True)
    airports.to_csv("outputs/airports_clean.csv", index=False)
    routes.to_csv("outputs/routes_with_distance.csv", index=False)
    print("\nSaved cleaned data to outputs/airports_clean.csv and outputs/routes_with_distance.csv")
