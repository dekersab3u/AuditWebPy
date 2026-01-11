import tkinter as tk
from tkinter import ttk, messagebox
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx
from wordcloud import WordCloud

from ..tools.Crawler import Crawler
from ..tools.Vectoriseur import Vectoriseur


class AuditWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Audit Web - Projet Python")
        self.geometry("1000x700")

        self.crawler = None
        self.vectoriseur = None

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

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

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

        self.log_text = tk.Text(self.tab_logs, state='disabled')
        self.log_text.pack(fill="both", expand=True)

    def log(self, message):
        #message dans onglet logs
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def start_audit_thread(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Erreur", "Veuillez entrer une URL valide.")
            return

        self.btn_start.config(state="disabled")
        self.lbl_status.config(text="Audit en cours...", fg="blue")
        self.log("--- Démarrage de l'audit ---")

        threading.Thread(target=self.run_process, args=(url,), daemon=True).start()

    def display_broken_links(self):
        for widget in self.tab_links.winfo_children():
            widget.destroy()

        links = self.crawler.get_broken_links()

        if not links:
            tk.Label(self.tab_links, text="Aucun lien cassé trouvé ! Bravo.", fg="green", font=("Arial", 14)).pack(
                pady=20)
            return

        columns = ("source", "target", "code")
        tree = ttk.Treeview(self.tab_links, columns=columns, show="headings")

        tree.heading("source", text="Page d'origine")
        tree.heading("target", text="Lien mort")
        tree.heading("code", text="Erreur")

        tree.column("source", width=300)
        tree.column("target", width=300)
        tree.column("code", width=100)

        for src, tgt, code in links:
            tree.insert("", tk.END, values=(src, tgt, code))

        scrollbar = ttk.Scrollbar(self.tab_links, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

    def display_word_cloud(self):
        for widget in self.tab_cloud.winfo_children():
            widget.destroy()

        top_words = self.vectoriseur.get_top_n_words(n=100)
        word_dict = {mot: score for mot, score in top_words}

        if not word_dict:
            tk.Label(self.tab_cloud, text="Pas assez de données pour le nuage.", fg="red").pack()
            return

        # Génération du nuage
        wc = WordCloud(width=800, height=500, background_color='white').generate_from_frequencies(word_dict)

        # Affichage Matplotlib
        fig = plt.Figure(figsize=(6, 5), dpi=100)
        ax = fig.add_subplot(111)
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")

        canvas = FigureCanvasTkAgg(fig, master=self.tab_cloud)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def display_graph(self):
        for widget in self.tab_graph.winfo_children():
            widget.destroy()

        adj_matrix = self.vectoriseur.get_adjacency_matrix()
        urls = self.vectoriseur.urls

        labels = {}
        for i, url in enumerate(urls):
            short_name = url.rstrip('/').split('/')[-1]
            if not short_name:
                short_name = "homepage"
            labels[i] = short_name

        graphs = nx.from_numpy_array(adj_matrix, create_using=nx.DiGraph)

        fig = plt.Figure(figsize=(6, 5), dpi=100)
        ax = fig.add_subplot(111)


        try:
            pos = nx.spring_layout(graphs, k=0.5, iterations=20)
            """
            nx.draw(graphs, pos, ax=ax, with_labels=True, node_size=300,
                    node_color='skyblue', font_size=8, arrows=True, edge_color='gray')
            """
            nx.draw_networkx_nodes(graphs, pos, ax=ax, node_size=500, node_color='lightblue')
            nx.draw_networkx_edges(graphs, pos, ax=ax, edge_color='gray', arrows=True)
            nx.draw_networkx_labels(graphs, pos, labels, ax=ax, font_size=8, font_weight="bold")

            ax.set_title("Structure des liens (Interne)", fontsize=10)
            ax.axis("off")

        except Exception as e:
            ax.text(0.5, 0.5, f"Erreur graphe: {str(e)}", ha='center')

        canvas = FigureCanvasTkAgg(fig, master=self.tab_graph)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def display_heatmap(self):
        for widget in self.tab_matrix.winfo_children():
            widget.destroy()

        sim_matrix = self.vectoriseur.get_similarity_matrix()
        urls = self.vectoriseur.urls

        # labels courts
        short_labels = []
        for url in urls:
            name = url.rstrip('/').split('/')[-1]
            short_labels.append(name if name else "Accueil")

        if len(urls) > 60:
            show_labels = False
            title_suffix = "(Trop de pages pour afficher les noms)"
        else:
            show_labels = True
            title_suffix = ""

        fig = plt.Figure(figsize=(6, 5), dpi=100)
        ax = fig.add_subplot(111)

        cax = ax.matshow(sim_matrix, cmap='viridis')
        fig.colorbar(cax)

        ax.set_title(f"Similarité (Cosinus) {title_suffix}", fontsize=10)

        if show_labels:

            ax.set_xticks(range(len(short_labels)))
            ax.set_yticks(range(len(short_labels)))


            ax.set_xticklabels(short_labels, rotation=90, fontsize=8)
            ax.set_yticklabels(short_labels, fontsize=8)
        else:
            ax.set_xlabel("Index Page")
            ax.set_ylabel("Index Page")

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.tab_matrix)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def run_process(self, url):
        try:
            # 1. Lancement du Crawler
            self.log(f"Crawling de {url} en cours...")
            self.crawler = Crawler(url, max_pages=60)
            self.crawler.run()

            nb_pages = len(self.crawler.get_results())
            self.log(f"Crawl terminé. {nb_pages} pages trouvées.")

            # 2. Lancement du Vectoriseur
            self.log("Analyse mathématique (Vectorisation)...")
            self.vectoriseur = Vectoriseur(self.crawler.get_results(), self.crawler.get_graph())

            self.log("Calculs terminés.")

            self.after(0, self.update_ui_after_audit)

        except Exception as e:
            self.log(f"ERREUR FATALE : {e}")
            print(e)
            self.after(0, lambda: self.lbl_status.config(text="Erreur", fg="red"))
            self.after(0, lambda: self.btn_start.config(state="normal"))

            self.lbl_status.config(text="Terminé", fg="green")
            self.btn_start.config(state="normal")



        """except Exception as e:
            self.log(f"ERREUR FATALE : {e}")
            print(e)  # Pour le debug console
            self.lbl_status.config(text="Erreur", fg="red")
            self.btn_start.config(state="normal")"""

    def update_ui_after_audit(self):
        self.lbl_status.config(text="Audit terminé ", fg="green")
        self.btn_start.config(state="normal")

        # Appel des fonctions d'affichage
        self.display_broken_links()
        self.display_word_cloud()
        self.display_graph()
        self.display_heatmap()

        self.log("Onglets mis à jour.")
        messagebox.showinfo("Succès", "Audit terminé, voir onglets")

if __name__ == "__main__":
    app = AuditWindow()
    app.mainloop()