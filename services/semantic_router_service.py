from dotenv import load_dotenv
from semantic_router import Route, RouteLayer
from semantic_router.encoders import OpenAIEncoder
from config import router_schemas
import os

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

schemas = router_schemas

# Add the new route for trend analysis
routes = [
    Route(
        name="fetch_cdx_data",
        utterances=[
            "Get CDX data for URL",
            "Fetch Wayback Machine data for URL",
            "Historical data for URL",
            "Get historical data for URL",
            "Get CDX data",
            "Get Archive data",
            "Get Archive records",
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
            "What are the trends for this URL?",
            "What are the resilience, fixity, and chaos metrics for this URL?",
            "What are the metrics for this URL?",
            "What are the trends for this website?",
            "How is this website doing?",
            "How is this URL doing?",
            "How has this URL been performing?",
            "How healthy is this URL?",
            "How resilient is this URL?",
            "How chaotic is this URL?",
            "How stable is this URL?",
            "How reliable is this URL?",
            "How trustworthy is this URL?",
            "How secure is this URL?",
            "How much has this URL changed?",
            "How much has this website changed?",
            "How much has this URL been modified?",
        ],
        function_schemas=schemas,
    ),
    Route(
        name="fetch_data_wayback",
        utterances=[
            "Fetch webpage snapshot",
            "Get webpage snapshot",
            "Get webpage snapshot from Wayback Machine",
            "Fetch webpage snapshot from Wayback Machine",
            "Fetch webpage from Wayback Machine",
            "What was the webpage like in the past?",
            "Show me the webpage snapshot",
            "What did the webpage look like in the past?",
            "What was shown on the webpage in the past?",
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

        # If the confidence about a route is zero, return None
        return result.name if result.name else None
