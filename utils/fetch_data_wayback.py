from datetime import datetime, timedelta
import logging
import streamlit as st
import streamlit.components.v1 as components
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
from mcmetadata import extract
import json
from utils.cdxdata import fetch_cdx_data
from typing import Optional, Dict, Any
from functools import lru_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@lru_cache(maxsize=100)
def get_latest_timestamp(url: str) -> str:
    """
    Fetches the latest snapshot timestamp for a given URL.

    :param url: The URL to fetch the timestamp for.
    :return: The latest snapshot timestamp.
    :raises ValueError: If no snapshot data is available.
    """
    cdx_data = fetch_cdx_data(url=url, limit=100)
    cdx_json = json.loads(cdx_data)

    if isinstance(cdx_json, dict) and "error" in cdx_json:
        raise ValueError(f"Error fetching CDX data: {cdx_json['error']}")
    if len(cdx_json) < 2:
        raise ValueError("No snapshot data available for this URL")

    return cdx_json[1][1]


def fetch_wayback_content(wayback_url: str) -> str:
    """
    Fetches content from a Wayback Machine URL.

    :param wayback_url: The Wayback Machine URL to fetch.
    :return: The fetched HTML content.
    :raises requests.RequestException: If there's an error fetching the content.
    """
    response = urlopen(wayback_url)
    if response.status != 200:
        raise requests.RequestException(
            f"HTTP Error {response.status}: {response.reason}"
        )
    return response.read()


def clean_text(text: str) -> str:
    """
    Cleans up extracted text.

    :param text: The text to clean.
    :return: Cleaned text.
    """
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return "\n".join(chunk for chunk in chunks if chunk)


def extract_metadata(url: str, text: str) -> Dict[str, Any]:
    """
    Extracts metadata from the given text using mcmetadata.

    :param url: The URL of the webpage.
    :param text: The text content to extract metadata from.
    :return: A dictionary containing the extracted metadata.
    """
    metadata = extract(url=url, html_text=text)
    return {
        "title": metadata.get("normalized_article_title", ""),
        "visible_text": metadata.get("text_content", ""),
    }


@st.cache_data(max_entries=100, show_spinner=False)
def get_snapshot_within_month(url: str, target_timestamp: str) -> str:
    """
    Fetches a snapshot timestamp within one month of the target timestamp.

    :param url: The URL to fetch the timestamp for.
    :param target_timestamp: The target timestamp in "YYYYMMDDhhmmss" format.
    :return: The closest snapshot timestamp within one month.
    :raises ValueError: If no snapshot data is available.
    """
    target_date = datetime.strptime(target_timestamp, "%Y%m%d%H%M%S")
    from_date = (target_date - timedelta(days=15)).strftime("%Y%m%d%H%M%S")
    to_date = (target_date + timedelta(days=15)).strftime("%Y%m%d%H%M%S")
    logger.info(f"Fetching snapshots between {from_date} and {to_date}...")

    cdx_data = fetch_cdx_data(
        url=url, limit=100, from_timestamp=from_date, to_timestamp=to_date
    )
    # cdx_json = json.loads(cdx_data)

    if isinstance(cdx_data, dict) and "error" in cdx_data:
        raise ValueError(f"Error fetching CDX data: {cdx_data['error']}")

    if not cdx_data:
        raise ValueError("No snapshot data available for this URL")

    cdx_json = json.loads(cdx_data)

    if isinstance(cdx_json, dict) and "error" in cdx_json:
        raise ValueError(f"Error fetching CDX data: {cdx_json['error']}")
    if len(cdx_json) < 2:
        raise ValueError("No snapshot data available for this URL")

    # Find the closest timestamp to the target
    closest_snapshot = min(
        cdx_json,
        key=lambda x: abs(datetime.strptime(x[1], "%Y%m%d%H%M%S") - target_date),
    )

    return closest_snapshot[1]


def fetch_data_wayback(
    url: str, timestamp: Optional[str] = None, debug: bool = True
) -> str:
    """
    Fetches a webpage from the Wayback Machine and extracts its main textual content.

    :param url: The URL of the webpage to fetch and extract text from.
    :param timestamp: The timestamp of the snapshot in the format "YYYYMMDDhhmmss".
                      If None, the latest snapshot will be used.
    :param debug: If True, print debug information.
    :return: A string containing the extracted text content, or an empty string
             if an error occurs during fetching or processing.
    """
    try:
        logger.info(f"Fetching content for: {url}")
        logger.info(f"Fetching content for the time: {timestamp}")

        if timestamp:
            timestamp = get_snapshot_within_month(url, timestamp)
        else:
            timestamp = get_latest_timestamp(url)

        logger.info(f"Using snapshot timestamp: {timestamp}")
        if debug:
            logger.debug(f"Using snapshot timestamp: {timestamp}")

        wayback_url = f"https://web.archive.org/web/{timestamp}id_/{url}"
        if debug:
            logger.debug(f"Fetching content from: {wayback_url}")

        with st.chat_message("assistant", avatar="assets/favicon.ico"):
            st.write("Here's the Wayback Machine rendering of the page:")
            components.iframe(wayback_url, width=700, height=500, scrolling=True)

        logger.info(f"Fetching html content from: {wayback_url}")

        html = fetch_wayback_content(wayback_url)
        soup = BeautifulSoup(html, features="html.parser")
        for script in soup(["script", "style"]):
            script.extract()

        text = clean_text(soup.get_text())

        if debug:
            logger.debug(f"Extracted text length: {len(text)} characters")

        metadata = extract_metadata(url, text)

        text_content = "\n".join([metadata["title"], metadata["visible_text"]])

        if len(text_content.strip()) < 50:
            raise ValueError("Content is too short")

        return text_content.strip()

    except (requests.RequestException, ValueError) as e:
        logger.error(f"Error processing {url}: {e}")
        if debug and "text" in locals():
            logger.debug(
                f"Extracted text: {text[:500]}..."
            )  # Print first 500 characters
        return ""
    except Exception as e:
        logger.error(f"Unexpected error processing {url}: {e}")
        return ""


if __name__ == "__main__":
    # print(fetch_data_wayback("https://www.cartoonnetwork.com", debug=True))
    (fetch_data_wayback("http://www.cartoonnetwork.com", "20100101000000", debug=True))
