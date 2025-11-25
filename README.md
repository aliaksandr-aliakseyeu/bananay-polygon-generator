# Polygon Generator

Natural language to geographic polygon generator using OpenAI and OpenStreetMap.

## Description

This tool allows you to describe geographic areas in natural language and get GeoJSON polygons as output. The system uses LangGraph to orchestrate an AI-powered workflow that understands your query, geocodes locations, and generates combined polygons.

## Examples

**English:**
```
Input: "I want a polygon that includes Uruchye-6 and Kolodishchi in Minsk district and Sukhorukie in Minsk district"
Output: GeoJSON polygon combining all these areas
```

**Russian:**
```
Input: "Я хочу полигон который включает Уручье-6 Минска + Колодищи в Минском районе + Сухорукие в Минском районе"
Output: GeoJSON polygon combining all these areas
```

## Features

- 🤖 **AI-Powered Parsing** - Extracts locations from natural language with spelling correction
- 🌍 **Multi-language Support** - Works with English and Russian
- 🔍 **Smart Geocoding** - Uses Nominatim with AI-powered disambiguation
- 📐 **Boundary Detection** - Automatically fetches OSM administrative boundaries
- 🎯 **Buffer Generation** - Creates circular buffers for point locations with AI-suggested radii
- 🗺️ **Interactive Maps** - Visualize results with Folium/Leaflet
- 💾 **GeoJSON Export** - Download results in standard GeoJSON format
- ⏸️ **Human-in-the-Loop** - Pauses for user input when needed (buffer radii)
- 🔀 **Disconnected Regions** - Handles multiple separate polygons (e.g., distant cities)

## Technology Stack

- **Frontend:** Streamlit
- **LLM Orchestration:** LangGraph + LangChain
- **LLM:** OpenAI GPT-4-turbo
- **Geocoding:** Nominatim (OpenStreetMap)
- **Geometry:** Shapely
- **Maps:** Folium + Leaflet
- **Async:** aiohttp, nest-asyncio


### Prerequisites

- Python 3.11+
- Poetry
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. Clone the repository

2. Install dependencies:
```bash
poetry install
```

3. Create `.env` file:
```bash
cp .env.example .env
```

4. Add your OpenAI API key to `.env`:
```env
OPENAI_API_KEY=sk-your-actual-key-here
```

### Run the Application

```bash
poetry run streamlit run app.py
```

Open your browser at: **http://localhost:8501**

## Project Structure

```
polygon-generator/
├── app.py                        # Main Streamlit UI
├── src/
│   ├── config.py                 # Configuration management
│   ├── geocoding.py              # Nominatim/Overpass API clients
│   ├── geometry.py               # Shapely geometry operations
│   ├── llm_agents_async.py       # Async OpenAI agents
│   └── orchestrator/             # LangGraph workflow orchestration
│       ├── __init__.py           # Public API exports
│       ├── interface.py          # Clean API for external use
│       ├── graph.py              # LangGraph workflow definition
│       ├── state.py              # State management
│       ├── routing.py            # Conditional routing logic
│       └── nodes/                # Workflow nodes
│           ├── base.py           # Base node interface
│           ├── intent_async.py   # Intent validation
│           ├── parser_async.py   # Query parsing
│           ├── geocoding.py      # Location geocoding
│           ├── disambiguation_async.py  # AI result selection
│           ├── boundaries.py     # OSM boundary fetching
│           ├── buffers_async.py  # Buffer generation
│           ├── validation_async.py      # Result validation
│           └── merge.py          # Geometry merging
├── pyproject.toml                # Poetry dependencies
├── .env.example                  # Environment variables template
└── README.md                     # This file
```

## How It Works

The system uses a LangGraph workflow with the following steps:

1. **Validate Intent** - Check if query is about geographic polygons
2. **Parse Query** - Extract locations, context (city/country), and language
3. **Geocode Locations** - Search each location in Nominatim
4. **Disambiguate** - AI selects best match from geocoding results
5. **Fetch Boundaries** - Get OSM administrative boundaries
6. **Suggest Buffers** - For locations without boundaries, AI suggests buffer radii
7. **[User Input]** - User confirms/adjusts buffer radii (if needed)
8. **Generate Buffers** - Create circular buffers around point locations
9. **Validate Results** - Check geometry validity and provide warnings
10. **Merge Geometries** - Combine all polygons into final result

## Usage Tips

### Writing Good Queries

**✅ Good:**
- "I want a polygon that includes Uruchye-6 and Kolodishchi in Minsk district"
- "Я хочу полигон который включает Уручье-6 Минска + Колодищи в Минском районе"
- "Combine Minsk city with Gomel city, Belarus"

**❌ Less Optimal:**
- "uručča" (use standard spelling)
- "place near there" (be specific)
- Just "districts" (which districts? where?)

### Buffer Radii Guidelines

When the system asks for buffer radii:
- **Village/Town:** 0.5-2 km
- **District/Neighborhood:** 2-5 km
- **City:** 5-10 km
- **Large Region:** 10+ km

The AI will suggest appropriate radii based on location type.


## Troubleshooting

### "OPENAI_API_KEY not set"
Add your API key to `.env` file (see Installation step 4)

### "Invalid API key"
- Verify key starts with `sk-`
- Check for extra spaces
- Ensure key is active in OpenAI dashboard

### No results for location
- Add country context: "Kolodishchi, Belarus"
- Use Latin transliteration: "Uruchye" instead of "Уручча"
- Be more specific: "Uruchye district, Minsk city"

### Slow processing
This is normal! AI + geocoding takes time:
- Query parsing: 2-3 seconds
- Geocoding: 1 second per location (rate limit)
- AI disambiguation: 2-3 seconds per location
- **Total: 10-20 seconds for 3-5 locations**

## License

MIT

---

**Made with 🤖 LangGraph + 🗺️ OpenStreetMap**
