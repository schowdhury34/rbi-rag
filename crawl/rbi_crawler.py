# crawl/rbi_crawler.py — RBI circular crawler (skeleton)
import requests
from bs4 import BeautifulSoup
import logging

log = logging.getLogger(__name__)


class RBICrawler:
    def __init__(self):
        self.session = requests.Session()

    def fetch_index(self):
        # TODO: implement
        pass

    def download_pdf(self, url, filename):
        # TODO: implement
        pass

    def run(self):
        # TODO: orchestrate crawl
        pass
