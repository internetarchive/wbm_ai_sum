import requests
from mcmetadata import extract


def fetch_and_extract_text(url):
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
