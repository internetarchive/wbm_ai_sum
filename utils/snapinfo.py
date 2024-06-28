import requests

def get_snapshot_data(url, timestamp, job_id):
    """
    Retrieves the HTML, CSS, and other data for a specific snapshot of a web page from the Wayback Machine.

    Args:
        url (str): The URL of the web page.
        timestamp (str): The timestamp of the snapshot in the format "YYYYMMDDhhmmss".
        job_id (str): The job ID associated with the snapshot (optional).

    Returns:
        str: The HTML, CSS, and other data for the specified snapshot.
    """
    base_url = "https://web.archive.org/web"
    snapshot_url = f"{base_url}/{timestamp}id_{job_id}/{url}"

    response = requests.get(snapshot_url)

    if response.status_code == 200:
        return response.text
    else:
        return f"Error: {response.status_code} - {response.reason}"

if __name__ == "__main__":
    # Example usage
    url = "http://example.org/"
    timestamp = "20240104000803"
    job_id = ""  # Leave empty if no job ID is available

    snapshot_data = get_snapshot_data(url, timestamp, job_id)
    print(snapshot_data)