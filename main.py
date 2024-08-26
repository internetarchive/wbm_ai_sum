import logging
import random
import pandas as pd
import streamlit as st
import os
import sys
from typing import Any, Dict, Generator
from dotenv import load_dotenv
from config import suggestions
from services import OpenAIService, WaybackService, SemanticRouterService
from utils.trend_analysis import analyze_trends

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page config
st.set_page_config(
    page_title="Athena",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/internetarchive/wbm_ai_sum",
        "Report a bug": "https://github.com/internetarchive/wbm_ai_sum/issues/new",
    },
)


@st.cache_resource
def initialize_services():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        st.error(
            "OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable."
        )
        st.stop()

    try:
        return OpenAIService(openai_api_key), WaybackService(), SemanticRouterService()
    except ValueError as e:
        st.error(f"Error initializing services: {str(e)}")
        st.stop()


openai_service, wayback_service, semantic_router = initialize_services()


# display all suggestions in the sidebar as text, make the suggestionn shown in sidebar expander
def suggestions_fragment():
    with st.sidebar.expander("View Suggestions"):
        for suggestion in suggestions:
            st.write(suggestion)


def process_user_input(user_input: str):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    # Use Semantic Router to determine intent
    intent = semantic_router.get_intent(user_input)
    logging.info(f"Detected intent: {intent}")
    # Prepare the messages for OpenAI, including the detected intent
    messages_for_openai = st.session_state.messages.copy()
    if intent:
        messages_for_openai.append(
            {
                "role": "system",
                "content": f"The detected intent for the user's last message is: {intent}. "
                f"Consider using the {intent} function if appropriate.",
            }
        )

    # Get OpenAI response, which may include a function call
    try:
        response = openai_service.get_completion(messages_for_openai)
        if response is None:
            st.error("Received an invalid response from OpenAI service.")
            return

        if response and response.function_call:
            # OpenAI has decided to call a function
            function_name = response.function_call.name
            function_args = openai_service.get_function_args(response.function_call)

            # Ensure args is correctly structured
            if "url" in function_args:
                function_args["url"] = str(
                    function_args["url"]
                )  # Convert URL to string if necessary

            # Execute the function
            result = execute_function(function_name, function_args)

            # Add the function result to the messages
            st.session_state.messages.append(
                {
                    "role": "function",
                    "name": str(function_name),
                    "content": str(result),
                }
            )

            # Get a new response from OpenAI with the function result
            final_response = openai_service.get_completion(st.session_state.messages)
            response_content = final_response.content
        else:
            # No function call, use the initial response
            response_content = (
                response.content if response else "No response generated."
            )

    except Exception as e:
        st.error(f"Error processing request: {str(e)}")
        return

    st.session_state.messages.append({"role": "assistant", "content": response_content})
    with st.chat_message("assistant", avatar="assets/favicon.ico"):
        st.write_stream(stream_text(response_content))


def execute_function(function_name: str, args: Dict[str, Any]) -> str:
    if function_name == "fetch_cdx_data":
        logger.info(f"Fetching CDX data for URL: {args.get('url')}")
        logger.info(f"Limit: {args.get('limit')}, URL: {args.get('url')}")
        return wayback_service.fetch_cdx_data(args.get("url"), args.get("limit"))
    elif function_name == "fetch_data_wayback":
        logger.info(
            f"Fetching data for URL: {args.get('url')} with timestamp: {args.get('timestamp')}"
        )
        return wayback_service.fetch_data_wayback(
            args.get("url"), args.get("timestamp")
        )
    elif function_name == "get_trend_analysis":
        logger.info(f"Getting trend analysis for URL: {args.get('url')}")
        return wayback_service.get_trend_analysis(args.get("url"))

    else:
        logger.error(f"Unknown function: {function_name}")
        raise ValueError(f"Unknown function: {function_name}")


def stream_text(text: str):
    if text is None:
        yield "No response generated."
    else:
        for char in text:
            yield char


# Main content
# st.image("assets/favicon.ico", width=50)
st.title("Archive Temporal History Exploration and Navigation Assistant")

suggestions_fragment()

# Initialize messages
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hello, How can I help you?"}
    ]

# Display chat history
for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"]:
        avatar_path = "assets/favicon.ico" if msg["role"] == "assistant" else None
        with st.chat_message(msg["role"], avatar=avatar_path):
            if msg["role"] == "assistant":
                st.write_stream(stream_text(msg["content"]))
            else:
                st.write(msg["content"])

# Chat input
user_input = st.chat_input("Type your message here...", key="user_input")

if user_input:
    process_user_input(user_input)
