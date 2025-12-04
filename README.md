# 🎬 Projet Audio-Visuel - Frère Théodore

Application Windows pour la **détection vocale automatique** et la **génération de shorts** avec sous-titres dynamiques mot par mot.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

## ✨ Fonctionnalités

- 🎤 **Détection vocale** : Identifie automatiquement une voix spécifique dans une vidéo (empreinte vocale)
- ✂️ **Génération de shorts** : Extrait les segments détectés en clips courts
- 📝 **Sous-titres dynamiques** : Affichage mot par mot synchronisé avec la parole
- 🎯 **Transcription précise** : Utilise faster-whisper (large-v3) pour une transcription de qualité
- 🎮 **Détection GPU automatique** : Accélération CUDA si disponible
- 🖥️ **Interface graphique moderne** : Application Windows avec thème sombre/clair

## 📸 Aperçu

L'application propose :
- Sélection de vidéos à analyser
- Choix du modèle de transcription (Rapide vs Précis)
- Pipeline complet : détection → extraction → sous-titres
- Logs en temps réel avec progression

## 🚀 Installation

### Prérequis

- **Python 3.10+** ([Télécharger](https://www.python.org/downloads/))
- **FFmpeg** ([Télécharger](https://ffmpeg.org/download.html)) - Doit être dans le PATH
- **~5 GB d'espace disque** (pour les modèles IA)

### Étape 1 : Cloner le projet

```bash
git clone https://github.com/Lauvick/Projet-Audio-Visuel.git
cd Projet-Audio-Visuel
```

### Étape 2 : Créer un environnement virtuel

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### Étape 3 : Installer les dépendances

```bash
pip install -r requirements.txt
pip install -r ai_agent/requirements_ai.txt
```

### Étape 4 : Premier lancement (téléchargement des modèles)

Au premier lancement, les modèles IA seront téléchargés automatiquement (~3 GB) :
- **SpeechBrain X-Vector** : Pour la détection vocale
- **faster-whisper large-v3** : Pour la transcription

## 🎯 Utilisation

### Lancer l'application graphique

```bash
python ai_agent/app_gui.py
```

Ou double-cliquez sur `Lancer_Application.bat`

### Interface

1. **Sélectionnez une vidéo** dans le menu déroulant
2. **Choisissez le modèle** :
   - ⚡ **Rapide** : ~3 min pour 10 min de vidéo (CPU)
   - 🎯 **Précis** : ~17 min pour 10 min de vidéo (CPU)
3. **Cliquez sur une action** :
   - 🚀 Générer les Shorts : Pipeline complet
   - 📝 Transcrire la vidéo : Transcription seule (TXT + SRT)
   - 🔍 Analyser : Détection vocale uniquement

### Créer une empreinte vocale personnalisée

Pour détecter une voix spécifique, placez 2-3 fichiers audio (.wav, .mp3, .m4a) de cette personne dans `ai_agent/audio_theodore/` puis :

```bash
python ai_agent/create_voice_print.py
```

## 📁 Structure du projet

```
Projet-Audio-Visuel/
├── ai_agent/
│   ├── app_gui.py              # 🖥️ Application graphique principale
│   ├── transcription_engine.py # 🎤 Moteur faster-whisper
│   ├── detect_theodore.py      # 🔍 Détection vocale
│   ├── generate_shorts.py      # ✂️ Génération de shorts
│   ├── create_voice_print.py   # 🎯 Création d'empreinte vocale
│   ├── chatbot.py              # 🤖 Interface chatbot (Ollama)
│   ├── videos_theodore/        # 📹 Vidéos à analyser
│   ├── shorts_theodore/        # 🎬 Shorts générés
│   └── transcriptions/         # 📄 Fichiers de transcription
├── requirements.txt            # 📦 Dépendances de base
├── Lancer_Application.bat      # ▶️ Lanceur Windows
└── README.md                   # 📖 Documentation
```

## ⚡ Performance

| Mode | CPU (i7/Ryzen 7) | GPU NVIDIA |
|------|------------------|------------|
| **Rapide (small)** | ~0.3x temps réel | ~0.02x temps réel |
| **Précis (large-v3)** | ~1.5x temps réel | ~0.1x temps réel |

*Exemple : Vidéo de 10 min → 3 min (Rapide/CPU) ou 1 min (Précis/GPU)*

## 🔧 Configuration GPU (optionnel)

Si vous avez un GPU NVIDIA, installez CUDA pour des transcriptions 10x plus rapides :

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

L'application détecte automatiquement le GPU au démarrage.

## 📝 Dépendances principales

- **faster-whisper** : Transcription audio ultra-rapide
- **speechbrain** : Détection et reconnaissance vocale
- **customtkinter** : Interface graphique moderne
- **FFmpeg** : Traitement vidéo/audio

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit (`git commit -m 'Ajout fonctionnalité'`)
4. Push (`git push origin feature/amelioration`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👤 Auteur

**Lauvick** - [GitHub](https://github.com/Lauvick)

---

⭐ Si ce projet vous est utile, n'hésitez pas à lui donner une étoile !
