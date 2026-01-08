import logging
import requests
from bs4 import BeautifulSoup
import re

from Url import Url

class Crawler:
    def __init__(self, base_url_str):
        self.base_url = Url(base_url_str)
        self.visited = set()
        self.output_dir = []

        #liens morts pour audit
        self.broken_links = []

    def extract_text(self, soup):
        # soup = doc html
        soup = soup if not isinstance(soup, str) else BeautifulSoup(soup, "html.parser")
        # supprimer les balises non pertinentes
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside", "svg"]):
            tag.decompose()
        text = " ".join(soup.stripped_strings)
        return re.sub(r"\s+", " ", text).strip()