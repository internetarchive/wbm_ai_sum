import requests
import json


def fetch_cdx_data(
    url,
    match_type="exact",
    limit=10,
    fields=None,
    filters=None,
    from_timestamp=None,
    to_timestamp=None,
) -> str:
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
