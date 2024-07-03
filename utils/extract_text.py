import requests
from mcmetadata import extract


def fetch_and_extract_text(url: str) -> str:
    """
    Fetches a webpage and extracts its main textual content.

    This function retrieves the HTML content of a given URL, then uses the
    trafilatura library to extract relevant metadata and the main text content.
    It focuses on extracting the title and the visible text content, discarding
    boilerplate elements like navigation, headers, footers, etc.

    :param url: The URL of the webpage to fetch and extract text from.
                This should be a full URL including the protocol.
    :type url: str
    :return: A string containing the extracted text content, or an empty string
             if an error occurs during fetching or processing.
    :rtype: str
    """
    try:
        response = requests.get(url)
        response.raise_for_status()

        # html_content = response.content
        encoding = response.encoding if response.encoding else "utf-8"
        html_content = response.content.decode(encoding)
        # print(html_content)
        metadata = extract(url=url, html_text=html_content)
        print(metadata)
        # Extract relevant metadata
        title = metadata.get("normalized_article_title", "")
        # meta_description = metadata.get("description", "")
        # meta_keywords = metadata.get("keywords", "")
        visible_text = metadata.get("text_content", "")

        # Concatenate all parts with newline separators
        # text_content = "\n".join([title, meta_description, meta_keywords, visible_text])
        text_content = "\n".join([title, visible_text])
        return text_content.strip()
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return ""
    except Exception as e:
        print(f"Error processing HTML content from {url}: {e}")
        return ""


# Example usage
if __name__ == "__main__":
    url = "https://edition.cnn.com/"
    text_content = fetch_and_extract_text(url)
    if text_content:
        print("Extracted text content:")
        print(text_content)
    else:
        print("No text content extracted.")
