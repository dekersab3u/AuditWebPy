import tkinter as tk
from tkinter import ttk, messagebox
import threading

from ..tools.Crawler import Crawler
from ..tools.Vectoriseur import Vectoriseur


class AuditWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Audit Web - Projet Python")
        self.geometry("1000x700")

        # Variables de stockage des résultats
        self.crawler = None
        self.vectoriseur = None

        # --- Zone du haut : Saisie URL et Bouton ---
        top_frame = tk.Frame(self, pady=10)
        top_frame.pack(fill="x")

        tk.Label(top_frame, text="URL à auditer :").pack(side="left", padx=10)

        self.url_entry = tk.Entry(top_frame, width=50)
        self.url_entry.insert(0, "")  # Valeur par défaut
        self.url_entry.pack(side="left", padx=5)

        self.btn_start = tk.Button(top_frame, text="Lancer l'Audit", command=self.start_audit_thread)
        self.btn_start.pack(side="left", padx=10)

        self.lbl_status = tk.Label(top_frame, text="Prêt", fg="grey")
        self.lbl_status.pack(side="left", padx=10)

        # --- Zone centrale : Les Onglets (Notebook) ---
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Création des onglets (vides pour l'instant)
        self.tab_logs = tk.Frame(self.notebook)
        self.tab_links = tk.Frame(self.notebook)
        self.tab_cloud = tk.Frame(self.notebook)
        self.tab_graph = tk.Frame(self.notebook)
        self.tab_matrix = tk.Frame(self.notebook)

        self.notebook.add(self.tab_logs, text="Logs & Infos")
        self.notebook.add(self.tab_links, text="Liens Cassés")
        self.notebook.add(self.tab_cloud, text="Nuage de Mots")
        self.notebook.add(self.tab_graph, text="Graphe du Site")
        self.notebook.add(self.tab_matrix, text="Matrice Proximité")

        # Ajout d'une zone de texte simple dans le premier onglet pour voir ce qu'il se passe
        self.log_text = tk.Text(self.tab_logs, state='disabled')
        self.log_text.pack(fill="both", expand=True)

    def log(self, message):
        """Affiche un message dans l'onglet Logs"""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def start_audit_thread(self):
        """Lance l'audit dans un thread séparé pour ne pas geler l'interface"""
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Erreur", "Veuillez entrer une URL valide.")
            return

        self.btn_start.config(state="disabled")
        self.lbl_status.config(text="Audit en cours...", fg="blue")
        self.log("--- Démarrage de l'audit ---")

        # On utilise un Thread pour que la fenêtre ne "plante" pas pendant le chargement
        threading.Thread(target=self.run_process, args=(url,), daemon=True).start()

    def run_process(self, url):
        try:
            # 1. Lancement du Crawler
            self.log(f"Crawling de {url} en cours...")
            self.crawler = Crawler(url)
            self.crawler.run()

            nb_pages = len(self.crawler.get_results())
            self.log(f"Crawl terminé. {nb_pages} pages trouvées.")

            # 2. Lancement du Vectoriseur
            self.log("Analyse mathématique (Vectorisation)...")
            # On récupère les résultats ET le graphe du crawler
            self.vectoriseur = Vectoriseur(self.crawler.get_results(), self.crawler.get_graph())

            self.log("Calculs terminés.")

            # 3. Mise à jour de l'interface (doit se faire sur le thread principal idéalement,
            # mais pour l'instant on reste simple)
            self.lbl_status.config(text="Terminé", fg="green")
            self.btn_start.config(state="normal")

            # ICI : On appellera les fonctions pour afficher les graphiques plus tard

        except Exception as e:
            self.log(f"ERREUR FATALE : {e}")
            print(e)  # Pour le debug console
            self.lbl_status.config(text="Erreur", fg="red")
            self.btn_start.config(state="normal")


if __name__ == "__main__":
    app = AuditWindow()
    app.mainloop()