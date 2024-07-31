from dotenv import load_dotenv
from semantic_router import Route, RouteLayer
from semantic_router.encoders import OpenAIEncoder

# from utils import fetch_and_extract_text, fetch_cdx_data, get_trend_analysis
# from semantic_router.llms.openai import get_schemas_openai
from config import router_schemas
import os

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Get the schemas for the functions
# schemas = get_schemas_openai(
#     [fetch_cdx_data, fetch_and_extract_text, get_trend_analysis]
# )

schemas = router_schemas

# Add the new route for trend analysis
routes = [
    Route(
        name="fetch_cdx_data",
        utterances=[
            "Get CDX data for URL",
            "Fetch Wayback Machine data for URL",
            "Historical data for URL",
        ],
        function_schemas=schemas,
    ),
    Route(
        name="fetch_and_extract_text",
        utterances=[
            "Get webpage content",
            "Extract text from URL",
            "Fetch webpage text",
        ],
        function_schemas=schemas,
    ),
    Route(
        name="get_trend_analysis",
        utterances=[
            "Analyze trends for URL",
            "Get resilience, fixity, and chaos metrics",
            "Trend analysis for website",
            "Show me the trend analysis of URL",
        ],
        function_schemas=schemas,
    ),
]


class SemanticRouterService:
    def __init__(self):
        encoder = OpenAIEncoder()
        self.layer = RouteLayer(encoder=encoder, routes=routes)

    def get_intent(self, user_input):
        result = self.layer(user_input)
        print(result.name)

        # If the confidence about a route is zero, return None
        return result.name if result.name else None
