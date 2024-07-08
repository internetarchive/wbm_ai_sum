import streamlit as st
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

# from services import OpenAIService, WaybackService, SemanticRouterService
from services import OpenAIService, WaybackService

load_dotenv()

st.title("Wayback Machine Copilot")

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
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
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
    else:
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
