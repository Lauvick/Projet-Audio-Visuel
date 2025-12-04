# 🎵 Projet Audio HERMANN - Réduction de Bruit IA

## 📋 Objectif Principal
Solution basée sur l'IA pour la réduction de bruit sur fichiers audio extraits de productions vidéo. Cette solution est conçue pour gérer des bruits de fond complexes et large bande.

## ✅ Stories Validées
- **Story 1.3**: Tester différents outils de réduction de bruit IA pour choisir le meilleur
- **Story 2.2**: Utiliser une IA pour nettoyer l'audio automatiquement

## 📁 Structure du Projet
```
Projet_audio/
│
├── denoise_agent.py              # Script principal de dénoisation IA
├── requirements.txt              # Dépendances Python
├── README.md                     # Documentation (ce fichier)
│
├── audio_bruit_test1.wav         # [À FOURNIR] Fichier audio source bruité
├── audio_nettoye_ia.wav          # [GÉNÉRÉ] Fichier audio nettoyé
└── comparaison_fft_denoise.png   # [GÉNÉRÉ] Graphique FFT comparatif
```

## 🔧 Installation

### Prérequis
- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### Étape 1: Installation des dépendances
Ouvrez un terminal dans le dossier du projet et exécutez:

```powershell
pip install -r requirements.txt
```

### Bibliothèques Installées
- **numpy**: Calculs numériques et manipulation de tableaux
- **scipy**: Traitement du signal (FFT, STFT, lecture/écriture WAV)
- **matplotlib**: Visualisation des spectres FFT
- **noisereduce**: Bibliothèque IA de dénoisation (méthode principale)
- **librosa**: Analyse audio avancée (optionnel)
- **soundfile**: Support de formats audio supplémentaires
- **tqdm**: Barres de progression

## 🎯 Utilisation

### Préparation
1. Placez votre fichier audio bruité dans le dossier du projet
2. Renommez-le en `audio_bruit_test1.wav` (ou modifiez le nom dans le script)

### Caractéristiques Requises du Fichier Audio
- **Format**: WAV (non compressé)
- **Encodage**: 16-bit PCM (recommandé)
- **Fréquence**: 48000 Hz (idéal, mais d'autres fréquences sont supportées)

### Exécution
```powershell
python denoise_agent.py
```

## 📊 Résultats Générés

### 1. Fichier Audio Nettoyé
- **Nom**: `audio_nettoye_ia.wav`
- **Format**: WAV 16-bit PCM
- **Contenu**: Signal audio avec bruit large bande réduit

### 2. Graphique Comparatif FFT
- **Nom**: `comparaison_fft_denoise.png`
- **Contenu**: 
  - Graphique supérieur: Spectre FFT comparé (Original vs Nettoyé)
  - Graphique inférieur: Profil du bruit éliminé
- **Métrique**: Réduction du plancher de bruit en dB

## 🧠 Méthodes de Dénoisation IA

### Méthode Principale: `noisereduce`
- Algorithme IA basé sur le filtrage spectral avancé
- Détection automatique du profil de bruit
- Configuration optimisée pour bruit large bande:
  - Bruit non-stationnaire
  - Réduction agressive (90%)
  - Lissage fréquentiel et temporel

### Méthode Alternative: Spectral Gating
- Utilisée si `noisereduce` n'est pas disponible
- Basée sur STFT (Short-Time Fourier Transform)
- Estimation du profil de bruit sur les premières frames
- Application d'un masque spectral adaptatif

## 📈 Critères de Succès
✅ Le script s'exécute sans erreur  
✅ Un graphique comparatif des spectres FFT est généré  
✅ Le graphique montre une réduction visible du bruit de fond  
✅ Le fichier `audio_nettoye_ia.wav` est créé  
✅ Réduction mesurable du plancher de bruit (affiché en dB)

## 🔍 Analyse Technique

### Pipeline de Traitement
```
1. CHARGEMENT
   ├── Lecture du fichier WAV
   ├── Vérification Fs = 48000 Hz
   ├── Conversion mono si stéréo
   └── Normalisation [-1.0, 1.0]

2. DÉNOISATION IA
   ├── Analyse du profil de bruit
   ├── Application algorithme IA (noisereduce)
   └── Normalisation du signal nettoyé

3. VALIDATION FFT
   ├── Calcul FFT original
   ├── Calcul FFT nettoyé
   ├── Mesure du plancher de bruit
   └── Génération graphique comparatif

4. EXPORTATION
   ├── Conversion int16
   └── Sauvegarde WAV
```

### Paramètres Clés
- **Taille FFT**: 2048 échantillons
- **Réduction du bruit**: 90% (prop_decrease=0.9)
- **Lissage fréquentiel**: 500 Hz
- **Lissage temporel**: 50 ms

## 🛠️ Personnalisation

### Modifier le Fichier d'Entrée
Éditez la ligne dans `denoise_agent.py`:
```python
denoiser = AudioDenoiser(input_file="votre_fichier.wav")
```

### Ajuster l'Agressivité de la Réduction
Dans la fonction `denoise_audio()`, modifiez:
```python
prop_decrease=0.9  # 0.0 (aucune) à 1.0 (max)
```

### Forcer une Méthode Spécifique
```python
denoiser.denoise_audio(method="noisereduce")  # ou "spectral"
```

## 📞 Support & Dépannage

### Erreur: "Fichier introuvable"
- Vérifiez que `audio_bruit_test1.wav` est dans le même dossier que le script
- Vérifiez l'orthographe du nom de fichier

### Erreur: "Import could not be resolved"
- Réinstallez les dépendances: `pip install -r requirements.txt`
- Vérifiez que vous utilisez le bon environnement Python

### Performances Lentes
- Normal pour de longs fichiers audio
- Une barre de progression s'affiche pendant le traitement
- Durée approximative: ~10-30 secondes par minute d'audio

## 📚 Références Techniques
- **FFT**: Analyse spectrale du signal audio
- **Spectral Gating**: Réduction de bruit par masquage fréquentiel
- **noisereduce**: https://github.com/timsainb/noisereduce
- **Fréquence 48kHz**: Standard professionnel vidéo/audio

---

**Auteur**: Agent IA Copilot  
**Date**: Décembre 2025  
**Projet**: HERMANN - Production Audio/Vidéo
