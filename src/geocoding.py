"""
Geocoding services using Nominatim and Overpass API (OpenStreetMap)
"""

import time
from typing import Optional, List
import requests
from shapely.geometry import Point, Polygon, shape
from src.config import config


class GeocodingResult:
    """Result from geocoding a location"""

    def __init__(self, data: dict):
        self.place_id = data.get("place_id")
        self.osm_type = data.get("osm_type")
        self.osm_id = data.get("osm_id")
        self.lat = float(data.get("lat", 0))
        self.lon = float(data.get("lon", 0))
        self.display_name = data.get("display_name", "")
        self.place_type = data.get("type", "unknown")
        self.importance = float(data.get("importance", 0))
        self.geojson = data.get("geojson")
        self.boundingbox = data.get("boundingbox")

    @property
    def coordinates(self) -> tuple[float, float]:
        """Returns (lon, lat) tuple"""
        return (self.lon, self.lat)

    @property
    def point(self) -> Point:
        """Returns Shapely Point"""
        return Point(self.lon, self.lat)

    @property
    def has_polygon(self) -> bool:
        """Check if result includes a polygon"""
        return self.geojson is not None and self.geojson.get("type") in [
            "Polygon",
            "MultiPolygon",
        ]

    def get_polygon(self) -> Optional[Polygon]:
        """
        Extract polygon from geojson if available

        Returns:
            Shapely Polygon or None
        """
        if not self.has_polygon:
            return None

        try:
            return shape(self.geojson)
        except Exception as e:
            print(f"Error converting geojson to polygon: {e}")
            return None

    def __repr__(self):
        return (
            f"GeocodingResult(name='{self.display_name}', "
            f"type='{self.place_type}', "
            f"coords=({self.lat:.4f}, {self.lon:.4f}), "
            f"has_polygon={self.has_polygon})"
        )


class NominatimClient:
    """Client for Nominatim geocoding API"""

    def __init__(self):
        self.base_url = config.NOMINATIM_BASE_URL
        self.user_agent = config.NOMINATIM_USER_AGENT
        self.delay = config.NOMINATIM_DELAY
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting (Nominatim policy: max 1 request per second)"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request_time = time.time()

    def search(
        self,
        query: str,
        limit: int = 5,
        country_codes: Optional[List[str]] = None,
        polygon_geojson: bool = True,
    ) -> List[GeocodingResult]:
        """
        Search for a location by name

        Args:
            query: Location name to search for
            limit: Maximum number of results
            country_codes: List of country codes to limit search (e.g., ["by", "pl"])
            polygon_geojson: Include polygon geometry if available

        Returns:
            List of GeocodingResult objects
        """
        self._rate_limit()

        params = {
            "q": query,
            "format": "json",
            "addressdetails": 1,
            "limit": limit,
            "polygon_geojson": 1 if polygon_geojson else 0,
        }

        if country_codes:
            params["countrycodes"] = ",".join(country_codes)

        headers = {"User-Agent": self.user_agent}

        try:
            response = requests.get(
                f"{self.base_url}/search", params=params, headers=headers, timeout=10
            )
            response.raise_for_status()

            data = response.json()
            return [GeocodingResult(item) for item in data]

        except requests.exceptions.RequestException as e:
            print(f"Nominatim API error: {e}")
            return []

    def reverse(self, lat: float, lon: float) -> Optional[GeocodingResult]:
        """
        Reverse geocode coordinates to location

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            GeocodingResult or None
        """
        self._rate_limit()

        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "addressdetails": 1,
            "polygon_geojson": 1,
        }

        headers = {"User-Agent": self.user_agent}

        try:
            response = requests.get(
                f"{self.base_url}/reverse", params=params, headers=headers, timeout=10
            )
            response.raise_for_status()

            data = response.json()
            return GeocodingResult(data)

        except requests.exceptions.RequestException as e:
            print(f"Nominatim reverse API error: {e}")
            return None

    def lookup(self, osm_type: str, osm_id: int) -> Optional[GeocodingResult]:
        """
        Look up a specific OSM object

        Args:
            osm_type: Type of OSM object (node, way, relation)
            osm_id: OSM ID

        Returns:
            GeocodingResult or None
        """
        self._rate_limit()

        params = {
            "osm_ids": f"{osm_type[0].upper()}{osm_id}",
            "format": "json",
            "addressdetails": 1,
            "polygon_geojson": 1,
        }

        headers = {"User-Agent": self.user_agent}

        try:
            response = requests.get(
                f"{self.base_url}/lookup", params=params, headers=headers, timeout=10
            )
            response.raise_for_status()

            data = response.json()
            if data:
                return GeocodingResult(data[0])
            return None

        except requests.exceptions.RequestException as e:
            print(f"Nominatim lookup API error: {e}")
            return None


class OverpassClient:
    """Client for Overpass API (advanced OSM queries)"""

    def __init__(self):
        self.base_url = config.OVERPASS_BASE_URL

    def query(self, overpass_query: str, timeout: int = 25) -> Optional[dict]:
        """
        Execute an Overpass QL query

        Args:
            overpass_query: Overpass QL query string
            timeout: Query timeout in seconds

        Returns:
            JSON response or None
        """
        try:
            response = requests.post(
                self.base_url,
                data={"data": overpass_query},
                timeout=timeout + 5,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Overpass API error: {e}")
            return None

    def get_boundary(
        self, name: str, lat: float, lon: float, radius_m: int = 5000
    ) -> Optional[dict]:
        """
        Get boundary polygon for a named area

        Args:
            name: Name of the area
            lat: Approximate latitude
            lon: Approximate longitude
            radius_m: Search radius in meters

        Returns:
            GeoJSON dict or None
        """
        query = f"""
        [out:json][timeout:25];
        (
          relation["name"="{name}"]["boundary"="administrative"](around:{radius_m},{lat},{lon});
          way["name"="{name}"]["boundary"="administrative"](around:{radius_m},{lat},{lon});
        );
        out geom;
        """

        result = self.query(query)

        if not result or not result.get("elements"):
            return None

        elements = result.get("elements", [])
        if elements:
            return self._convert_to_geojson(elements[0])

        return None

    def _convert_to_geojson(self, element: dict) -> Optional[dict]:
        """Convert Overpass element to GeoJSON"""
        if element.get("type") == "way" and element.get("geometry"):
            coords = [[node["lon"], node["lat"]] for node in element["geometry"]]
            if coords[0] != coords[-1]:
                coords.append(coords[0])

            return {
                "type": "Polygon",
                "coordinates": [coords]
            }

        return None


# Convenience functions
def geocode_location(
    query: str, limit: int = 5, country_codes: Optional[List[str]] = None
) -> List[GeocodingResult]:
    """
    Geocode a location by name

    Args:
        query: Location name
        limit: Max results
        country_codes: Limit to specific countries

    Returns:
        List of results
    """
    client = NominatimClient()
    return client.search(query, limit=limit, country_codes=country_codes)


def reverse_geocode(lat: float, lon: float) -> Optional[GeocodingResult]:
    """
    Reverse geocode coordinates

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        GeocodingResult or None
    """
    client = NominatimClient()
    return client.reverse(lat, lon)


if __name__ == "__main__":
    print("Testing Geocoding Module")
    print("=" * 60)

    print("\n1. Searching for 'Minsk, Belarus'...")
    results = geocode_location("Minsk, Belarus", limit=3)

    if results:
        print(f"   Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result}")
            print(f"      Place ID: {result.place_id}")
            print(f"      Importance: {result.importance}")
            if result.has_polygon:
                poly = result.get_polygon()
                if poly:
                    print(f"      Polygon area: {poly.area:.6f} sq degrees")
    else:
        print("   No results found")

    print("\n2. Searching for 'Uruchye, Minsk'...")
    results = geocode_location("Uruchye, Minsk, Belarus", limit=3)

    if results:
        print(f"   Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result}")
    else:
        print("   No results found")

    print("\n" + "=" * 60)
    print("Geocoding module test complete!")
