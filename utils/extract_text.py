import requests
import logging
from mcmetadata import extract
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def fetch_and_extract_text(url: str) -> Optional[str]:
    """
    Fetches a webpage and extracts its main textual content.

    This function retrieves the HTML content of a given URL, then uses the
    trafilatura library to extract relevant metadata and the main text content.
    It focuses on extracting the title and the visible text content, discarding
    boilerplate elements like navigation, headers, footers, etc.

    :param url: The URL of the webpage to fetch and extract text from.
                This should be a full URL including the protocol.
    :type url: str
    :return: A string containing the extracted text content, or None
             if an error occurs during fetching or processing.
    :rtype: Optional[str]
    """
    try:
        logging.info(f"Fetching content from {url}")
        response = requests.get(url)
        response.raise_for_status()

        encoding = response.encoding if response.encoding else "utf-8"
        html_content = response.content.decode(encoding)
        logging.info(f"Extracting metadata from {url}")
        metadata = extract(url=url, html_text=html_content)

        # Extract relevant metadata
        title = metadata.get("normalized_article_title", "")
        visible_text = metadata.get("text_content", "")

        # Concatenate all parts with newline separators
        text_content = "\n".join([title, visible_text])
        logging.info(f"Successfully extracted text content from {url}")
        return text_content.strip()
    except requests.RequestException as e:
        logging.error(f"Error fetching {url}: {e}")
        return None
    except Exception as e:
        logging.error(f"Error processing HTML content from {url}: {e}")
        return None


# Example usage
if __name__ == "__main__":
    url = "https://edition.cnn.com/"
    text_content = fetch_and_extract_text(url)
    if text_content:
        print("Extracted text content:")
        print(text_content)
    else:
        print("No text content extracted.")
