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

    def crawl_page(self, current_url_obj, source_url=None):
        url_str = current_url_obj.normalize()

        if url_str in self.visited:
            return
        self.visited.add(url_str)

        logging.info(f"Scan de : {url_str}")
        print(f"Scan de : {url_str}")  # console
        try:
            # connexion
            response = requests.get(url_str, timeout=5)

            # Lien cassé
            if not response.ok:
                print(f" -> Lien cassé ({response.status_code}) trouvé sur {source_url}")
                if source_url:
                    self.broken_links.append((source_url, url_str, response.status_code))
                return  # On arrête le traitement de cette page ici

            # Vérification type (HTML)
            if "text/html" not in response.headers.get("Content-Type", ""):
                return

            soup = BeautifulSoup(response.text, 'html.parser')
            texte_propre = self.extract_text(soup)
            self.save(texte_propre, url_str)

            for link_tag in soup.find_all("a", href=True):
                raw_href = link_tag["href"]

                # url courante comme base
                next_url_obj = Url(raw_href, base_url=url_str)

                # suit lien si interne
                if next_url_obj.is_internal(self.base_url):
                    self.crawl_page(next_url_obj, source_url=url_str)

        except requests.exceptions.RequestException as e:
            print(f" -> Erreur connexion sur {url_str}")
            if source_url:
                self.broken_links.append((source_url, url_str, "Erreur Connexion"))

    def run(self):
            """Lance le crawl à partir de l'URL de base."""
            print(f"Démarrage du crawl sur {self.base_url.normalize()}")
            self.crawl_page(self.base_url)

    def save(self, text, url):
            """Stocke le résultat."""
            self.output_dir.append((url, text))

    def get_results(self):
            return self.output_dir

    def get_broken_links(self):
            return self.broken_links