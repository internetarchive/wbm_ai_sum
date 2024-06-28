import streamlit as st
from openai import OpenAI
import re
import sys
import os
import json
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.cdxdata import fetch_cdx_data
from utils.extract_text import fetch_and_extract_text

schema_cdx_data = {
    "name": "fetch_cdx_data",
    "description": "Fetch CDX data from the Wayback Machine for a given URL",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch the CDX data for",
            },
            "match_type": {
                "type": "string",
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
}

schema_fetch_data = {
    "name": "fetch_and_extract_text",
    "description": "Fetch HTML content from a URL and extract relevant metadata",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch the HTML content from",
            },
        },
        "required": ["url"],
    },
}


load_dotenv()
# with st.sidebar:
#     openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
#     "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"

openai_api_key = os.getenv("OPENAI_API_KEY")

st.title("Wayback Machine Copilot")

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you?"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

print("Initial", st.session_state.messages)
if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    client = OpenAI(api_key=openai_api_key)

    # Add the user's message to the chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Call the OpenAI API
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=st.session_state.messages,
        functions=[schema_cdx_data, schema_fetch_data],
    )

    # Check if a function call was made
    if response.choices[0].message.function_call:
        function_call = response.choices[0].message.function_call.name

        if function_call == "fetch_cdx_data":
            args = json.loads(response.choices[0].message.function_call.arguments)
            url = args["url"]
            cdxData = fetch_cdx_data(url)

            # call GPT and give it the cdx data
            st.session_state.messages.append(
                {
                    "role": "function",
                    "name": "fetch_cdx_data",
                    "content": cdxData,
                }
            )
            print(st.session_state.messages)
            # Check if the assistant's response contains valid content
            if response.choices[0].message.content:
                response_content = response.choices[0].message.content
            else:
                response_content = "No response content available"

            # st.chat_message("function").write(cdxData)
            response2 = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=st.session_state.messages,
                functions=[schema_cdx_data, schema_fetch_data],
            )

            msg2 = response2.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": msg2})
            st.chat_message("assistant").write(msg2)

        elif function_call == "fetch_and_extract_text":
            args = json.loads(response.choices[0].message.function_call.arguments)
            url = args["url"]
            text_content = fetch_and_extract_text(url)

            st.session_state.messages.append(
                {
                    "role": "function",
                    "name": "fetch_and_extract_text",
                    "content": text_content,
                }
            )

            response_content = (
                response.choices[0].message.content
                if response.choices[0].message.content
                else "No response content available"
            )
            response2 = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=st.session_state.messages,
                functions=[schema_cdx_data, schema_fetch_data],
            )

            msg2 = response2.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": msg2})
            st.chat_message("assistant").write(msg2)
    else:
        # Extract the message from the response
        msg = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)
