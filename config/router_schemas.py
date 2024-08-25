router_schemas = (
    {
        "type": "function",
        "function": {
            "name": "fetch_cdx_data",
            "description": "Fetches CDX (Capture Index) data from the Wayback Machine for a given URL.\n\nThis function queries the Wayback Machine's CDX server to retrieve historical\ninformation about captures of a specified URL. It allows for various query\nparameters to filter and customize the results.\n\n:param url: The URL to fetch CDX data for. This should be a full URL including\n            the protocol.\n:return: A JSON string containing the CDX data if successful, or a dictionary\n         with an 'error' key describing the failure reason.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch CDX data for. This should be a full URL including\n the protocol.",
                    },
                    "match_type": {
                        "type": "object",
                        "description": "The type of URL match",
                        "enum": ["exact", "prefix", "host", "domain"],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "The maximum number of results to return",
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "A list of specific fields to return",
                    },
                    "filters": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "A list of filters to apply",
                    },
                    "from_timestamp": {
                        "type": "string",
                        "description": "Start timestamp for filtering",
                    },
                    "to_timestamp": {
                        "type": "string",
                        "description": "End timestamp for filtering",
                    },
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_and_extract_text",
            "description": "Fetches a webpage and extracts its main textual content.\n\nThis function retrieves the HTML content of a given URL, then uses the\ntrafilatura library to extract relevant metadata and the main text content.\nIt focuses on extracting the title and the visible text content, discarding\nboilerplate elements like navigation, headers, footers, etc.\n\n:param url: The URL of the webpage to fetch and extract text from.\n            This should be a full URL including the protocol.\n:type url: str\n:return: A string containing the extracted text content, or an empty string\n         if an error occurs during fetching or processing.\n:rtype: str",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the webpage to fetch and extract text from.\n            This should be a full URL including the protocol.",
                    }
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_trend_analysis",
            "description": "Get trend analysis for a URL, including resilience, fixity, and chaos metrics. The metric are for the understanding of LLM only. Try to simplify the explanation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to analyze"}
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_data_wayback",
            "description": "Fetches a webpage snapshot from the Wayback Machine and extracts its main textual content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the webpage to fetch and extract text from.",
                    },
                    "timestamp": {
                        "type": "string",
                        "description": "The timestamp of the snapshot in the format 'YYYYMMDDhhmmss'.\nIf None, the latest snapshot will be used.",
                    },
                },
                "required": ["url"],
            },
        },
    },
)
