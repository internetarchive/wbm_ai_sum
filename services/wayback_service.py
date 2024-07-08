from utils.cdxdata import fetch_cdx_data
from utils.extract_text import fetch_and_extract_text
from utils.trend_analysis import get_trend_analysis


class WaybackService:
    def fetch_cdx_data(self, url):
        return fetch_cdx_data(url)

    def fetch_and_extract_text(self, url):
        return fetch_and_extract_text(url)

    def get_trend_analysis(self, url):
        return get_trend_analysis(url)
