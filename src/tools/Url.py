from urllib.parse import urlparse, urlunparse, urljoin


class Url:
    def __init__(self, url, base_url=None):
        """
        :param url: L'URL brute (chaîne de caractères)
        :param base_url: (Optionnel) Une chaîne représentant l'URL de la page courante.
                         Nécessaire pour reconstruire les liens relatifs.
        """
        if base_url:
            self.url = urljoin(base_url, url)
        else:
            self.url = url

        parsed = urlparse(self.url)
        self.scheme = parsed.scheme  # http ou https
        self.domain = parsed.netloc  # ex: www.univ-lorraine.fr
        self.path = parsed.path  # ex: /formation/index.html

    def normalize(self):
        """
        Nettoie l'URL : met le domaine en minuscule, supprime les fragments (#ancre).
        :return: Une chaîne de caractères de l'URL normalisée.
        """
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
        """
        Vérifie si l'URL courante appartient au même domaine que l'URL de base.
        :param base_url_obj: Un objet Url ou une chaîne représentant le site audité.
        """

        if isinstance(base_url_obj, str):
            base_domain = urlparse(base_url_obj).netloc
        else:
            base_domain = base_url_obj.domain

        if not self.domain:
            return True

        # nettoyage
        clean_base = base_domain.replace("www.", "").lower()
        clean_current = self.domain.replace("www.", "").lower()

        return clean_base == clean_current or clean_current.endswith("." + clean_base)

    def __str__(self):
        return self.url

    def __repr__(self):
        return f"Url('{self.url}')"