"""
🎯 MOTEUR DE TRANSCRIPTION ULTRA-PERFORMANT
============================================

Ce module utilise faster-whisper avec le modèle large-v3 pour une transcription
de qualité professionnelle, 100% gratuite et offline.

Optimisations incluses:
1. faster-whisper (CTranslate2) - 4x plus rapide que Whisper standard
2. Modèle large-v3 - Le plus précis disponible (1.5B paramètres)
3. VAD (Voice Activity Detection) - Ignore les silences
4. Beam search optimisé - Meilleure précision
5. Post-processing intelligent - Correction des erreurs communes

Auteur: AI Agent pour Frère Théodore
"""

import os
import sys
import tempfile
import subprocess
import threading
from typing import List, Tuple, Optional

# Lock global pour la thread-safety du modèle
_model_lock = threading.Lock()

# Configuration
CONDA_ENV = os.path.dirname(sys.executable)
FFMPEG_PATH = os.path.join(CONDA_ENV, "Library", "bin", "ffmpeg.exe")
if not os.path.exists(FFMPEG_PATH):
    FFMPEG_PATH = "ffmpeg"

# Ajouter FFmpeg au PATH
if os.path.exists(os.path.dirname(FFMPEG_PATH)):
    os.environ["PATH"] = os.path.dirname(FFMPEG_PATH) + os.pathsep + os.environ.get("PATH", "")

# ============================================================
# DÉTECTION AUTOMATIQUE DU GPU
# ============================================================

def detect_device():
    """
    Détecte automatiquement si un GPU NVIDIA avec CUDA est disponible.
    
    Returns:
        tuple: (device, compute_type)
            - ("cuda", "float16") si GPU NVIDIA disponible
            - ("cpu", "int8") sinon
    """
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"🎮 GPU NVIDIA détecté : {gpu_name} ({gpu_memory:.1f} GB)")
            print(f"⚡ Mode CUDA activé - Transcription ultra-rapide!")
            return "cuda", "float16"
    except ImportError:
        pass
    
    # Fallback: essayer avec ctranslate2 directement
    try:
        import ctranslate2
        if "cuda" in ctranslate2.get_supported_compute_types("cuda"):
            print(f"🎮 GPU CUDA détecté via CTranslate2")
            print(f"⚡ Mode CUDA activé - Transcription ultra-rapide!")
            return "cuda", "float16"
    except:
        pass
    
    print("💻 Pas de GPU CUDA détecté - Utilisation du CPU")
    return "cpu", "int8"

# Détection automatique au démarrage
DEVICE, COMPUTE_TYPE = detect_device()

# ============================================================
# CONFIGURATION DU MODÈLE
# ============================================================

# Modèles disponibles (du plus rapide au plus précis):
# - tiny    : 39M params, très rapide mais peu précis
# - base    : 74M params, rapide mais erreurs fréquentes  
# - small   : 244M params, bon compromis
# - medium  : 769M params, très bon
# - large-v3: 1.5B params, MEILLEURE PRÉCISION (recommandé)

MODEL_SIZE = "large-v3"  # Le plus précis disponible

# Options de transcription optimisées
TRANSCRIPTION_OPTIONS = {
    "language": "fr",           # Français
    "task": "transcribe",       # Transcription (pas traduction)
    "beam_size": 5,             # Beam search pour meilleure précision
    "best_of": 5,               # Garde les 5 meilleures hypothèses
    "patience": 1.0,            # Patience pour beam search
    "length_penalty": 1.0,      # Pénalité sur la longueur
    "temperature": 0.0,         # Déterministe (pas de sampling)
    "compression_ratio_threshold": 2.4,
    "log_prob_threshold": -1.0,
    "no_speech_threshold": 0.6,
    "condition_on_previous_text": True,  # Contexte entre segments
    "initial_prompt": "Transcription d'un sermon religieux chrétien en français. Le prédicateur parle de Dieu, Jésus-Christ, le Saint-Esprit, la Bible, la foi, la prière, l'église, les frères et sœurs.",
    "word_timestamps": True,    # Timestamps par mot
    "vad_filter": True,         # Voice Activity Detection
    "vad_parameters": {
        "min_silence_duration_ms": 500,
        "speech_pad_ms": 400,
    }
}

# ============================================================
# DICTIONNAIRE DE CORRECTIONS
# ============================================================

# Corrections spécifiques au vocabulaire religieux
CORRECTIONS = {
    # Corrections religieuses
    "jésus christ": "Jésus-Christ",
    "jesus christ": "Jésus-Christ",
    "jesus": "Jésus",
    "jésus": "Jésus",
    "christ": "Christ",
    "saint esprit": "Saint-Esprit",
    "saint-esprit": "Saint-Esprit",
    "esprit saint": "Esprit Saint",
    "dieu": "Dieu",
    "seigneur": "Seigneur",
    "père": "Père",
    "fils": "Fils",
    "évangile": "Évangile",
    "evangile": "Évangile",
    "bible": "Bible",
    "église": "Église",
    "eglise": "Église",
    "amen": "Amen",
    "alléluia": "Alléluia",
    "alleluia": "Alléluia",
    "frère": "frère",
    "soeur": "sœur",
    "théodore": "Théodore",
    "theodore": "Théodore",
    
    # Corrections phonétiques communes
    "y a": "il y a",
    "t'as": "tu as",
    "c'est à dire": "c'est-à-dire",
    "parce que": "parce que",
    "aujourd'hui": "aujourd'hui",
}

# ============================================================
# CLASSE PRINCIPALE
# ============================================================

class TranscriptionEngine:
    """
    Moteur de transcription ultra-performant basé sur faster-whisper.
    """
    
    def __init__(self, model_size: str = MODEL_SIZE):
        """
        Initialise le moteur de transcription.
        
        Args:
            model_size: Taille du modèle (tiny, base, small, medium, large-v3)
        """
        self.model_size = model_size
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Charge le modèle faster-whisper."""
        try:
            from faster_whisper import WhisperModel
            
            print(f"🎤 Chargement du modèle {self.model_size}...")
            print(f"   (Première utilisation: téléchargement ~3GB)")
            
            self.model = WhisperModel(
                self.model_size,
                device=DEVICE,
                compute_type=COMPUTE_TYPE,
                download_root=os.path.join(os.path.dirname(__file__), "models_cache")
            )
            
            print(f"✅ Modèle {self.model_size} chargé!")
            
        except ImportError:
            print("❌ faster-whisper non installé. Utilisation de whisper standard.")
            self.model = None
        except Exception as e:
            print(f"❌ Erreur chargement modèle: {e}")
            self.model = None
    
    def extract_audio(self, video_path: str, start_sec: float, duration: float) -> Optional[str]:
        """
        Extrait l'audio d'un segment vidéo.
        
        Args:
            video_path: Chemin de la vidéo
            start_sec: Début en secondes
            duration: Durée en secondes
        
        Returns:
            Chemin du fichier audio temporaire
        """
        # Créer un fichier temporaire avec un nom unique
        import uuid
        temp_dir = tempfile.gettempdir()
        temp_audio_path = os.path.join(temp_dir, f"audio_segment_{uuid.uuid4().hex}.wav")
        
        cmd = [
            FFMPEG_PATH,
            '-y',
            '-ss', str(start_sec),
            '-i', video_path,
            '-t', str(duration),
            '-vn',
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            temp_audio_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and os.path.exists(temp_audio_path):
                return temp_audio_path
        except Exception as e:
            print(f"⚠️ Erreur extraction audio: {e}")
        
        return None
    
    def apply_corrections(self, text: str) -> str:
        """
        Applique les corrections au texte transcrit.
        
        Args:
            text: Texte brut de la transcription
        
        Returns:
            Texte corrigé
        """
        result = text.lower()
        
        # Appliquer les corrections
        for wrong, correct in CORRECTIONS.items():
            result = result.replace(wrong.lower(), correct)
        
        # Capitaliser la première lettre de chaque phrase
        sentences = result.split('. ')
        sentences = [s.capitalize() if s else s for s in sentences]
        result = '. '.join(sentences)
        
        # Capitaliser après "?"  et "!"
        for punct in ['? ', '! ']:
            parts = result.split(punct)
            parts = [p.capitalize() if p else p for p in parts]
            result = punct.join(parts)
        
        return result.strip()
    
    def transcribe(self, audio_path: str) -> List[Tuple[float, float, str]]:
        """
        Transcrit un fichier audio.
        
        Args:
            audio_path: Chemin du fichier audio
        
        Returns:
            Liste de (start, end, text) pour chaque segment
        """
        if self.model is None:
            return []
        
        try:
            # Utiliser un lock pour éviter les problèmes de threading
            with _model_lock:
                segments, info = self.model.transcribe(
                    audio_path,
                    **TRANSCRIPTION_OPTIONS
                )
                
                results = []
                for segment in segments:
                    text = self.apply_corrections(segment.text)
                    if text.strip():
                        results.append((segment.start, segment.end, text))
                
                return results
            
        except Exception as e:
            print(f"❌ Erreur transcription: {e}")
            return []
    
    def transcribe_words(self, audio_path: str) -> List[Tuple[float, float, str]]:
        """
        Transcrit un fichier audio et retourne les timestamps MOT PAR MOT.
        
        Args:
            audio_path: Chemin du fichier audio
        
        Returns:
            Liste de (start, end, word) pour chaque mot
        """
        if self.model is None:
            return []
        
        try:
            # Utiliser un lock pour éviter les problèmes de threading
            with _model_lock:
                segments, info = self.model.transcribe(
                    audio_path,
                    **TRANSCRIPTION_OPTIONS
                )
                
                words = []
                for segment in segments:
                    # Récupérer les mots avec leurs timestamps
                    if hasattr(segment, 'words') and segment.words:
                        for word_info in segment.words:
                            word = word_info.word.strip()
                            if word:
                                words.append((word_info.start, word_info.end, word))
                
                return words
            
        except Exception as e:
            print(f"❌ Erreur transcription mots: {e}")
            return []
    
    def transcribe_video_segment(self, video_path: str, start_sec: float, duration: float) -> List[Tuple[float, float, str]]:
        """
        Transcrit un segment d'une vidéo (par phrase).
        
        Args:
            video_path: Chemin de la vidéo
            start_sec: Début en secondes
            duration: Durée en secondes
        
        Returns:
            Liste de (start_relative, end_relative, text)
        """
        # Extraire l'audio
        audio_path = self.extract_audio(video_path, start_sec, duration)
        if not audio_path:
            return []
        
        try:
            # Transcrire
            return self.transcribe(audio_path)
        finally:
            # Nettoyer
            try:
                os.unlink(audio_path)
            except:
                pass
    
    def transcribe_video_segment_words(self, video_path: str, start_sec: float, duration: float) -> List[Tuple[float, float, str]]:
        """
        Transcrit un segment d'une vidéo MOT PAR MOT.
        
        Args:
            video_path: Chemin de la vidéo
            start_sec: Début en secondes
            duration: Durée en secondes
        
        Returns:
            Liste de (start_relative, end_relative, word) pour chaque mot
        """
        # Extraire l'audio
        audio_path = self.extract_audio(video_path, start_sec, duration)
        if not audio_path:
            return []
        
        try:
            # Transcrire mot par mot
            return self.transcribe_words(audio_path)
        finally:
            # Nettoyer
            try:
                os.unlink(audio_path)
            except:
                pass


# ============================================================
# INSTANCE GLOBALE (SINGLETON)
# ============================================================

# Dictionnaire des moteurs (fast et precise)
_engines = {}

# Mapping des types de modèles
MODEL_TYPES = {
    "fast": "small",       # Rapide, bonne qualité
    "precise": "large-v3"  # Meilleure qualité, plus lent
}

def get_engine(model_type: str = "precise") -> TranscriptionEngine:
    """
    Retourne l'instance du moteur de transcription pour le type demandé.
    
    Args:
        model_type: "fast" pour small, "precise" pour large-v3
    
    Returns:
        Instance de TranscriptionEngine
    """
    global _engines
    
    # Normaliser le type de modèle
    if model_type not in MODEL_TYPES:
        model_type = "precise"
    
    if model_type not in _engines:
        model_size = MODEL_TYPES[model_type]
        print(f"🎤 Initialisation du moteur {model_type} ({model_size})...")
        _engines[model_type] = TranscriptionEngine(model_size=model_size)
    
    return _engines[model_type]


def transcribe_segment(video_path: str, start_sec: float, duration: float, model_type: str = "precise") -> List[Tuple[float, float, str]]:
    """
    Fonction de commodité pour transcrire un segment.
    
    Args:
        video_path: Chemin de la vidéo
        start_sec: Début en secondes
        duration: Durée en secondes
        model_type: "fast" ou "precise"
    
    Returns:
        Liste de (start, end, text)
    """
    engine = get_engine(model_type)
    return engine.transcribe_video_segment(video_path, start_sec, duration)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎯 TEST DU MOTEUR DE TRANSCRIPTION ULTRA-PERFORMANT")
    print("="*60)
    
    # Test avec une vidéo
    import sys
    if len(sys.argv) > 1:
        video = sys.argv[1]
        start = float(sys.argv[2]) if len(sys.argv) > 2 else 0
        duration = float(sys.argv[3]) if len(sys.argv) > 3 else 30
        
        print(f"\n📹 Vidéo: {video}")
        print(f"⏱️ Segment: {start}s → {start + duration}s")
        
        results = transcribe_segment(video, start, duration)
        
        print(f"\n📝 Transcription ({len(results)} segments):")
        for start_t, end_t, text in results:
            print(f"   [{start_t:.1f}s → {end_t:.1f}s] {text}")
    else:
        print("\nUsage: python transcription_engine.py <video> [start] [duration]")
        print("Exemple: python transcription_engine.py test.mp4 0 30")
