import requests
import json
from datetime import datetime, timezone


def fetch_cdx_data(
    url: str,
    match_type="domain",
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
    print("d1")
    if limit is not None:
        params = {
            "url": url,
            "output": "json",
            "limit": -limit,
            "matchType": match_type,
        }
    else:
        params = {"url": url, "output": "json", "limit": 10, "matchType": match_type}
    print("d2")
    if fields:
        params["fl"] = ",".join(fields)
    if filters:
        params.update({"filter": filters})
    if from_timestamp:
        params["from"] = from_timestamp
    if to_timestamp:
        params["to"] = to_timestamp
    print("d3")
    # # Set from_timestamp to today's date if not provided
    # if not from_timestamp:
    #     today = datetime.now(timezone.utc).strftime("%Y%m%d")
    #     params["from"] = today
    try:
        response = requests.get(base_url, params=params)
        print(response.json())
        response.raise_for_status()
        if response.status_code == 200:
            cdx_data = response.json()
            if cdx_data:
                # Filter out captures with status code other than 200
                filtered_cdx_data = [
                    capture for capture in cdx_data if capture[4] == "200"
                ]
                if filtered_cdx_data:
                    return json.dumps(filtered_cdx_data)
                else:
                    return {
                        "error": "No CDX data found with status code 200 for this URL."
                    }
            else:
                return {"error": "No CDX data found for this URL."}
        else:
            return {
                "error": f"Failed to retrieve CDX data. Status code: {response.status_code}"
            }

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print(fetch_cdx_data("cartoonnetwork.jp", limit=100))
