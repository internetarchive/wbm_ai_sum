from typing import Optional
import logging
from utils.fetch_data_wayback import fetch_data_wayback
from utils.cdxdata import fetch_cdx_data
from utils.extract_text import fetch_and_extract_text
from utils.trend_analysis import get_trend_analysis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WaybackService:
    def fetch_cdx_data(self, url, limit=None):
        logger.info(f"Fetching CDX data for URL: {url}")
        return fetch_cdx_data(url, limit=limit)

    def fetch_and_extract_text(self, url):
        return fetch_and_extract_text(url)

    def get_trend_analysis(self, url):
        print("url", url)
        return get_trend_analysis(url)

    def fetch_data_wayback(self, url, time=None):
        return fetch_data_wayback(url, timestamp=time)
