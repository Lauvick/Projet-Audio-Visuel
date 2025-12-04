"""
🎬 FRÈRE THÉODORE - Application de génération de Shorts
Interface graphique professionnelle avec CustomTkinter

Fonctionnalités:
- Détection vocale automatique de Frère Théodore
- Génération de shorts avec sous-titres mot par mot
- Interface moderne et intuitive
"""

import os
import sys
import threading
import queue
from datetime import datetime

import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk

# Configuration du thème
ctk.set_appearance_mode("dark")  # Mode sombre par défaut
ctk.set_default_color_theme("blue")

# Chemin de base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Import des modules du projet
try:
    from generate_shorts import extract_short
    MODULES_OK = True
except ImportError as e:
    MODULES_OK = False
    IMPORT_ERROR = str(e)


# ============================================================
# COULEURS ET STYLES
# ============================================================
class Colors:
    # Palette principale
    PRIMARY = "#6366F1"       # Indigo
    PRIMARY_HOVER = "#4F46E5"
    SECONDARY = "#10B981"     # Vert émeraude
    SECONDARY_HOVER = "#059669"
    ACCENT = "#F59E0B"        # Orange/Ambre
    
    # Fonds
    BG_DARK = "#0F172A"       # Bleu très foncé
    BG_CARD = "#1E293B"       # Bleu foncé
    BG_CARD_HOVER = "#334155"
    
    # Textes
    TEXT_PRIMARY = "#F8FAFC"
    TEXT_SECONDARY = "#94A3B8"
    TEXT_MUTED = "#64748B"
    
    # États
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    ERROR = "#EF4444"
    INFO = "#3B82F6"


# ============================================================
# COMPOSANTS PERSONNALISÉS
# ============================================================
class ModernCard(ctk.CTkFrame):
    """Carte avec style moderne et ombre."""
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color=Colors.BG_CARD,
            corner_radius=16,
            border_width=1,
            border_color=Colors.BG_CARD_HOVER,
            **kwargs
        )


class GradientButton(ctk.CTkButton):
    """Bouton avec style gradient."""
    def __init__(self, parent, text, command=None, style="primary", **kwargs):
        colors = {
            "primary": (Colors.PRIMARY, Colors.PRIMARY_HOVER),
            "secondary": (Colors.SECONDARY, Colors.SECONDARY_HOVER),
            "accent": (Colors.ACCENT, "#D97706"),
        }
        fg, hover = colors.get(style, colors["primary"])
        
        super().__init__(
            parent,
            text=text,
            command=command,
            fg_color=fg,
            hover_color=hover,
            corner_radius=12,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            **kwargs
        )


class StatusBadge(ctk.CTkLabel):
    """Badge de statut coloré."""
    def __init__(self, parent, text="", status="info", **kwargs):
        colors = {
            "success": Colors.SUCCESS,
            "warning": Colors.WARNING,
            "error": Colors.ERROR,
            "info": Colors.INFO,
        }
        
        super().__init__(
            parent,
            text=f"  {text}  ",
            fg_color=colors.get(status, Colors.INFO),
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="white",
            **kwargs
        )
    
    def set_status(self, text, status="info"):
        colors = {
            "success": Colors.SUCCESS,
            "warning": Colors.WARNING,
            "error": Colors.ERROR,
            "info": Colors.INFO,
        }
        self.configure(text=f"  {text}  ", fg_color=colors.get(status, Colors.INFO))


# ============================================================
# APPLICATION PRINCIPALE
# ============================================================
class ThéodoreApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuration de la fenêtre
        self.title("🎬 Frère Théodore - Générateur de Shorts")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        
        # Couleur de fond
        self.configure(fg_color=Colors.BG_DARK)
        
        # Variables
        self.video_path = tk.StringVar()
        self.processing = False
        self.message_queue = queue.Queue()
        
        # Dossiers
        self.videos_folder = os.path.join(BASE_DIR, "videos_theodore")
        self.shorts_folder = os.path.join(BASE_DIR, "shorts_theodore")
        os.makedirs(self.videos_folder, exist_ok=True)
        os.makedirs(self.shorts_folder, exist_ok=True)
        
        # Créer l'interface
        self.create_ui()
        
        # Vérifier les modules
        self.after(100, self.check_modules)
        
        # Traiter les messages de la queue
        self.process_queue()
    
    def create_ui(self):
        """Crée l'interface utilisateur complète."""
        
        # Container principal avec padding
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # === HEADER ===
        self.create_header()
        
        # === CONTENU PRINCIPAL (2 colonnes) ===
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, pady=(20, 0))
        
        # Colonne gauche (contrôles)
        self.left_panel = ctk.CTkFrame(self.content_frame, fg_color="transparent", width=400)
        self.left_panel.pack(side="left", fill="y", padx=(0, 10))
        self.left_panel.pack_propagate(False)
        
        # Colonne droite (logs et résultats)
        self.right_panel = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # Créer les sections
        self.create_video_section()
        self.create_settings_section()
        self.create_actions_section()
        self.create_stats_section()
        self.create_log_section()
        self.create_shorts_section()
    
    def create_header(self):
        """Crée l'en-tête de l'application."""
        header = ModernCard(self.main_container, height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Contenu du header
        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Logo et titre
        title_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        title_frame.pack(side="left")
        
        # Icône
        icon_label = ctk.CTkLabel(
            title_frame,
            text="🎬",
            font=ctk.CTkFont(size=32)
        )
        icon_label.pack(side="left", padx=(0, 10))
        
        # Titre
        title_text = ctk.CTkFrame(title_frame, fg_color="transparent")
        title_text.pack(side="left")
        
        ctk.CTkLabel(
            title_text,
            text="Frère Théodore",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            title_text,
            text="Générateur de Shorts avec IA",
            font=ctk.CTkFont(size=12),
            text_color=Colors.TEXT_SECONDARY
        ).pack(anchor="w")
        
        # Status badge (droite)
        self.status_badge = StatusBadge(header_content, "Prêt", "success")
        self.status_badge.pack(side="right")
        
        # Bouton thème
        self.theme_btn = ctk.CTkButton(
            header_content,
            text="🌙",
            width=40,
            height=40,
            corner_radius=20,
            fg_color=Colors.BG_CARD_HOVER,
            hover_color=Colors.PRIMARY,
            command=self.toggle_theme
        )
        self.theme_btn.pack(side="right", padx=(0, 15))
    
    def create_video_section(self):
        """Section de sélection de vidéo."""
        card = ModernCard(self.left_panel)
        card.pack(fill="x", pady=(0, 15))
        
        # Titre
        title_frame = ctk.CTkFrame(card, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            title_frame,
            text="📹 Sélection de la vidéo",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(anchor="w")
        
        # Zone de sélection
        select_frame = ctk.CTkFrame(card, fg_color=Colors.BG_DARK, corner_radius=12)
        select_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # Dropdown des vidéos existantes
        self.video_dropdown = ctk.CTkOptionMenu(
            select_frame,
            values=self.get_video_list(),
            variable=self.video_path,
            width=250,
            height=40,
            corner_radius=10,
            fg_color=Colors.BG_CARD,
            button_color=Colors.PRIMARY,
            button_hover_color=Colors.PRIMARY_HOVER,
            dropdown_fg_color=Colors.BG_CARD,
            dropdown_hover_color=Colors.BG_CARD_HOVER
        )
        self.video_dropdown.pack(side="left", padx=10, pady=10)
        
        # Bouton parcourir
        ctk.CTkButton(
            select_frame,
            text="📁",
            width=45,
            height=40,
            corner_radius=10,
            fg_color=Colors.BG_CARD,
            hover_color=Colors.BG_CARD_HOVER,
            command=self.browse_video
        ).pack(side="left", padx=(0, 10), pady=10)
        
        # Bouton refresh
        ctk.CTkButton(
            select_frame,
            text="🔄",
            width=45,
            height=40,
            corner_radius=10,
            fg_color=Colors.BG_CARD,
            hover_color=Colors.BG_CARD_HOVER,
            command=self.refresh_video_list
        ).pack(side="left", padx=(0, 10), pady=10)
        
        # Info vidéo
        self.video_info = ctk.CTkLabel(
            card,
            text="Sélectionnez une vidéo pour commencer",
            font=ctk.CTkFont(size=12),
            text_color=Colors.TEXT_MUTED
        )
        self.video_info.pack(padx=20, pady=(0, 20), anchor="w")
    
    def create_settings_section(self):
        """Section des paramètres de transcription."""
        card = ModernCard(self.left_panel)
        card.pack(fill="x", pady=(0, 15))
        
        # Titre
        ctk.CTkLabel(
            card,
            text="⚙️ Paramètres",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        # Frame pour le sélecteur de modèle
        model_frame = ctk.CTkFrame(card, fg_color="transparent")
        model_frame.pack(fill="x", padx=20, pady=(0, 5))
        
        ctk.CTkLabel(
            model_frame,
            text="Modèle de transcription :",
            font=ctk.CTkFont(size=13),
            text_color=Colors.TEXT_SECONDARY
        ).pack(side="left")
        
        # Variable pour stocker le choix du modèle
        self.model_choice = ctk.StringVar(value="precise")
        
        # Segmented button pour choisir le modèle
        self.model_selector = ctk.CTkSegmentedButton(
            model_frame,
            values=["Rapide", "Précis"],
            variable=self.model_choice,
            command=self.on_model_change,
            selected_color=Colors.PRIMARY,
            selected_hover_color=Colors.PRIMARY_HOVER,
            unselected_color=Colors.BG_CARD_HOVER,
            unselected_hover_color=Colors.BG_CARD_HOVER,
            corner_radius=8,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.model_selector.pack(side="right", padx=(10, 0))
        self.model_selector.set("Précis")  # Valeur par défaut
        
        # Description du modèle sélectionné
        self.model_description = ctk.CTkLabel(
            card,
            text="🎯 Précis (large-v3) : Meilleure qualité, plus lent (~1.5x temps réel)",
            font=ctk.CTkFont(size=11),
            text_color=Colors.TEXT_MUTED,
            wraplength=360,
            justify="left"
        )
        self.model_description.pack(padx=20, pady=(0, 15), anchor="w")
    
    def on_model_change(self, value):
        """Callback quand le modèle est changé."""
        if value == "Rapide":
            self.model_choice.set("fast")
            self.model_description.configure(
                text="⚡ Rapide (small) : Plus rapide (~0.3x temps réel), bonne qualité"
            )
            self.log("📊 Modèle changé : Rapide (small)")
        else:
            self.model_choice.set("precise")
            self.model_description.configure(
                text="🎯 Précis (large-v3) : Meilleure qualité, plus lent (~1.5x temps réel)"
            )
            self.log("📊 Modèle changé : Précis (large-v3)")
    
    def create_actions_section(self):
        """Section des actions principales."""
        card = ModernCard(self.left_panel)
        card.pack(fill="x", pady=(0, 15))
        
        # Titre
        ctk.CTkLabel(
            card,
            text="⚡ Actions",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(anchor="w", padx=20, pady=(20, 15))
        
        # Bouton principal - Pipeline complet
        self.btn_pipeline = GradientButton(
            card,
            text="🚀 Générer les Shorts",
            command=self.run_pipeline,
            style="primary"
        )
        self.btn_pipeline.pack(fill="x", padx=20, pady=(0, 10))
        
        # Bouton Transcription complète
        self.btn_transcribe = GradientButton(
            card,
            text="📝 Transcrire la vidéo",
            command=self.run_transcription,
            style="secondary"
        )
        self.btn_transcribe.pack(fill="x", padx=20, pady=(0, 10))
        
        # Boutons secondaires
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.btn_analyze = ctk.CTkButton(
            btn_frame,
            text="🔍 Analyser",
            command=self.run_analysis,
            fg_color=Colors.BG_CARD_HOVER,
            hover_color=Colors.PRIMARY,
            corner_radius=10,
            height=40
        )
        self.btn_analyze.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        self.btn_shorts_only = ctk.CTkButton(
            btn_frame,
            text="✂️ Shorts",
            command=self.run_shorts_only,
            fg_color=Colors.BG_CARD_HOVER,
            hover_color=Colors.SECONDARY,
            corner_radius=10,
            height=40
        )
        self.btn_shorts_only.pack(side="left", expand=True, fill="x", padx=(5, 0))
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(
            card,
            mode="indeterminate",
            progress_color=Colors.PRIMARY,
            fg_color=Colors.BG_DARK
        )
        self.progress.pack(fill="x", padx=20, pady=(0, 20))
        self.progress.set(0)
    
    def create_stats_section(self):
        """Section des statistiques."""
        card = ModernCard(self.left_panel)
        card.pack(fill="x")
        
        # Titre
        ctk.CTkLabel(
            card,
            text="📊 Statistiques",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(anchor="w", padx=20, pady=(20, 15))
        
        # Stats grid
        stats_frame = ctk.CTkFrame(card, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Videos count
        stat1 = self.create_stat_item(stats_frame, "📹", "Vidéos", str(len(self.get_video_list())))
        stat1.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        # Shorts count
        stat2 = self.create_stat_item(stats_frame, "🎬", "Shorts", str(self.count_shorts()))
        stat2.pack(side="left", expand=True, fill="x", padx=(5, 0))
        
        self.stat_videos = stat1
        self.stat_shorts = stat2
    
    def create_stat_item(self, parent, icon, label, value):
        """Crée un élément de statistique."""
        frame = ctk.CTkFrame(parent, fg_color=Colors.BG_DARK, corner_radius=12)
        
        ctk.CTkLabel(
            frame,
            text=icon,
            font=ctk.CTkFont(size=24)
        ).pack(pady=(15, 5))
        
        self.stat_value_label = ctk.CTkLabel(
            frame,
            text=value,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=Colors.PRIMARY
        )
        self.stat_value_label.pack()
        
        ctk.CTkLabel(
            frame,
            text=label,
            font=ctk.CTkFont(size=12),
            text_color=Colors.TEXT_MUTED
        ).pack(pady=(0, 15))
        
        return frame
    
    def create_log_section(self):
        """Section des logs."""
        card = ModernCard(self.right_panel)
        card.pack(fill="both", expand=True, pady=(0, 15))
        
        # Header avec titre et bouton clear
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            header,
            text="📋 Journal d'activité",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(side="left")
        
        ctk.CTkButton(
            header,
            text="Effacer",
            width=80,
            height=30,
            corner_radius=8,
            fg_color=Colors.BG_CARD_HOVER,
            hover_color=Colors.ERROR,
            command=self.clear_logs
        ).pack(side="right")
        
        # Zone de texte des logs
        self.log_text = ctk.CTkTextbox(
            card,
            fg_color=Colors.BG_DARK,
            corner_radius=12,
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=Colors.TEXT_SECONDARY
        )
        self.log_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Message initial
        self.log("🎬 Application Frère Théodore démarrée")
        self.log("📁 Sélectionnez une vidéo pour commencer")
    
    def create_shorts_section(self):
        """Section d'affichage des shorts générés."""
        card = ModernCard(self.right_panel, height=200)
        card.pack(fill="x")
        card.pack_propagate(False)
        
        # Header
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            header,
            text="🎬 Shorts générés",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(side="left")
        
        # Boutons dossiers
        btn_folders = ctk.CTkFrame(header, fg_color="transparent")
        btn_folders.pack(side="right")
        
        ctk.CTkButton(
            btn_folders,
            text="📄 Transcriptions",
            width=110,
            height=30,
            corner_radius=8,
            fg_color=Colors.ACCENT,
            hover_color="#D97706",
            command=self.open_transcriptions_folder
        ).pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(
            btn_folders,
            text="📂 Shorts",
            width=90,
            height=30,
            corner_radius=8,
            fg_color=Colors.SECONDARY,
            hover_color=Colors.SECONDARY_HOVER,
            command=self.open_shorts_folder
        ).pack(side="left")
        
        # Liste scrollable des shorts
        self.shorts_scroll = ctk.CTkScrollableFrame(
            card,
            fg_color=Colors.BG_DARK,
            corner_radius=12
        )
        self.shorts_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.refresh_shorts_list()
    
    # ============================================================
    # MÉTHODES UTILITAIRES
    # ============================================================
    
    def get_video_list(self):
        """Récupère la liste des vidéos disponibles."""
        if not os.path.exists(self.videos_folder):
            return ["Aucune vidéo"]
        
        videos = [f for f in os.listdir(self.videos_folder) 
                  if f.endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm'))]
        return videos if videos else ["Aucune vidéo"]
    
    def count_shorts(self):
        """Compte le nombre de shorts générés."""
        if not os.path.exists(self.shorts_folder):
            return 0
        return len([f for f in os.listdir(self.shorts_folder) if f.endswith('.mp4')])
    
    def refresh_video_list(self):
        """Rafraîchit la liste des vidéos."""
        videos = self.get_video_list()
        self.video_dropdown.configure(values=videos)
        if videos:
            self.video_dropdown.set(videos[0])
        self.log("🔄 Liste des vidéos actualisée")
    
    def refresh_shorts_list(self):
        """Rafraîchit la liste des shorts affichés."""
        # Nettoyer la liste
        for widget in self.shorts_scroll.winfo_children():
            widget.destroy()
        
        if not os.path.exists(self.shorts_folder):
            return
        
        shorts = sorted([f for f in os.listdir(self.shorts_folder) if f.endswith('.mp4')])
        
        if not shorts:
            ctk.CTkLabel(
                self.shorts_scroll,
                text="Aucun short généré",
                text_color=Colors.TEXT_MUTED
            ).pack(pady=20)
            return
        
        for short in shorts[-10:]:  # Afficher les 10 derniers
            short_path = os.path.join(self.shorts_folder, short)
            size_mb = os.path.getsize(short_path) / (1024 * 1024)
            
            item = ctk.CTkFrame(self.shorts_scroll, fg_color=Colors.BG_CARD, corner_radius=8)
            item.pack(fill="x", pady=2)
            
            ctk.CTkLabel(
                item,
                text=f"🎬 {short}",
                font=ctk.CTkFont(size=12),
                text_color=Colors.TEXT_PRIMARY
            ).pack(side="left", padx=10, pady=8)
            
            ctk.CTkLabel(
                item,
                text=f"{size_mb:.1f} MB",
                font=ctk.CTkFont(size=11),
                text_color=Colors.TEXT_MUTED
            ).pack(side="right", padx=10, pady=8)
    
    def browse_video(self):
        """Ouvre un dialogue pour sélectionner une vidéo."""
        filepath = filedialog.askopenfilename(
            title="Sélectionner une vidéo",
            filetypes=[
                ("Vidéos", "*.mp4 *.mkv *.avi *.mov *.webm"),
                ("Tous les fichiers", "*.*")
            ],
            initialdir=self.videos_folder
        )
        if filepath:
            self.video_path.set(os.path.basename(filepath))
            # Copier dans le dossier videos si nécessaire
            if os.path.dirname(filepath) != self.videos_folder:
                import shutil
                dest = os.path.join(self.videos_folder, os.path.basename(filepath))
                if not os.path.exists(dest):
                    shutil.copy2(filepath, dest)
                    self.log(f"📁 Vidéo copiée: {os.path.basename(filepath)}")
            self.refresh_video_list()
    
    def open_shorts_folder(self):
        """Ouvre le dossier des shorts dans l'explorateur."""
        os.startfile(self.shorts_folder)
    
    def open_transcriptions_folder(self):
        """Ouvre le dossier des transcriptions dans l'explorateur."""
        transcriptions_folder = os.path.join(BASE_DIR, "transcriptions")
        os.makedirs(transcriptions_folder, exist_ok=True)
        os.startfile(transcriptions_folder)
    
    def toggle_theme(self):
        """Bascule entre thème clair et sombre."""
        current = ctk.get_appearance_mode()
        new_mode = "light" if current == "Dark" else "dark"
        ctk.set_appearance_mode(new_mode)
        self.theme_btn.configure(text="☀️" if new_mode == "dark" else "🌙")
    
    def log(self, message, level="info"):
        """Ajoute un message au journal."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {
            "info": "",
            "success": "✅ ",
            "warning": "⚠️ ",
            "error": "❌ "
        }
        
        prefix = colors.get(level, "")
        full_message = f"[{timestamp}] {prefix}{message}\n"
        
        self.log_text.insert("end", full_message)
        self.log_text.see("end")
    
    def clear_logs(self):
        """Efface les logs."""
        self.log_text.delete("1.0", "end")
        self.log("📋 Journal effacé")
    
    def check_modules(self):
        """Vérifie que les modules sont chargés."""
        if not MODULES_OK:
            self.log(f"Erreur de chargement des modules: {IMPORT_ERROR}", "error")
            self.status_badge.set_status("Erreur modules", "error")
        else:
            self.log("Modules IA chargés avec succès", "success")
    
    def update_stats(self):
        """Met à jour les statistiques affichées."""
        # Recréer les stats
        self.refresh_shorts_list()
    
    def process_queue(self):
        """Traite les messages de la queue (thread-safe)."""
        try:
            while True:
                msg, level = self.message_queue.get_nowait()
                self.log(msg, level)
        except queue.Empty:
            pass
        
        # Replanifier
        self.after(100, self.process_queue)
    
    def set_processing(self, state):
        """Active/désactive l'état de traitement."""
        self.processing = state
        
        if state:
            self.progress.start()
            self.btn_pipeline.configure(state="disabled")
            self.btn_transcribe.configure(state="disabled")
            self.btn_analyze.configure(state="disabled")
            self.btn_shorts_only.configure(state="disabled")
            self.status_badge.set_status("Traitement...", "warning")
        else:
            self.progress.stop()
            self.progress.set(0)
            self.btn_pipeline.configure(state="normal")
            self.btn_transcribe.configure(state="normal")
            self.btn_analyze.configure(state="normal")
            self.btn_shorts_only.configure(state="normal")
            self.status_badge.set_status("Prêt", "success")
            self.update_stats()
    
    # ============================================================
    # ACTIONS PRINCIPALES
    # ============================================================
    
    def run_pipeline(self):
        """Lance le pipeline complet en arrière-plan."""
        video = self.video_path.get()
        if not video or video == "Aucune vidéo":
            messagebox.showwarning("Attention", "Veuillez sélectionner une vidéo")
            return
        
        self.set_processing(True)
        self.log(f"🚀 Lancement du pipeline pour: {video}")
        
        # Lancer dans un thread séparé
        thread = threading.Thread(target=self._pipeline_thread, args=(video,))
        thread.daemon = True
        thread.start()
    
    def _pipeline_thread(self, video_name):
        """Thread du pipeline complet."""
        try:
            video_path = os.path.join(self.videos_folder, video_name)
            
            if not os.path.exists(video_path):
                self.message_queue.put((f"Vidéo non trouvée: {video_name}", "error"))
                return
            
            # Importer et exécuter le pipeline
            from chatbot import pipeline_complet
            
            self.message_queue.put(("📌 Étape 1: Détection de la voix...", "info"))
            
            result = pipeline_complet(video_name)
            
            # Parser le résultat
            for line in result.split('\n'):
                if line.strip():
                    if '✅' in line:
                        self.message_queue.put((line.strip(), "success"))
                    elif '❌' in line:
                        self.message_queue.put((line.strip(), "error"))
                    elif '⚠️' in line:
                        self.message_queue.put((line.strip(), "warning"))
                    else:
                        self.message_queue.put((line.strip(), "info"))
            
            self.message_queue.put(("🎉 Pipeline terminé avec succès!", "success"))
            
        except Exception as e:
            self.message_queue.put((f"Erreur: {str(e)}", "error"))
        finally:
            # Remettre l'état normal (dans le thread principal)
            self.after(100, lambda: self.set_processing(False))
    
    def run_analysis(self):
        """Lance uniquement l'analyse."""
        video = self.video_path.get()
        if not video or video == "Aucune vidéo":
            messagebox.showwarning("Attention", "Veuillez sélectionner une vidéo")
            return
        
        self.set_processing(True)
        self.log(f"🔍 Analyse de: {video}")
        
        thread = threading.Thread(target=self._analysis_thread, args=(video,))
        thread.daemon = True
        thread.start()
    
    def _analysis_thread(self, video_name):
        """Thread d'analyse."""
        try:
            from chatbot import analyser_video
            result = analyser_video(video_name)
            
            for line in result.split('\n')[-20:]:  # Dernières lignes
                if line.strip():
                    self.message_queue.put((line.strip(), "info"))
            
        except Exception as e:
            self.message_queue.put((f"Erreur: {str(e)}", "error"))
        finally:
            self.after(100, lambda: self.set_processing(False))
    
    def run_shorts_only(self):
        """Génère les shorts à partir des timestamps existants."""
        video = self.video_path.get()
        if not video or video == "Aucune vidéo":
            messagebox.showwarning("Attention", "Veuillez sélectionner une vidéo")
            return
        
        self.set_processing(True)
        self.log(f"✂️ Génération des shorts pour: {video}")
        
        thread = threading.Thread(target=self._shorts_thread, args=(video,))
        thread.daemon = True
        thread.start()
    
    def _shorts_thread(self, video_name):
        """Thread de génération des shorts."""
        try:
            from chatbot import generer_shorts
            result = generer_shorts(video_name)
            
            for line in result.split('\n'):
                if line.strip():
                    self.message_queue.put((line.strip(), "info"))
            
        except Exception as e:
            self.message_queue.put((f"Erreur: {str(e)}", "error"))
        finally:
            self.after(100, lambda: self.set_processing(False))
    
    def run_transcription(self):
        """Lance la transcription complète de la vidéo."""
        video = self.video_path.get()
        if not video or video == "Aucune vidéo":
            messagebox.showwarning("Attention", "Veuillez sélectionner une vidéo")
            return
        
        self.set_processing(True)
        self.log(f"📝 Transcription complète de: {video}")
        
        # Récupérer le modèle choisi
        model_type = self.model_choice.get()
        
        thread = threading.Thread(target=self._transcription_thread, args=(video, model_type))
        thread.daemon = True
        thread.start()
    
    def _transcription_thread(self, video_name, model_type="precise"):
        """Thread de transcription complète."""
        try:
            import subprocess
            from datetime import timedelta
            
            video_path = os.path.join(self.videos_folder, video_name)
            
            if not os.path.exists(video_path):
                self.message_queue.put((f"Vidéo non trouvée: {video_name}", "error"))
                return
            
            # Afficher le modèle utilisé
            model_name = "small (Rapide)" if model_type == "fast" else "large-v3 (Précis)"
            self.message_queue.put((f"🎤 Modèle sélectionné : {model_name}", "info"))
            
            # Obtenir la durée de la vidéo
            self.message_queue.put(("📊 Analyse de la vidéo...", "info"))
            
            ffprobe_path = os.path.join(os.path.dirname(sys.executable), "Library", "bin", "ffprobe.exe")
            result = subprocess.run(
                [ffprobe_path, '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', video_path],
                capture_output=True, text=True
            )
            duration = float(result.stdout.strip()) if result.stdout.strip() else 0
            
            self.message_queue.put((f"⏱️ Durée: {timedelta(seconds=int(duration))}", "info"))
            
            # Importer pour détecter le device
            from transcription_engine import DEVICE
            
            # Estimation du temps selon le device et le modèle
            if DEVICE == "cuda":
                self.message_queue.put(("🎮 GPU NVIDIA détecté - Mode ultra-rapide!", "success"))
                if model_type == "fast":
                    estimated_time = duration * 0.02  # ~0.02x temps réel sur GPU
                    self.message_queue.put((f"⚡ Temps estimé: ~{timedelta(seconds=int(max(estimated_time, 10)))} (GPU + rapide)", "info"))
                else:
                    estimated_time = duration * 0.1  # ~0.1x temps réel sur GPU
                    self.message_queue.put((f"🎯 Temps estimé: ~{timedelta(seconds=int(max(estimated_time, 30)))} (GPU + précis)", "info"))
            else:
                self.message_queue.put(("💻 Mode CPU (pas de GPU détecté)", "info"))
                if model_type == "fast":
                    estimated_time = duration * 0.3  # ~0.3x temps réel
                    self.message_queue.put((f"⚡ Temps estimé: ~{timedelta(seconds=int(estimated_time))} (CPU + rapide)", "info"))
                else:
                    estimated_time = duration * 1.5  # ~1.5x temps réel
                    self.message_queue.put((f"🎯 Temps estimé: ~{timedelta(seconds=int(estimated_time))} (CPU + précis)", "info"))
            
            self.message_queue.put(("🎤 Chargement du modèle de transcription...", "info"))
            
            # Importer le moteur de transcription avec le bon modèle
            from transcription_engine import get_engine
            engine = get_engine(model_type)
            
            # Transcrire par segments de 30 secondes
            segment_duration = 30
            all_segments = []
            
            for start in range(0, int(duration), segment_duration):
                end = min(start + segment_duration, duration)
                progress = int((start / duration) * 100)
                
                self.message_queue.put((f"📝 Transcription... {progress}% ({timedelta(seconds=start)} / {timedelta(seconds=int(duration))})", "info"))
                
                segments = engine.transcribe_video_segment(video_path, start, end - start)
                
                for seg_start, seg_end, text in segments:
                    # Ajuster les timestamps absolus
                    abs_start = start + seg_start
                    abs_end = start + seg_end
                    all_segments.append((abs_start, abs_end, text))
            
            # Sauvegarder la transcription
            output_dir = os.path.join(BASE_DIR, "transcriptions")
            os.makedirs(output_dir, exist_ok=True)
            
            video_base = os.path.splitext(video_name)[0]
            output_txt = os.path.join(output_dir, f"{video_base}_transcription.txt")
            output_srt = os.path.join(output_dir, f"{video_base}_transcription.srt")
            
            # Fichier texte simple
            with open(output_txt, 'w', encoding='utf-8') as f:
                f.write(f"TRANSCRIPTION - {video_name}\n")
                f.write(f"Durée: {timedelta(seconds=int(duration))}\n")
                f.write("=" * 60 + "\n\n")
                
                for start, end, text in all_segments:
                    time_str = str(timedelta(seconds=int(start)))
                    f.write(f"[{time_str}] {text}\n")
                
                f.write("\n" + "=" * 60 + "\n")
                f.write(f"Total: {len(all_segments)} segments transcrits\n")
            
            # Fichier SRT pour sous-titres
            with open(output_srt, 'w', encoding='utf-8') as f:
                for i, (start, end, text) in enumerate(all_segments, 1):
                    start_srt = f"{int(start//3600):02d}:{int((start%3600)//60):02d}:{int(start%60):02d},{int((start%1)*1000):03d}"
                    end_srt = f"{int(end//3600):02d}:{int((end%3600)//60):02d}:{int(end%60):02d},{int((end%1)*1000):03d}"
                    f.write(f"{i}\n{start_srt} --> {end_srt}\n{text}\n\n")
            
            self.message_queue.put(("", "info"))
            self.message_queue.put(("=" * 50, "info"))
            self.message_queue.put(("📝 TRANSCRIPTION TERMINÉE", "success"))
            self.message_queue.put(("=" * 50, "info"))
            self.message_queue.put((f"✅ {len(all_segments)} segments transcrits", "success"))
            self.message_queue.put((f"📄 Fichier TXT: {output_txt}", "info"))
            self.message_queue.put((f"📄 Fichier SRT: {output_srt}", "info"))
            
            # Afficher les premiers segments dans le log
            self.message_queue.put(("", "info"))
            self.message_queue.put(("📋 Aperçu de la transcription:", "info"))
            for start, end, text in all_segments[:5]:
                time_str = str(timedelta(seconds=int(start)))
                self.message_queue.put((f"   [{time_str}] {text[:60]}...", "info"))
            
            if len(all_segments) > 5:
                self.message_queue.put((f"   ... et {len(all_segments) - 5} autres segments", "info"))
            
            # Ouvrir le dossier
            self.message_queue.put(("", "info"))
            self.message_queue.put(("💡 Cliquez sur 'Ouvrir transcriptions' pour voir les fichiers", "info"))
            
        except Exception as e:
            self.message_queue.put((f"Erreur: {str(e)}", "error"))
            import traceback
            self.message_queue.put((traceback.format_exc(), "error"))
        finally:
            self.after(100, lambda: self.set_processing(False))


# ============================================================
# POINT D'ENTRÉE
# ============================================================
def main():
    app = ThéodoreApp()
    app.mainloop()


if __name__ == "__main__":
    main()
