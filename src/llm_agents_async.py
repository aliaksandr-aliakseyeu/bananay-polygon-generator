"""
Async LLM Agents for parallel API calls
"""

from typing import List, Dict, Optional, Any
import asyncio
from openai import AsyncOpenAI
from src.config import config
from src.geocoding import GeocodingResult
import json


class AsyncLLMClient:
    """Async OpenAI client wrapper"""

    def __init__(self):
        if not config.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY not set. Please add it to .env file."
            )
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL

    async def chat(
        self,
        messages: List[Dict[str, str]],
        # temperature: float = 0.3,
        response_format: Optional[Dict] = None,
    ) -> str:
        """
        Send async chat completion request

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Creativity (0-2)
            response_format: Optional format (e.g., {"type": "json_object"})

        Returns:
            Response content
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            # "temperature": temperature,
        }

        if response_format:
            kwargs["response_format"] = response_format

        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content


class AsyncQueryParserAgent:
    """Async version of query parser"""

    def __init__(self, llm_client: AsyncLLMClient):
        self.llm = llm_client

    async def parse(self, user_query: str) -> Dict[str, Any]:
        """
        Parse natural language query asynchronously

        Args:
            user_query: Natural language text

        Returns:
            Dict with locations, context, language
        """
        system_prompt = """You are a geographic query parser. Extract and normalize location \
        information from user queries.

        Your task:
        1. Extract all location names mentioned
        2. **FIX spelling and grammar errors** in location names
        3. Normalize capitalization (proper names should be capitalized)
        4. Detect context (nearby city, country, region)
        5. Detect language (en, ru)

        IMPORTANT - Spelling correction:
        - "Совецкий район" → "Советский район" (fix typo: ц→т)
        - "валерьяново" → "Валерьяново" (capitalize proper name)
        - "минский район" → "Минский район" (capitalize)
        - "уручье" → "Уручье" (capitalize district name)

        CRITICAL - Context vs Location:
        - "в минском районе" = CONTEXT (in Minsk district), NOT a location!
        - "валерьяново в минском районе" = location: "Валерьяново", context: "Минский район"
        - "а.г." or "аг" = village prefix (агрогородок), remove from location name
        - Prepositions (в, на, около, рядом с) indicate CONTEXT, not separate locations

        Return JSON format:
        {
        "locations": ["location1", "location2", ...],
        "context": {
            "city": "city name if mentioned or implied",
            "country": "country if mentioned or implied",
            "region": "region if mentioned"
        },
        "language": "ru",
        "confidence": 0.9
        }

        Examples:
        - "Я хочу полигон Уручье Минска + Колодищи" →
        locations: ["Уручье", "Колодищи"], context: {"city": "Minsk", "country": "Belarus"}

        - "Советский район и а.г. валерьяново в минском районе, аг королев стан в минском районе" →
        locations: ["Советский район", "Валерьяново", "Королев Стан"]
        context: {"region": "Минский район", "country": "Belarus"}
        (NOTE: "в минском районе" is context, NOT a 4th location!)

        - "combine districts: uruchye, kolodishchi near Minsk" →
        locations: ["Uruchye", "Kolodishchi"], context: {"city": "Minsk"}

        Be smart about context:
        - "Уручье" without city → likely Minsk (it's a well-known district)
        - "Колодищи" → likely near Minsk, Belarus
        - Always include country if you can infer it
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ]

        response = await self.llm.chat(
            messages,
            # temperature=0.3,
            response_format={"type": "json_object"},
        )

        return json.loads(response)


class AsyncDisambiguationAgent:
    """Async version of disambiguation agent"""

    def __init__(self, llm_client: AsyncLLMClient):
        self.llm = llm_client

    async def select_best(
        self,
        location_query: str,
        geocoding_results: List[GeocodingResult],
        context: Dict[str, str],
    ) -> int:
        """
        Select best geocoding result asynchronously

        Args:
            location_query: Original location query
            geocoding_results: List of geocoding results
            context: Context from query parsing

        Returns:
            Index of best result
        """
        system_prompt = """You are a geocoding result disambiguator.
Given a location query and multiple results, pick the most relevant one.

CRITICAL: Prioritize location types in this order:
1. administrative, boundary, place (cities, villages, settlements, агрогородки) - HIGHEST PRIORITY
2. station (railway/bus stations) - MEDIUM PRIORITY
3. service, amenity, highway (streets, bus stops, services) - LOWEST PRIORITY

Then consider secondary factors:
- Context (city, country, region)
- Importance score (only if types are equal)
- Geographic proximity to context

EXAMPLE: If you see "Колодищи":
- Option A: station (importance: 0.32) ❌
- Option B: administrative (importance: 0.27) ✅ CHOOSE THIS - it's a settlement!

Return JSON: {"best_index": 0, "reason": "explanation"}
"""

        # Build candidates description
        candidates = []
        for i, result in enumerate(geocoding_results):
            candidates.append(
                f"{i}. {result.display_name} "
                f"(type: {result.place_type}, "
                f"importance: {result.importance:.2f}, "
                f"coords: {result.lat:.4f}, {result.lon:.4f})"
            )

        user_message = f"""Location query: "{location_query}"
Context: {json.dumps(context)}

Candidates:
{chr(10).join(candidates)}

Which result best matches the query considering the context?
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        response = await self.llm.chat(
            messages,
            # temperature=0.2,
            response_format={"type": "json_object"},
        )

        result = json.loads(response)
        return int(result.get("best_index", 0))

    async def select_best_batch(
        self,
        queries_and_results: List[tuple[str, List[GeocodingResult]]],
        context: Dict[str, str],
    ) -> List[int]:
        """
        Process multiple disambiguations in parallel

        Args:
            queries_and_results: List of (query, results) tuples
            context: Shared context

        Returns:
            List of best indices
        """
        tasks = [
            self.select_best(query, results, context)
            for query, results in queries_and_results
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)


class AsyncValidationAgent:
    """Async version of validation agent"""

    def __init__(self, llm_client: AsyncLLMClient):
        self.llm = llm_client

    async def validate(
        self,
        user_query: str,
        parsed_data: Dict[str, Any],
        geocoded_locations: List[Dict],
    ) -> Dict[str, Any]:
        """
        Validate geocoding results asynchronously

        Args:
            user_query: Original query
            parsed_data: Parsed query data
            geocoded_locations: Geocoding results

        Returns:
            Dict with warnings and suggestions
        """
        system_prompt = """You are a geocoding result validator.
Check if geocoding results match user intent.

Look for:
1. Wrong country/region
2. Wrong type of location (e.g., street instead of district)
3. Unexpected locations
4. Missing expected locations

Return JSON: {
  "is_valid": true/false,
  "warnings": ["warning1", ...],
  "suggestions": ["suggestion1", ...]
}
"""

        geocoded_summary = []
        for loc in geocoded_locations:
            try:
                result = loc['result']
                geocoded_summary.append(f"- {loc['query']} → {result.display_name}")
            except Exception:
                geocoded_summary.append(f"- {loc['query']} → [Error]")

        user_message = f"""Original query: "{user_query}"
Parsed locations: {parsed_data.get('locations', [])}
Context: {parsed_data.get('context', {})}

Geocoded results:
{chr(10).join(geocoded_summary)}

Are these results reasonable? Any warnings or suggestions?
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        response = await self.llm.chat(
            messages,
            # temperature=0.3,
            response_format={"type": "json_object"},
        )

        return json.loads(response)


class AsyncBufferSuggestionAgent:
    """Async version of buffer suggestion agent"""

    def __init__(self, llm_client: AsyncLLMClient):
        self.llm = llm_client

    async def suggest_radius(
        self, location_name: str, place_type: str, context: Dict[str, str]
    ) -> float:
        """
        Suggest buffer radius asynchronously

        Args:
            location_name: Name of location
            place_type: Type (village, hamlet, neighbourhood, etc.)
            context: Query context

        Returns:
            Suggested radius in kilometers
        """
        system_prompt = """You are a geographic buffer radius suggester.
Suggest appropriate buffer radius in kilometers based on location type.

Guidelines:
- hamlet, village, locality: 0.5-2 km
- neighbourhood, suburb, residential: 1-3 km
- town, city_district: 2-5 km
- city: 5-15 km
- region, county: 10-50 km

Return JSON: {"radius_km": 2.0, "reasoning": "explanation"}
"""

        user_message = f"""Location: {location_name}
Type: {place_type}
Context: {json.dumps(context)}

What buffer radius (in km) would you suggest?
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        response = await self.llm.chat(
            messages,
            # temperature=0.2,
            response_format={"type": "json_object"},
        )

        result = json.loads(response)
        return float(result.get("radius_km", 1.0))

    async def suggest_radius_batch(
        self, locations: List[tuple[str, str, Dict[str, str]]]
    ) -> List[float]:
        """
        Process multiple buffer suggestions in parallel

        Args:
            locations: List of (name, place_type, context) tuples

        Returns:
            List of suggested radii
        """
        tasks = [
            self.suggest_radius(name, place_type, context)
            for name, place_type, context in locations
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)


def create_async_agents():
    """
    Create all async agents with shared client

    Returns:
        Tuple of (parser, disambiguator, validator, buffer_suggester)
    """
    llm_client = AsyncLLMClient()

    return (
        AsyncQueryParserAgent(llm_client),
        AsyncDisambiguationAgent(llm_client),
        AsyncValidationAgent(llm_client),
        AsyncBufferSuggestionAgent(llm_client),
    )


# Convenience function for sync code
def run_async(coro):
    """Run async coroutine in sync context"""
    try:
        asyncio.get_running_loop()
        # Loop running (e.g., in Jupyter), use nest_asyncio
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.run(coro)
    except RuntimeError:
        # No loop running, create new one
        return asyncio.run(coro)
