"""
Geocoding services using Nominatim and Overpass API (OpenStreetMap)
"""

import time
import asyncio
from typing import Optional, List
from threading import Lock
import aiohttp
from shapely.geometry import Polygon, shape
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
    """
    Client for Nominatim geocoding API with global rate limiting

    Uses class-level locks to ensure rate limits are respected across
    all instances and concurrent users in the same process.
    """

    # Shared across ALL instances for proper multi-user rate limiting
    _last_request_time = 0.0
    _sync_lock = Lock()  # For thread-safe sync calls
    _async_lock = asyncio.Lock()  # For async calls

    def __init__(self):
        self.base_url = config.NOMINATIM_BASE_URL
        self.user_agent = config.NOMINATIM_USER_AGENT
        self.delay = config.NOMINATIM_DELAY

    async def _rate_limit_async(self):
        """
        Async rate limiting for concurrent requests
        Ensures proper spacing across all users
        """
        async with NominatimClient._async_lock:
            elapsed = time.time() - NominatimClient._last_request_time
            if elapsed < self.delay:
                await asyncio.sleep(self.delay - elapsed)
            NominatimClient._last_request_time = time.time()

    async def search_async(
        self,
        query: str,
        limit: int = 5,
        country_codes: Optional[List[str]] = None,
        polygon_geojson: bool = True,
    ) -> List[GeocodingResult]:
        """
        Async search for a location by name with rate limiting

        Args:
            query: Location name to search for
            limit: Maximum number of results
            country_codes: List of country codes to limit search (e.g., ["by", "pl"])
            polygon_geojson: Include polygon geometry if available

        Returns:
            List of GeocodingResult objects
        """
        await self._rate_limit_async()

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
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/search",
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return [GeocodingResult(item) for item in data]

        except aiohttp.ClientError as e:
            print(f"Nominatim API error: {e}")
            return []
        except asyncio.TimeoutError:
            print(f"Nominatim API timeout for query: {query}")
            return []


async def geocode_location_async(
    query: str, limit: int = 5, country_codes: Optional[List[str]] = None
) -> List[GeocodingResult]:
    """
    Async geocode a location by name with global rate limiting

    Args:
        query: Location name
        limit: Max results
        country_codes: Limit to specific countries

    Returns:
        List of results
    """
    client = NominatimClient()
    return await client.search_async(query, limit=limit, country_codes=country_codes)
