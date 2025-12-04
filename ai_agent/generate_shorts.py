"""
Script de découpage vidéo automatique.
Extrait uniquement les segments où le Frère Théodore parle
et génère des fichiers vidéo séparés (prêts pour les Shorts).

NOUVEAU : Transcription vocale avec Whisper + sous-titres dynamiques style TikTok
"""

import os
import sys
import io
import subprocess
import tempfile
from datetime import timedelta

# Forcer l'encodage UTF-8 pour la console Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuration FFmpeg (chemin absolu pour Windows)
CONDA_ENV = os.path.dirname(sys.executable)
FFMPEG_PATH = os.path.join(CONDA_ENV, "Library", "bin", "ffmpeg.exe")
if not os.path.exists(FFMPEG_PATH):
    FFMPEG_PATH = "ffmpeg"  # Fallback vers PATH système

# Ajouter le dossier FFmpeg au PATH
if os.path.exists(os.path.dirname(FFMPEG_PATH)):
    os.environ["PATH"] = os.path.dirname(FFMPEG_PATH) + os.pathsep + os.environ.get("PATH", "")

# Import Whisper pour la transcription
try:
    # Essayer faster-whisper d'abord (plus performant)
    from transcription_engine import transcribe_segment as transcribe_segment_engine
    from transcription_engine import get_engine
    TRANSCRIPTION_ENGINE = "faster-whisper-large-v3"
    WHISPER_AVAILABLE = True
    
    def transcribe_segment(video_path, start_sec, duration):
        """Utilise le moteur de transcription ultra-performant."""
        return transcribe_segment_engine(video_path, start_sec, duration)
    
    def transcribe_segment_words(video_path, start_sec, duration):
        """Transcription MOT PAR MOT pour sous-titres temps réel."""
        engine = get_engine()
        return engine.transcribe_video_segment_words(video_path, start_sec, duration)
    
except ImportError:
    try:
        import whisper
        TRANSCRIPTION_ENGINE = "whisper-base"
        WHISPER_AVAILABLE = True
        WHISPER_MODEL = None
        
        def transcribe_segment_words(video_path, start_sec, duration):
            return None
    except ImportError:
        TRANSCRIPTION_ENGINE = None
        WHISPER_AVAILABLE = False
        
        def transcribe_segment_words(video_path, start_sec, duration):
            return None

# ============================================================
# CONFIGURATION
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output_segments")
SHORTS_FOLDER = os.path.join(BASE_DIR, "shorts_theodore")

# Configuration des sous-titres
ADD_SUBTITLES = True  # Activer les sous-titres dynamiques par défaut
USE_TRANSCRIPTION = True  # Utiliser le moteur de transcription

SUBTITLE_STYLE = {
    'font': 'Arial',
    'font_size': 48,  # Taille adaptée pour les shorts
    'primary_color': '&H00FFFFFF',  # Blanc
    'outline_color': '&H00000000',  # Noir
    'outline_width': 4,
    'position': 'center',  # bottom, center, top
}

# Durée cible pour les Shorts (en secondes)
SHORT_MIN_DURATION = 3     # Minimum 3 secondes (pour les tests)
SHORT_MAX_DURATION = 60    # Maximum 60 secondes (1 minute)
SHORT_TARGET_DURATION = 30 # Durée idéale : 30 secondes

# Configuration des sous-titres MOT PAR MOT
WORDS_PER_GROUP = 4        # Nombre de mots affichés simultanément
MIN_WORD_DURATION = 0.15   # Durée minimum par mot (en secondes)


# Note: La fonction transcribe_segment est importée depuis transcription_engine.py
# si faster-whisper est disponible, sinon on utilise whisper standard


def group_words_for_display(word_timestamps, words_per_group=WORDS_PER_GROUP):
    """
    Regroupe les mots par paquets pour un affichage style YouTube/TikTok.
    Au lieu d'afficher chaque mot individuellement, on affiche des groupes
    de mots qui apparaissent et disparaissent ensemble.
    
    Args:
        word_timestamps: Liste de (start, end, word) pour chaque mot
        words_per_group: Nombre de mots par groupe (défaut: 4)
    
    Returns:
        Liste de (group_start, group_end, group_text) pour l'affichage
    """
    if not word_timestamps:
        return []
    
    groups = []
    current_group = []
    
    for start, end, word in word_timestamps:
        current_group.append((start, end, word))
        
        # Quand on a assez de mots, créer un groupe
        if len(current_group) >= words_per_group:
            group_start = current_group[0][0]
            group_end = current_group[-1][1]
            
            # Assurer une durée minimum pour la lisibilité
            if group_end - group_start < MIN_WORD_DURATION * len(current_group):
                group_end = group_start + MIN_WORD_DURATION * len(current_group)
            
            group_text = " ".join([w[2] for w in current_group])
            groups.append((group_start, group_end, group_text))
            current_group = []
    
    # Ne pas oublier le dernier groupe partiel
    if current_group:
        group_start = current_group[0][0]
        group_end = current_group[-1][1]
        
        # Assurer une durée minimum
        if group_end - group_start < MIN_WORD_DURATION * len(current_group):
            group_end = group_start + MIN_WORD_DURATION * len(current_group)
        
        group_text = " ".join([w[2] for w in current_group])
        groups.append((group_start, group_end, group_text))
    
    # S'assurer que les groupes ne se chevauchent pas
    for i in range(1, len(groups)):
        if groups[i][0] < groups[i-1][1]:
            # Ajuster le début du groupe suivant
            groups[i] = (groups[i-1][1], groups[i][1], groups[i][2])
    
    return groups


def create_srt_from_transcription(transcription_segments, output_path):
    """
    Crée un fichier SRT à partir de la transcription.
    
    Args:
        transcription_segments: Liste de (start, end, text)
        output_path: Chemin du fichier SRT à créer
    
    Returns:
        True si succès
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, (start, end, text) in enumerate(transcription_segments, 1):
                # Format SRT: HH:MM:SS,mmm
                start_time = format_srt_time(start)
                end_time = format_srt_time(end)
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")
        return True
    except Exception as e:
        print(f"   ⚠️ Erreur création SRT: {e}")
        return False


def format_srt_time(seconds):
    """Convertit des secondes en format SRT (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def create_ass_from_transcription(transcription_segments, output_path):
    """
    Crée un fichier ASS (sous-titres avancés) à partir de la transcription.
    Le format ASS supporte mieux le style et le timing que SRT.
    
    Args:
        transcription_segments: Liste de (start, end, text)
        output_path: Chemin du fichier ASS à créer
    
    Returns:
        True si succès
    """
    style = SUBTITLE_STYLE
    
    # Déterminer l'alignement
    if style['position'] == 'bottom':
        alignment = 2  # Bas centre
        margin_v = 60
    elif style['position'] == 'top':
        alignment = 8  # Haut centre
        margin_v = 30
    else:  # center
        alignment = 5  # Centre
        margin_v = 0
    
    ass_header = f"""[Script Info]
Title: Frere Theodore Subtitles
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{style['font_size']},&H00FFFF00,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,1,{alignment},10,10,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ass_header)
            
            for start, end, text in transcription_segments:
                start_time = seconds_to_ass_time(start)
                end_time = seconds_to_ass_time(end)
                
                # Nettoyer le texte pour ASS
                clean_text = text.replace('\\', '\\\\').replace('{', '\\{').replace('}', '\\}')
                
                f.write(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{clean_text}\n")
        
        return True
    except Exception as e:
        print(f"   ⚠️ Erreur création ASS: {e}")
        return False


def create_subtitle_filter_from_transcription(transcription_segments, duration):
    """
    Crée un filtre FFmpeg drawtext à partir de la transcription Whisper.
    DEPRECATED: Utiliser create_ass_from_transcription à la place.
    """
    style = SUBTITLE_STYLE
    
    # Position Y
    if style['position'] == 'bottom':
        y_expr = "h-100"
    elif style['position'] == 'top':
        y_expr = "100"
    else:
        y_expr = "(h-text_h)/2"
    
    filters = []
    
    for start, end, text in transcription_segments:
        # Nettoyer le texte pour FFmpeg (enlever tous les caractères problématiques)
        clean_text = text
        # Enlever les caractères spéciaux
        for char in ["'", '"', ":", "\\", "[", "]", "{", "}", "(", ")", ";", ","]:
            clean_text = clean_text.replace(char, "")
        # Remplacer les accents problématiques
        clean_text = clean_text.replace("é", "e").replace("è", "e").replace("ê", "e")
        clean_text = clean_text.replace("à", "a").replace("â", "a")
        clean_text = clean_text.replace("ù", "u").replace("û", "u")
        clean_text = clean_text.replace("î", "i").replace("ï", "i")
        clean_text = clean_text.replace("ô", "o")
        clean_text = clean_text.replace("ç", "c")
        clean_text = clean_text.replace("É", "E").replace("È", "E")
        clean_text = clean_text.replace("À", "A")
        clean_text = clean_text.strip()
        
        if not clean_text:
            continue
        
        # Limiter la longueur
        if len(clean_text) > 40:
            words = clean_text.split()
            if len(words) > 6:
                clean_text = " ".join(words[:6]) + "..."
        
        # Créer le filtre drawtext
        filter_str = (
            f"drawtext=text='{clean_text}'"
            f":fontsize={style['font_size']}"
            f":fontcolor=yellow"
            f":borderw=3"
            f":bordercolor=black"
            f":x=(w-text_w)/2"
            f":y={y_expr}"
            f":enable='between(t,{start:.2f},{end:.2f})'"
        )
        filters.append(filter_str)
    
    if not filters:
        return None
    
    return ",".join(filters)


def format_time(seconds):
    """Convertit des secondes en format HH:MM:SS"""
    return str(timedelta(seconds=int(seconds)))


def format_ffmpeg_time(seconds):
    """Convertit des secondes en format HH:MM:SS.mmm pour FFmpeg"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def seconds_to_ass_time(seconds):
    """Convertit des secondes en temps ASS (H:MM:SS.cc)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    centisecs = int((secs % 1) * 100)
    secs = int(secs)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"


def create_dynamic_subtitle_filter(duration, text_lines=None):
    """
    Crée un filtre FFmpeg drawtext avec animation dynamique.
    Style TikTok/Reels avec texte animé mot par mot.
    
    Args:
        duration: Durée de la vidéo en secondes
        text_lines: Liste de textes à afficher (optionnel)
    
    Returns:
        Chaîne de filtre FFmpeg drawtext
    """
    style = SUBTITLE_STYLE
    
    # Position Y selon la configuration
    if style['position'] == 'bottom':
        y_expr = "h-100"
    elif style['position'] == 'top':
        y_expr = "100"
    else:  # center
        y_expr = "(h-text_h)/2"
    
    # Si pas de texte fourni, utiliser des textes par défaut
    if not text_lines:
        text_lines = [
            "Frere Theodore",
            "Parole en cours",
            "Ecoutez bien"
        ]
    
    # Distribuer les textes sur la durée
    filters = []
    segment_duration = duration / len(text_lines) if text_lines else duration
    
    for i, text in enumerate(text_lines):
        start_time = i * segment_duration
        end_time = (i + 1) * segment_duration
        
        # Nettoyer le texte (pas de caractères spéciaux)
        clean_text = text.replace("'", "").replace(":", "").replace("\\", "")
        
        # Créer le filtre drawtext avec enable pour le timing
        # Le texte apparaît/disparaît selon le temps
        filter_str = (
            f"drawtext=text='{clean_text}'"
            f":fontsize={style['font_size']}"
            f":fontcolor=white"
            f":borderw=4"
            f":bordercolor=black"
            f":x=(w-text_w)/2"
            f":y={y_expr}"
            f":enable='between(t,{start_time:.2f},{end_time:.2f})'"
        )
        filters.append(filter_str)
    
    # Combiner tous les filtres
    return ",".join(filters)


def create_demo_subtitles_ass(duration, text_lines=None):
    """
    Crée un fichier ASS avec des sous-titres de démonstration.
    En attendant la transcription automatique, on affiche un texte générique.
    
    Args:
        duration: Durée de la vidéo en secondes
        text_lines: Liste de textes à afficher (optionnel)
    """
    style = SUBTITLE_STYLE
    
    if style['position'] == 'bottom':
        alignment = 2
        margin_v = 80
    elif style['position'] == 'top':
        alignment = 8
        margin_v = 30
    else:  # center
        alignment = 5
        margin_v = 0
    
    ass_content = f"""[Script Info]
Title: Dynamic Subtitles - Frère Théodore
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Dynamic,{style['font']},{style['font_size']},{style['primary_color']},&H000000FF,{style['outline_color']},&H80000000,1,0,0,0,100,100,0,0,1,{style['outline_width']},2,{alignment},10,10,{margin_v},1
Style: Highlight,{style['font']},{style['font_size']},&H0000FFFF,&H000000FF,{style['outline_color']},&H80000000,1,0,0,0,100,100,0,0,1,{style['outline_width']},2,{alignment},10,10,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    # Si pas de texte fourni, utiliser des textes par défaut
    if not text_lines:
        text_lines = [
            "🎤 Frère Théodore",
            "💬 Parole en cours...",
            "✨ Écoutez bien!",
        ]
    
    # Distribuer les textes sur la durée
    segment_duration = duration / len(text_lines) if text_lines else duration
    
    for i, text in enumerate(text_lines):
        start_sec = i * segment_duration
        end_sec = (i + 1) * segment_duration
        
        start_time = seconds_to_ass_time(start_sec)
        end_time = seconds_to_ass_time(end_sec)
        
        # Effet de surbrillance mot par mot
        words = text.split()
        if len(words) > 1:
            # Animer chaque mot
            word_duration = segment_duration / len(words)
            for j, word in enumerate(words):
                word_start = start_sec + (j * word_duration)
                word_end = word_start + word_duration
                
                # Construire le texte avec le mot actuel en surbrillance
                highlighted_text = ""
                for k, w in enumerate(words):
                    if k == j:
                        highlighted_text += f"{{\\c&H00FFFF&}}{w}{{\\c&HFFFFFF&}} "
                    else:
                        highlighted_text += f"{w} "
                
                ass_content += f"Dialogue: 0,{seconds_to_ass_time(word_start)},{seconds_to_ass_time(word_end)},Dynamic,,0,0,0,,{highlighted_text.strip()}\n"
        else:
            ass_content += f"Dialogue: 0,{start_time},{end_time},Dynamic,,0,0,0,,{text}\n"
    
    return ass_content


def read_timestamps(timestamps_file):
    """
    Lit le fichier de timestamps généré par detect_theodore.py
    
    Returns:
        Liste de tuples (start_seconds, end_seconds)
    """
    segments = []
    
    if not os.path.exists(timestamps_file):
        print(f"❌ Fichier de timestamps non trouvé: {timestamps_file}")
        return segments
    
    with open(timestamps_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Format attendu: "1. 00:00:00 → 00:10:57"
            line = line.strip()
            if '→' in line and line[0].isdigit():
                parts = line.split('→')
                if len(parts) == 2:
                    start_str = parts[0].split('.')[-1].strip()
                    end_str = parts[1].strip()
                    
                    # Conversion HH:MM:SS en secondes
                    try:
                        start_parts = start_str.split(':')
                        end_parts = end_str.split(':')
                        
                        start_sec = int(start_parts[0]) * 3600 + int(start_parts[1]) * 60 + int(start_parts[2])
                        end_sec = int(end_parts[0]) * 3600 + int(end_parts[1]) * 60 + int(end_parts[2])
                        
                        segments.append((start_sec, end_sec))
                    except (ValueError, IndexError):
                        continue
    
    return segments


def split_into_shorts(segments):
    """
    Divise les segments longs en morceaux de durée adaptée aux Shorts.
    
    Args:
        segments: Liste de (start, end) en secondes
    
    Returns:
        Liste de (start, end) pour chaque Short
    """
    shorts = []
    
    for start, end in segments:
        duration = end - start
        
        if duration <= SHORT_MAX_DURATION:
            # Le segment est déjà assez court
            if duration >= SHORT_MIN_DURATION:
                shorts.append((start, end))
        else:
            # Diviser en plusieurs Shorts
            current_start = start
            while current_start < end:
                current_end = min(current_start + SHORT_TARGET_DURATION, end)
                remaining = end - current_end
                
                # Si le reste est trop court, on l'inclut dans ce Short
                if remaining > 0 and remaining < SHORT_MIN_DURATION:
                    current_end = end
                
                # Vérifier que le Short a une durée minimale
                if current_end - current_start >= SHORT_MIN_DURATION:
                    shorts.append((current_start, current_end))
                
                current_start = current_end
    
    return shorts


def extract_short(video_path, start_sec, end_sec, output_path, vertical=False, add_subtitles=True):
    """
    Extrait un segment vidéo avec FFmpeg et sous-titres transcrits MOT PAR MOT.
    Style YouTube/TikTok avec synchronisation temps réel.
    
    Args:
        video_path: Chemin de la vidéo source
        start_sec: Début en secondes
        end_sec: Fin en secondes
        output_path: Chemin du fichier de sortie
        vertical: Si True, recadre en format 9:16 (vertical)
        add_subtitles: Si True, ajoute des sous-titres dynamiques
    """
    duration = end_sec - start_sec
    word_transcription = None
    vf_filters = []
    
    # Transcription MOT PAR MOT avec timestamps précis
    if add_subtitles and ADD_SUBTITLES and USE_TRANSCRIPTION and WHISPER_AVAILABLE:
        print(f"         🎤 Transcription MOT PAR MOT ({TRANSCRIPTION_ENGINE})...")
        word_transcription = transcribe_segment_words(video_path, start_sec, duration)
        
        if word_transcription:
            print(f"         ✅ {len(word_transcription)} mot(s) avec timestamps")
        else:
            print(f"         ⚠️ Fallback vers transcription par phrase")
            # Fallback: transcription classique
            transcription = transcribe_segment(video_path, start_sec, duration)
            if transcription:
                print(f"         ✅ {len(transcription)} phrase(s)")
    
    # Ajouter le filtre de recadrage vertical si demandé
    if vertical:
        vf_filters.append("crop=ih*9/16:ih,scale=1080:1920")
    
    # Style des sous-titres
    style = SUBTITLE_STYLE
    y_expr = "(h-text_h)/2" if style['position'] == 'center' else ("h-80" if style['position'] == 'bottom' else "80")
    
    # Mode MOT PAR MOT (prioritaire) - Style YouTube/TikTok
    if word_transcription:
        # Grouper les mots par paquets de 3-5 pour un meilleur affichage
        word_groups = group_words_for_display(word_transcription)
        
        for group_start, group_end, group_text in word_groups:
            clean_text = sanitize_text_for_ffmpeg(group_text)
            if not clean_text:
                continue
            
            # Créer le filtre drawtext avec timing précis
            drawtext = (
                f"drawtext=text='{clean_text}'"
                f":fontsize={style['font_size']}"
                f":fontcolor=yellow"
                f":borderw=3"
                f":bordercolor=black"
                f":x=(w-text_w)/2"
                f":y={y_expr}"
                f":enable='between(t\\,{group_start:.3f}\\,{group_end:.3f})'"
            )
            vf_filters.append(drawtext)
    
    # Mode Phrase (fallback)
    elif 'transcription' in dir() and transcription:
        for start, end, text in transcription:
            clean_text = sanitize_text_for_ffmpeg(text)
            if not clean_text:
                continue
            
            drawtext = (
                f"drawtext=text='{clean_text}'"
                f":fontsize={style['font_size']}"
                f":fontcolor=yellow"
                f":borderw=3"
                f":bordercolor=black"
                f":x=(w-text_w)/2"
                f":y={y_expr}"
                f":enable='between(t\\,{start:.2f}\\,{end:.2f})'"
            )
            vf_filters.append(drawtext)
    
    # Construction de la commande FFmpeg
    if vf_filters:
        vf_filter = ",".join(vf_filters)
        
        cmd = [
            FFMPEG_PATH,
            '-y',
            '-ss', format_ffmpeg_time(start_sec),
            '-i', video_path,
            '-t', str(duration),
            '-vf', vf_filter,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-avoid_negative_ts', 'make_zero',
            output_path
        ]
    else:
        # Sans sous-titres : copie directe (plus rapide)
        cmd = [
            FFMPEG_PATH,
            '-y',
            '-ss', format_ffmpeg_time(start_sec),
            '-i', video_path,
            '-t', str(duration),
            '-c', 'copy',
            '-avoid_negative_ts', 'make_zero',
            output_path
        ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        success = result.returncode == 0
        
        if not success and result.stderr:
            # Afficher seulement les erreurs pertinentes
            stderr_lines = result.stderr.split('\n')
            for line in stderr_lines:
                if 'Error' in line or 'error' in line:
                    print(f"   ⚠️ FFmpeg: {line[:100]}")
                    break
        
        return success
    except subprocess.TimeoutExpired:
        print(f"   ⚠️ Timeout lors de l'extraction")
        return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def sanitize_text_for_ffmpeg(text):
    """
    Nettoie le texte pour l'utiliser dans un filtre drawtext FFmpeg.
    Garde TOUT le texte sans le tronquer.
    """
    clean = text
    # Caractères à supprimer complètement
    for char in ["'", '"', ":", "\\", "[", "]", "{", "}", "(", ")", ";", "%"]:
        clean = clean.replace(char, "")
    # Remplacer la virgule par rien (problème avec enable)
    clean = clean.replace(",", " ")
    # Remplacer les accents
    accents = {
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "à": "a", "â": "a", "ä": "a",
        "ù": "u", "û": "u", "ü": "u",
        "î": "i", "ï": "i",
        "ô": "o", "ö": "o",
        "ç": "c",
        "É": "E", "È": "E", "Ê": "E",
        "À": "A", "Â": "A",
        "Ù": "U", "Û": "U",
        "Î": "I",
        "Ô": "O",
        "Ç": "C"
    }
    for acc, repl in accents.items():
        clean = clean.replace(acc, repl)
    
    clean = clean.strip()
    
    # NE PAS tronquer - garder tout le texte
    # Si le texte est trop long, on le garde quand même
    # FFmpeg gérera l'affichage
    
    return clean


def generate_shorts(video_path, vertical_format=False, with_subtitles=True):
    """
    Fonction principale : Génère les Shorts à partir d'une vidéo.
    
    Args:
        video_path: Chemin vers la vidéo source
        vertical_format: Si True, convertit en format 9:16
        with_subtitles: Si True, ajoute des sous-titres dynamiques
    """
    
    print("\n" + "="*60)
    print("🎬 GÉNÉRATION DES SHORTS - FRÈRE THÉODORE")
    if with_subtitles:
        print("📝 Avec sous-titres dynamiques")
    print("="*60)
    
    # 1. Vérifications
    if not os.path.exists(video_path):
        print(f"❌ Vidéo non trouvée: {video_path}")
        return
    
    timestamps_file = os.path.join(OUTPUT_FOLDER, "theodore_timestamps.txt")
    if not os.path.exists(timestamps_file):
        print(f"❌ Fichier de timestamps non trouvé: {timestamps_file}")
        print("   Veuillez d'abord exécuter detect_theodore.py")
        return
    
    # Création du dossier de sortie
    os.makedirs(SHORTS_FOLDER, exist_ok=True)
    
    # 2. Lecture des timestamps
    print(f"\n📂 Vidéo source: {os.path.basename(video_path)}")
    print(f"📋 Lecture des timestamps...")
    
    segments = read_timestamps(timestamps_file)
    if not segments:
        print("❌ Aucun segment trouvé dans le fichier de timestamps")
        return
    
    print(f"   {len(segments)} séquences de Théodore trouvées")
    
    # 3. Division en Shorts
    print(f"\n✂️ Division en Shorts (durée cible: {SHORT_TARGET_DURATION}s)...")
    shorts = split_into_shorts(segments)
    print(f"   {len(shorts)} Shorts à générer")
    
    # 4. Extraction des Shorts
    print(f"\n🎬 Extraction des vidéos...")
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    successful = 0
    
    for i, (start, end) in enumerate(shorts, 1):
        duration = end - start
        output_name = f"short_{video_name}_{i:03d}_{int(start)}s-{int(end)}s.mp4"
        output_path = os.path.join(SHORTS_FOLDER, output_name)
        
        print(f"   [{i}/{len(shorts)}] {format_time(start)} → {format_time(end)} ({duration:.0f}s)")
        
        if extract_short(video_path, start, end, output_path, vertical=vertical_format, add_subtitles=with_subtitles):
            successful += 1
            print(f"         ✅ Créé: {output_name}")
        else:
            print(f"         ❌ Échec")
    
    # 5. Résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ")
    print("="*60)
    print(f"\n✅ {successful}/{len(shorts)} Shorts générés avec succès")
    print(f"📁 Dossier de sortie: {SHORTS_FOLDER}")
    
    if successful > 0:
        total_duration = sum(end - start for start, end in shorts[:successful])
        print(f"⏱️ Durée totale extraite: {format_time(total_duration)}")


# ============================================================
# POINT D'ENTRÉE
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("="*60)
        print("🎬 GÉNÉRATEUR DE SHORTS - FRÈRE THÉODORE")
        print("="*60)
        print("\nUsage: python generate_shorts.py <chemin_video> [options]")
        print("\nOptions:")
        print("  --vertical      Convertir en format 9:16 (TikTok/Reels/Shorts)")
        print("  --no-subtitles  Désactiver les sous-titres dynamiques")
        print("\nExemple:")
        print('  python generate_shorts.py "C:\\Videos\\culte.mp4"')
        print('  python generate_shorts.py "C:\\Videos\\culte.mp4" --vertical')
        print('  python generate_shorts.py "C:\\Videos\\culte.mp4" --no-subtitles')
        print("\n⚠️ IMPORTANT: Exécutez d'abord detect_theodore.py sur la même vidéo!")
        sys.exit(1)
    
    video_file = sys.argv[1]
    vertical = "--vertical" in sys.argv
    no_subtitles = "--no-subtitles" in sys.argv
    
    generate_shorts(video_file, vertical_format=vertical, with_subtitles=not no_subtitles)
