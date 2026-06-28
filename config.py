import os
from dotenv import load_dotenv

load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "mock").lower()

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

BING_API_KEY = os.getenv("BING_API_KEY")
BING_ENDPOINT = os.getenv(
    "BING_ENDPOINT",
    "https://api.bing.microsoft.com/v7.0/search",
)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///house_finder.db")

MAX_RESULTS_PER_QUERY = int(os.getenv("MAX_RESULTS_PER_QUERY", "10"))
MAX_URLS_PER_CRITERIA = int(os.getenv("MAX_URLS_PER_CRITERIA", "50"))

REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "12"))
DELAY_BETWEEN_REQUESTS_SECONDS = float(
    os.getenv("DELAY_BETWEEN_REQUESTS_SECONDS", "1")
)

ENABLE_LIVE_FETCH = os.getenv("ENABLE_LIVE_FETCH", "false").lower() == "true"
ENABLE_PLAYWRIGHT_FALLBACK = (
    os.getenv("ENABLE_PLAYWRIGHT_FALLBACK", "false").lower() == "true"
)