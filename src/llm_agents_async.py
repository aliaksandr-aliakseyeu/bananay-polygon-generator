"""
Async LLM Agents for parallel API calls
OpenAI 2.x with Pydantic Structured Outputs
"""

from typing import List, Dict, Optional, Any, Type, TypeVar
import asyncio
import json
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from src.config import config
from src.geocoding import GeocodingResult

T = TypeVar('T', bound=BaseModel)


class LocationContext(BaseModel):
    """Context information for location query"""
    city: Optional[str] = Field(None, description="City name if mentioned or implied")
    country: Optional[str] = Field(None, description="Country if mentioned or implied")
    region: Optional[str] = Field(None, description="Region if mentioned")


class ParsedQuery(BaseModel):
    """Structured output for query parser"""
    locations: List[str] = Field(description="List of extracted location names")
    context: LocationContext = Field(description="Geographic context")
    language: str = Field(description="Detected language code (en, ru, etc)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")


class DisambiguationResult(BaseModel):
    """Structured output for disambiguation"""
    best_index: int = Field(ge=0, description="Index of the best matching result")
    reason: str = Field(description="Explanation for the choice")


class ValidationResult(BaseModel):
    """Structured output for validation"""
    is_valid: bool = Field(description="Whether results are valid")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")
    suggestions: List[str] = Field(default_factory=list, description="List of suggestions")


class BufferSuggestion(BaseModel):
    """Structured output for buffer radius suggestion"""
    radius_km: float = Field(gt=0, description="Suggested radius in kilometers")
    reasoning: str = Field(description="Explanation for the suggested radius")


class AsyncLLMClient:
    """
    Async OpenAI client wrapper with Pydantic Structured Outputs
    Compatible with OpenAI 2.x
    """

    def __init__(self):
        if not config.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY not set. Please add it to .env file."
            )
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL

    async def chat_structured(
        self,
        messages: List[Dict[str, str]],
        response_format: Type[T],
    ) -> T:
        """
        Send async chat completion with Pydantic structured output (OpenAI 2.x)

        Args:
            messages: List of message dicts with 'role' and 'content'
            response_format: Pydantic model class for structured output

        Returns:
            Parsed Pydantic model instance

        Raises:
            ValueError: If model refuses or returns empty response
        """
        response = await self.client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            response_format=response_format,
        )

        choice = response.choices[0]

        if choice.message.refusal:
            raise ValueError(f"Model refused to respond: {choice.message.refusal}")

        if choice.message.parsed is None:
            raise ValueError("Model returned empty parsed response")

        return choice.message.parsed

    # async def chat(
    #     self,
    #     messages: List[Dict[str, str]],
    #     response_format: Optional[Dict] = None,
    # ) -> str:
    #     """
    #     Legacy chat method for backward compatibility
    #     Use chat_structured() for better type safety

    #     Args:
    #         messages: List of message dicts with 'role' and 'content'
    #         response_format: Optional format (e.g., {"type": "json_object"})

    #     Returns:
    #         Response content string

    #     Raises:
    #         ValueError: If model refuses or returns empty response
    #     """
    #     kwargs = {
    #         "model": self.model,
    #         "messages": messages,
    #     }

    #     if response_format:
    #         kwargs["response_format"] = response_format

    #     response = await self.client.chat.completions.create(**kwargs)

    #     choice = response.choices[0]

    #     if choice.message.refusal:
    #         raise ValueError(f"Model refused to respond: {choice.message.refusal}")

    #     content = choice.message.content
    #     if content is None:
    #         raise ValueError("Model returned empty response")

    #     return content


class AsyncQueryParserAgent:
    """
    Async query parser with Pydantic structured output
    Uses OpenAI 2.x Structured Outputs for guaranteed schema compliance
    """

    def __init__(self, llm_client: AsyncLLMClient):
        self.llm = llm_client

    async def parse(self, user_query: str) -> Dict[str, Any]:
        """
        Parse natural language query asynchronously with structured output

        Args:
            user_query: Natural language text

        Returns:
            Dict with locations, context, language (for backward compatibility)
        """
        system_prompt = """
            You are a geographic query parser. Extract and normalize location
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

        parsed = await self.llm.chat_structured(
            messages,
            response_format=ParsedQuery,
        )

        return {
            "locations": parsed.locations,
            "context": {
                "city": parsed.context.city,
                "country": parsed.context.country,
                "region": parsed.context.region,
            },
            "language": parsed.language,
            "confidence": parsed.confidence,
        }


class AsyncDisambiguationAgent:
    """
    Async disambiguation agent with Pydantic structured output
    Uses OpenAI 2.x Structured Outputs for guaranteed schema compliance
    """

    def __init__(self, llm_client: AsyncLLMClient):
        self.llm = llm_client

    async def select_best(
        self,
        location_query: str,
        geocoding_results: List[GeocodingResult],
        context: Dict[str, str],
    ) -> int:
        """
        Select best geocoding result asynchronously with structured output

        Args:
            location_query: Original location query
            geocoding_results: List of geocoding results
            context: Context from query parsing

        Returns:
            Index of best result
        """
        system_prompt = """
            You are a geocoding result disambiguator.
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
        """

        candidates = []
        for i, result in enumerate(geocoding_results):
            candidates.append(
                f"{i}. {result.display_name} "
                f"(type: {result.place_type}, "
                f"importance: {result.importance:.2f}, "
                f"coords: {result.lat:.4f}, {result.lon:.4f})"
            )

        user_message = f"""
            Location query: "{location_query}"
            Context: {json.dumps(context)}

            Candidates:
            {chr(10).join(candidates)}

            Which result best matches the query considering the context?
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        result = await self.llm.chat_structured(
            messages,
            response_format=DisambiguationResult,
        )

        return result.best_index

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
    """
    Async validation agent with Pydantic structured output
    Uses OpenAI 2.x Structured Outputs for guaranteed schema compliance
    """

    def __init__(self, llm_client: AsyncLLMClient):
        self.llm = llm_client

    async def validate(
        self,
        user_query: str,
        parsed_data: Dict[str, Any],
        geocoded_locations: List[Dict],
    ) -> Dict[str, Any]:
        """
        Validate geocoding results asynchronously with structured output

        Args:
            user_query: Original query
            parsed_data: Parsed query data
            geocoded_locations: Geocoding results

        Returns:
            Dict with is_valid, warnings and suggestions (for backward compatibility)
        """
        system_prompt = """
            You are a geocoding result validator.
            Check if geocoding results match user intent.

            Look for:
            1. Wrong country/region
            2. Wrong type of location (e.g., street instead of district)
            3. Unexpected locations
            4. Missing expected locations
        """

        geocoded_summary = []
        for loc in geocoded_locations:
            try:
                result = loc['result']
                geocoded_summary.append(f"- {loc['query']} → {result.display_name}")
            except Exception:
                geocoded_summary.append(f"- {loc['query']} → [Error]")

        user_message = f"""
            Original query: "{user_query}"
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

        result = await self.llm.chat_structured(
            messages,
            response_format=ValidationResult,
        )

        return {
            "is_valid": result.is_valid,
            "warnings": result.warnings,
            "suggestions": result.suggestions,
        }


class AsyncBufferSuggestionAgent:
    """
    Async buffer suggestion agent with Pydantic structured output
    Uses OpenAI 2.x Structured Outputs for guaranteed schema compliance
    """

    def __init__(self, llm_client: AsyncLLMClient):
        self.llm = llm_client

    async def suggest_radius(
        self, location_name: str, place_type: str, context: Dict[str, str]
    ) -> float:
        """
        Suggest buffer radius asynchronously with structured output

        Args:
            location_name: Name of location
            place_type: Type (village, hamlet, neighbourhood, etc.)
            context: Query context

        Returns:
            Suggested radius in kilometers
        """
        system_prompt = """
            You are a geographic buffer radius suggester.
            Suggest appropriate buffer radius in kilometers based on location type.

            Guidelines:
            - hamlet, village, locality: 0.5-2 km
            - neighbourhood, suburb, residential: 1-3 km
            - town, city_district: 2-5 km
            - city: 5-15 km
            - region, county: 10-50 km
        """

        user_message = f"""
            Location: {location_name}
            Type: {place_type}
            Context: {json.dumps(context)}

            What buffer radius (in km) would you suggest?
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        result = await self.llm.chat_structured(
            messages,
            response_format=BufferSuggestion,
        )

        return result.radius_km

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


# def run_async(coro):
#     """Run async coroutine in sync context"""
#     try:
#         asyncio.get_running_loop()
#         import nest_asyncio
#         nest_asyncio.apply()
#         return asyncio.run(coro)
#     except RuntimeError:
#         return asyncio.run(coro)
