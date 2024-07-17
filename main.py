import random
import streamlit as st
import os
import sys

from config import suggestions

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

# from services import OpenAIService, WaybackService, SemanticRouterService
from services import OpenAIService, WaybackService

load_dotenv()

# Set page config
st.set_page_config(
    page_title="Athena",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": "https://github.com/internetarchive/wbm_ai_sum",
        "Report a bug": "https://github.com/internetarchive/wbm_ai_sum/issues/new",
        # "About": "# This is a header. This is an *extremely* cool app!",
    },
)
st.logo("assets/favicon.ico")


# st.image("assets/owl_white.png", width=100)
st.title("Archive Temporal History Exploration and Navigation Assistant")

# Check if OpenAI API key is set
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error(
        "OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable."
    )
    st.stop()

# Initialize services
try:
    openai_service = OpenAIService(openai_api_key)
    wayback_service = WaybackService()
    # semantic_router = SemanticRouterService()
except ValueError as e:
    st.error(f"Error initializing services: {str(e)}")
    st.stop()

# Initialize messages
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you?"}
    ]

for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"]:
        avatar_path = "assets/favicon.ico" if msg["role"] == "assistant" else None
        st.chat_message(msg["role"], avatar=avatar_path).write(msg["content"])

# Initialize suggestion visibility state
if "show_suggestion" not in st.session_state:
    st.session_state.show_suggestion = True

# Initialize prompt in session state if not present
if "prompt" not in st.session_state:
    st.session_state.prompt = None

# Display a random suggestion as a button if the flag is True
if st.session_state.show_suggestion:
    random_suggestion = random.choice(suggestions)
    if st.button(random_suggestion):
        st.session_state.prompt = random_suggestion
        st.session_state.show_suggestion = False  # Hide the suggestion button
    prompt = None

# Use the prompt from session state if available
prompt = st.session_state.get("prompt", st.chat_input())

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Get intent using semantic router
    # intent = semantic_router.get_intent(prompt)
    intent = False
    # if intent is None:
    if intent:
        # If no specific intent is matched, let GPT handle it without functions
        response = openai_service.get_completion(st.session_state.messages)
        print(response)
        st.session_state.messages.append(
            {"role": "assistant", "content": response.content}
        )
        st.chat_message("assistant").write(response.content)
        st.session_state.show_suggestion = True  # Show the suggestion button again
    else:
        st.session_state.show_suggestion = False  # Hide the suggestion button
        # Get OpenAI response with function call
        response = openai_service.get_completion(st.session_state.messages)

        if response.function_call:
            function_name = response.function_call.name
            args = openai_service.get_function_args(response.function_call)

            if function_name == "fetch_cdx_data":
                result = wayback_service.fetch_cdx_data(args["url"])
            elif function_name == "fetch_and_extract_text":
                result = wayback_service.fetch_and_extract_text(args["url"])
            elif function_name == "get_trend_analysis":
                result = wayback_service.get_trend_analysis(args["url"])

            st.session_state.messages.append(
                {
                    "role": "function",
                    "name": function_name,
                    "content": result,
                }
            )

            # Get final response from OpenAI
            final_response = openai_service.get_completion(st.session_state.messages)
            st.session_state.messages.append(
                {"role": "assistant", "content": final_response.content}
            )
            st.chat_message("assistant").write(final_response.content)
        else:
            st.session_state.messages.append(
                {"role": "assistant", "content": response.content}
            )
            st.chat_message("assistant").write(response.content)

        # Show the suggestion button again after the assistant's response
        st.session_state.show_suggestion = True
