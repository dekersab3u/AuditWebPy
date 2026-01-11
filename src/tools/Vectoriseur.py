import numpy as np
import re
import math
from collections import Counter

STOP_WORDS = {
    "le", "la", "les", "de", "des", "du", "un", "une", "et", "ou", "en",
    "à", "pour", "par", "dans", "sur", "avec", "sans", "sous", "ce",
    "cet", "cette", "ces", "qui", "que", "quoi", "dont", "où", "mais",
    "donc", "or", "ni", "car", "je", "tu", "il", "elle", "nous", "vous",
    "ils", "elles", "mon", "ton", "son", "ma", "ta", "sa", "mes", "tes",
    "ses", "notre", "votre", "leur", "nos", "vos", "leurs", "aux", "est",
    "sont", "c'est", "plus", "pas", "ne", "se", "y", "été", "avoir", "être"
}

class Vectoriseur:
    def __init__(self, crawl_results, graph_dict):
        self.documents = crawl_results  # [(url, text), ...]
        self.vocabulaire = sorted(list(self._build_vocab()))
        self.tf_raw_matrix = self._build_raw_counts()
        self.graph = graph_dict
        self.urls = [doc[0] for doc in self.documents]

    def _tokenize(self, text):
        raw_tokens = re.findall(r'\b\w{2,}\b', text.lower())
        tokens = [mot for mot in raw_tokens if mot not in STOP_WORDS and not mot.isdigit()]
        return tokens

    def _build_vocab(self):
        vocab = set()
        for _, text in self.documents:
            mots = self._tokenize(text)
            vocab.update(mots)
        return vocab

    def _build_raw_counts(self):
        nb_docs = len(self.documents)
        nb_mots = len(self.vocabulaire)

        matrice = np.zeros((nb_docs, nb_mots), dtype=int)

        for i, (_, text) in enumerate(self.documents):
            compteur = Counter(self._tokenize(text))

            for j, mot in enumerate(self.vocabulaire):
                if mot in compteur:
                    matrice[i][j] = compteur[mot]

        return matrice

    def get_top_n_words(self, n=10):
        total_par_mot = np.sum(self.tf_raw_matrix, axis=0)

        mots_scores = []
        for i, mot in enumerate(self.vocabulaire):
            mots_scores.append((mot, total_par_mot[i]))

        mots_scores.sort(key=lambda x: x[1], reverse=True)

        return mots_scores[:n]

    def get_tfidf_matrix(self):

        nb_docs, nb_mots = self.tf_raw_matrix.shape

        row_sums = self.tf_raw_matrix.sum(axis=1)[:, np.newaxis]
        tf = self.tf_raw_matrix / (row_sums + 1e-9)

        doc_count_containing_word = np.count_nonzero(self.tf_raw_matrix, axis=0)

        idf = np.log(nb_docs / (doc_count_containing_word + 1))

        tfidf_matrix = tf * idf

        return tfidf_matrix

    def get_similarity_matrix(self):

        matrice_tfidf = self.get_tfidf_matrix()
        norm = np.linalg.norm(matrice_tfidf, axis=1)
        normalized_tfidf = matrice_tfidf / (norm[:, np.newaxis] + 1e-9)
        similarity_matrix = np.dot(normalized_tfidf, normalized_tfidf.T)
        return similarity_matrix

    def get_adjacency_matrix(self):
        """
        matrice d'adjacence du graphe web.
        M[i][j] = 1 si l'URL i contient un lien vers l'URL j.
        """
        n = len(self.urls)
        adj_matrix = np.zeros((n, n), dtype=int)

        url_to_index = {url: i for i, url in enumerate(self.urls)}
        for i, source_url in enumerate(self.urls):
            targets = self.graph.get(source_url, [])

            for target_url in targets:
                if target_url in url_to_index:
                    j = url_to_index[target_url]
                    adj_matrix[i][j] = 1

        return adj_matrix


"""
import numpy as np
from numpy import array
import Compteur

class Vecteuriseur:
    # liste de compteur (=traitement fichiers), ens de mots, matrice
    def __init__(self):
        self.compteurs = []
        self.ens_mots = set()
        self.matrice = None

    def add(self):
        # ajouter un compteur à la liste des compteurs
        self.compteurs.append(Compteur())

    def build_array(self):
        #initialiser la matrice avec des zéros
        self.ens_mots = set()
        res = np.zeros((len(self.ens_mots), len(self.get_word_list())), dtype=int)
        c = 0
        for wc in self.compteurs:
            l = 0
            for mot in self.get_word_list():
                res[l][c] = wc.mots.get(mot, 0)
                l += 1
            c += 1
        return res

    def get_word_list(self):
        # retourner la liste des mots
        return list(self.ens_mots)
"""

