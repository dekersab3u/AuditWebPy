from urllib.parse import urlparse, urlunparse, urljoin


class Url:
    def __init__(self, url, base_url=None):

        if base_url:
            self.url = urljoin(base_url, url)
        else:
            self.url = url

        parsed = urlparse(self.url)
        self.scheme = parsed.scheme  # http ou https
        self.domain = parsed.netloc  # ex: www.univ-lorraine.fr
        self.path = parsed.path  # ex: /formation/index.html

    def normalize(self):
        if not self.url:
            return ""

        parsed = urlparse(self.url)

        normalized = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path,
            parsed.params,
            parsed.query,
            ""  # Suppression de l'ancre (#)
        ))


        if normalized.endswith("/"):
            normalized = normalized[:-1]

        return normalized

    def is_internal(self, base_url_obj):

        #Vérifie si l'URL courante appartient au même domaine que l'URL de base.
        if self.scheme not in ["http", "https"]:
            return False

        if isinstance(base_url_obj, str):
            base_domain = urlparse(base_url_obj).netloc
        else:
            base_domain = base_url_obj.domain

        if not self.domain:
            return True
        current_domain = self.domain.lower()
        # nettoyage
        if base_domain.startswith("www."):
            base_domain = base_domain[4:]

        if current_domain.startswith("www."):
            current_domain = current_domain[4:]

        return base_domain == current_domain

    def __str__(self):
        return self.url

    def __repr__(self):
        return f"Url('{self.url}')"