"""
Configuration management for the polygon generator
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration"""

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-5-nano")

    # Geocoding Configuration
    NOMINATIM_USER_AGENT: str = os.getenv(
        "NOMINATIM_USER_AGENT", "polygon-generator/0.1.0"
    )
    NOMINATIM_BASE_URL: str = os.getenv(
        "NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org"
    )
    OVERPASS_BASE_URL: str = os.getenv(
        "OVERPASS_BASE_URL", "https://overpass-api.de/api/interpreter"
    )

    # Rate limiting
    NOMINATIM_DELAY: float = 1.0

    # Application settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        Validate configuration

        Returns:
            tuple: (is_valid, list of error messages)
        """
        errors = []

        if not cls.OPENAI_API_KEY:
            errors.append(
                "Warning: OPENAI_API_KEY not set. LLM features will not work."
            )

        if not cls.NOMINATIM_USER_AGENT:
            errors.append("NOMINATIM_USER_AGENT must be set")

        if not cls.NOMINATIM_BASE_URL:
            errors.append("NOMINATIM_BASE_URL must be set")

        if not cls.OVERPASS_BASE_URL:
            errors.append("OVERPASS_BASE_URL must be set")

        is_valid = len([e for e in errors if not e.startswith("Warning:")]) == 0

        return is_valid, errors

    @classmethod
    def get_info(cls) -> dict:
        """Get configuration info (without sensitive data)"""
        return {
            "openai_model": cls.OPENAI_MODEL,
            "openai_key_set": bool(cls.OPENAI_API_KEY),
            "nominatim_url": cls.NOMINATIM_BASE_URL,
            "overpass_url": cls.OVERPASS_BASE_URL,
            "debug": cls.DEBUG,
        }


config = Config()


if __name__ == "__main__":
    print("Configuration Test")
    print("=" * 50)

    is_valid, errors = config.validate()

    print(f"Valid: {is_valid}")
    if errors:
        print("\nMessages:")
        for error in errors:
            print(f"  - {error}")

    print("\nConfiguration Info:")
    for key, value in config.get_info().items():
        print(f"  {key}: {value}")
