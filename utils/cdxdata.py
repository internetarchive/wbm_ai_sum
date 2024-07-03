import requests
import json


def fetch_cdx_data(
    url: str,
    match_type="exact",
    limit=10,
    fields=None,
    filters=None,
    from_timestamp=None,
    to_timestamp=None,
) -> str:
    """
    Fetches CDX (Capture Index) data from the Wayback Machine for a given URL.

    This function queries the Wayback Machine's CDX server to retrieve historical
    information about captures of a specified URL. It allows for various query
    parameters to filter and customize the results.

    :param url: The URL to fetch CDX data for. This should be a full URL including
                the protocol.
    :return: A JSON string containing the CDX data if successful, or a dictionary
             with an 'error' key describing the failure reason.
    """
    base_url = "http://web.archive.org/cdx/search/cdx"
    params = {"url": url, "output": "json", "limit": limit, "matchType": match_type}

    if fields:
        params["fl"] = ",".join(fields)
    if filters:
        params.update({"filter": filters})
    if from_timestamp:
        params["from"] = from_timestamp
    if to_timestamp:
        params["to"] = to_timestamp

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        if response.status_code == 200:
            cdx_data = response.json()
            cdx_data = json.dumps(cdx_data)
            if cdx_data:
                return cdx_data
            else:
                return {"error": "No CDX data found for this URL."}
        else:
            return {
                "error": f"Failed to retrieve CDX data. Status code: {response.status_code}"
            }

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
