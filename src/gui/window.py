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
        self.geometry("1280x720")

        self.crawler = None
        self.vectoriseur = None

        top_frame = tk.Frame(self, pady=10)
        top_frame.pack(fill="x")

        tk.Label(top_frame, text="URL à auditer :").pack(side="left", padx=10)

        self.url_entry = tk.Entry(top_frame, width=50)
        self.url_entry.insert(0, "")  # Valeur par défaut
        self.url_entry.pack(side="left", padx=5)

        tk.Label(top_frame, text="Max Pages :").pack(side="left", padx=5)
        self.max_pages_entry = tk.Entry(top_frame, width=5)
        self.max_pages_entry.insert(0, "60")  # Valeur par défaut
        self.max_pages_entry.pack(side="left", padx=5)

        self.btn_start = tk.Button(top_frame, text="Lancer l'Audit", command=self.start_audit_thread)
        self.btn_start.pack(side="left", padx=10)

        self.lbl_status = tk.Label(top_frame, text="Prêt", fg="grey")
        self.lbl_status.pack(side="left", padx=10)

        self.lbl_counter = tk.Label(top_frame, text="Pages : 0", font=("Arial", 16, "bold"), fg="blue", borderwidth=2)
        self.lbl_counter.pack(side="right", padx=20)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_logs = tk.Frame(self.notebook)
        self.tab_links = tk.Frame(self.notebook)
        self.tab_cloud = tk.Frame(self.notebook)
        self.tab_words_table = tk.Frame(self.notebook)  # tableau mots
        self.tab_graph = tk.Frame(self.notebook)
        self.tab_matrix = tk.Frame(self.notebook)

        self.notebook.add(self.tab_logs, text="Logs & Infos")
        self.notebook.add(self.tab_links, text="Liens cassés")
        self.notebook.add(self.tab_cloud, text="Nuage de mots")
        self.notebook.add(self.tab_words_table, text="Tableau Mots")
        self.notebook.add(self.tab_graph, text="Graphe du site")
        self.notebook.add(self.tab_matrix, text="Matrice de proximité")

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

        # recup max pages
        try:
            max_p = int(self.max_pages_entry.get())
        except ValueError:
            messagebox.showerror("Erreur", "Le nombre de pages max doit être un entier.")
            return

        if not url:
            messagebox.showerror("Erreur", "Veuillez entrer une URL valide.")
            return

        self.btn_start.config(state="disabled")
        self.lbl_status.config(text="Audit en cours...", fg="blue")
        self.lbl_counter.config(text="Pages : 0")  # Reset compteur
        self.log("--- Démarrage de l'audit ---")
        threading.Thread(target=self.run_process, args=(url, max_p), daemon=True).start()

    def update_counter_ui(self, count):
        """Callback appelé par le Crawler pour mettre à jour l'interface"""
        self.after(0, lambda: self.lbl_counter.config(text=f"Pages trouvées : {count}"))

    def _create_scrollable_area(self, parent_tab):
        """
        Utilitaire pour nettoyer un onglet et y ajouter des scrollbars.
        Renvoie une 'frame' interne où l'on peut dessiner les graphiques.
        """
        # 1. Nettoyage
        for widget in parent_tab.winfo_children():
            widget.destroy()

        # 2. Création du conteneur principal
        container = tk.Frame(parent_tab)
        container.pack(fill="both", expand=True)

        # 3. Création du Canvas et des Scrollbars
        canvas = tk.Canvas(container, bg="white")
        v_scroll = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        h_scroll = tk.Scrollbar(container, orient="horizontal", command=canvas.xview)

        canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        # 4. Placement via Grid (pour que les scrollbars collent aux bords)
        canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        # Configuration du poids pour que le canvas prenne toute la place
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # 5. Création de la Frame interne (C'est là qu'on mettra le graphe)
        inner_frame = tk.Frame(canvas, bg="white")

        # On crée une fenêtre dans le canvas qui contient la frame
        canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        # 6. Fonction pour mettre à jour la zone de scroll quand le contenu change
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        inner_frame.bind("<Configure>", configure_scroll_region)

        # Optionnel : Centrage si le contenu est plus petit que la fenêtre

        def center_content(event):
            canvas_width = event.width
            canvas_height = event.height
            frame_width = inner_frame.winfo_reqwidth()
            frame_height = inner_frame.winfo_reqheight()

            # Si le graphe est plus petit que la fenêtre, on centre
            x_pos = max(0, (canvas_width - frame_width) // 2)
            # Pour Y, on laisse souvent en haut, mais on peut centrer aussi :
            y_pos = max(0, (canvas_height - frame_height) // 2)

            # Déplacement de la fenêtre interne
            canvas.coords(canvas_window, x_pos, y_pos)

        canvas.bind("<Configure>", center_content)

        return inner_frame

    def display_broken_links(self):
        for widget in self.tab_links.winfo_children():
            widget.destroy()

        links = self.crawler.get_broken_links()

        if not links:
            tk.Label(self.tab_links, text="Aucun lien cassé trouvé !", fg="green", font=("Arial", 14)).pack(
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
            tk.Label(self.tab_cloud, text="Pas assez de mots.", fg="red").pack()
            return

        # wordcloud
        wc = WordCloud(width=800, height=500, background_color='white').generate_from_frequencies(word_dict)

        # Affichage Matplotlib
        fig = plt.Figure(figsize=(6, 5), dpi=100)
        ax = fig.add_subplot(111)
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")

        canvas = FigureCanvasTkAgg(fig, master=self.tab_cloud)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def display_words_table(self):
        for widget in self.tab_words_table.winfo_children():
            widget.destroy()

        if self.vectoriseur:
            top_words = self.vectoriseur.get_top_n_words(n=100)
        else:
            return

        if not top_words:
            tk.Label(self.tab_words_table, text="Aucune donnée textuelle analysée.", font=("Arial", 12)).pack(pady=20)
            return

        frame_table = tk.Frame(self.tab_words_table)
        frame_table.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        columns = ("rang", "mot", "count")
        tree = ttk.Treeview(frame_table, columns=columns, show="headings")
        tree.heading("rang", text="#")
        tree.heading("mot", text="Mot trouvé")
        tree.heading("count", text="Fréquence")
        tree.column("rang", width=50, anchor="center")
        tree.column("mot", width=300, anchor="w")  # aligné gauche
        tree.column("count", width=100, anchor="center")

        for i, (mot, score) in enumerate(top_words):
            tree.insert("", tk.END, values=(i + 1, mot, score))

        scrollbar = ttk.Scrollbar(frame_table, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

    def display_graph(self):
        scrollable_frame = self._create_scrollable_area(self.tab_graph)

        adj_matrix = self.vectoriseur.get_adjacency_matrix()
        urls = self.vectoriseur.urls
        #scrollable_frame = self._create_scrollable_area(self.tab_graph)
        labels = {}
        for i, url in enumerate(urls):
            short_name = url.rstrip('/').split('/')[-1]
            if not short_name:
                short_name = "homepage"
            labels[i] = short_name

        graphs = nx.from_numpy_array(adj_matrix, create_using=nx.DiGraph)

        fig = plt.Figure(figsize=(8, 5), dpi=100)
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

        canvas = FigureCanvasTkAgg(fig, master=scrollable_frame)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def display_heatmap(self):
        scrollable_frame = self._create_scrollable_area(self.tab_matrix)

        sim_matrix = self.vectoriseur.get_similarity_matrix()
        urls = self.vectoriseur.urls

        # labels courts
        short_labels = []
        for url in urls:
            name = url.rstrip('/').split('/')[-1]
            if len(name) > 25:
                name = "..." + name[-22:]
            short_labels.append(name if name else "Accueil")


        if len(urls) > 60:
            show_labels = False
            title_suffix = "(Trop de pages pour afficher les noms)"
        else:
            show_labels = True
            title_suffix = ""

        fig = plt.Figure(figsize=(8, 5), dpi=100)
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

        canvas = FigureCanvasTkAgg(fig, master=scrollable_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def run_process(self, url, max_pages):
        try:
            # appel Crawler
            self.log(f"Crawling de {url} en cours...")
            self.crawler = Crawler(url, max_pages=max_pages, progress_callback=self.update_counter_ui)
            self.crawler.run()

            nb_pages = len(self.crawler.get_results())
            self.log(f"Crawl terminé. {nb_pages} pages trouvées.")

            # appel Vectoriseur
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

        # affichage
        self.display_broken_links()
        self.display_word_cloud()
        self.display_words_table()
        self.display_graph()
        self.display_heatmap()

        self.log("Onglets mis à jour.")
        messagebox.showinfo("Succès", "Audit terminé, voir onglets")

if __name__ == "__main__":
    app = AuditWindow()
    app.mainloop()