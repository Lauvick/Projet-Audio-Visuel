"""
Script d'incrustation de sous-titres dynamiques sur les vidéos.
Style TikTok/Reels avec animation mot par mot.
"""

import os
import sys
import io
import subprocess
import re
from datetime import timedelta

# Forcer l'encodage UTF-8 pour la console Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuration FFmpeg
CONDA_ENV = os.path.dirname(sys.executable)
FFMPEG_PATH = os.path.join(CONDA_ENV, "Library", "bin", "ffmpeg.exe")
if not os.path.exists(FFMPEG_PATH):
    FFMPEG_PATH = "ffmpeg"

# Ajouter FFmpeg au PATH
if os.path.exists(os.path.dirname(FFMPEG_PATH)):
    os.environ["PATH"] = os.path.dirname(FFMPEG_PATH) + os.pathsep + os.environ.get("PATH", "")

# ============================================================
# CONFIGURATION DES SOUS-TITRES
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHORTS_FOLDER = os.path.join(BASE_DIR, "shorts_theodore")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "shorts_avec_soustitres")

# Style des sous-titres dynamiques
SUBTITLE_STYLE = {
    'font': 'Arial',
    'font_size': 24,
    'font_color': 'white',
    'outline_color': 'black',
    'outline_width': 2,
    'position': 'center',  # 'bottom', 'center', 'top'
    'margin_bottom': 50,
    'shadow': True,
    'background': False,  # Fond coloré derrière le texte
    'background_color': 'black@0.5',  # Noir semi-transparent
}


def parse_srt(srt_content):
    """
    Parse un fichier SRT et retourne une liste de sous-titres.
    Format: [(start_sec, end_sec, text), ...]
    """
    subtitles = []
    
    # Pattern pour parser les blocs SRT
    pattern = r'(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s+(.+?)(?=\n\n|\Z)'
    
    matches = re.findall(pattern, srt_content, re.DOTALL)
    
    for match in matches:
        index, start_time, end_time, text = match
        
        # Convertir le temps en secondes
        start_sec = srt_time_to_seconds(start_time)
        end_sec = srt_time_to_seconds(end_time)
        
        # Nettoyer le texte
        text = text.strip().replace('\n', ' ')
        
        subtitles.append((start_sec, end_sec, text))
    
    return subtitles


def srt_time_to_seconds(time_str):
    """Convertit un temps SRT (00:00:00,000) en secondes."""
    time_str = time_str.replace(',', '.')
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def seconds_to_srt_time(seconds):
    """Convertit des secondes en temps SRT."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')


def create_ass_style():
    """
    Crée le style ASS pour les sous-titres dynamiques.
    ASS permet plus de contrôle que SRT pour l'animation.
    """
    style = SUBTITLE_STYLE
    
    # Convertir la couleur en format ASS (BGR inversé)
    # ASS utilise &HAABBGGRR
    primary_color = "&H00FFFFFF"  # Blanc
    outline_color = "&H00000000"  # Noir
    
    if style['position'] == 'bottom':
        alignment = 2  # Bas centre
        margin_v = style['margin_bottom']
    elif style['position'] == 'top':
        alignment = 8  # Haut centre
        margin_v = 30
    else:  # center
        alignment = 5  # Centre
        margin_v = 0
    
    ass_style = f"""[Script Info]
Title: Dynamic Subtitles
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Dynamic,{style['font']},{style['font_size'] * 3},{primary_color},&H000000FF,{outline_color},&H80000000,1,0,0,0,100,100,0,0,1,{style['outline_width'] * 2},{2 if style['shadow'] else 0},{alignment},10,10,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    return ass_style


def create_word_by_word_ass(subtitles, words_per_highlight=3):
    """
    Crée un fichier ASS avec effet mot par mot (style karaoké/TikTok).
    """
    ass_content = create_ass_style()
    
    for start_sec, end_sec, text in subtitles:
        words = text.split()
        if not words:
            continue
        
        duration = end_sec - start_sec
        word_duration = duration / len(words) if words else duration
        
        # Pour chaque groupe de mots
        for i in range(0, len(words), words_per_highlight):
            group_start = start_sec + (i * word_duration)
            group_end = min(start_sec + ((i + words_per_highlight) * word_duration), end_sec)
            
            # Créer le texte avec le groupe actuel en surbrillance
            highlighted_text = ""
            for j, word in enumerate(words):
                if i <= j < i + words_per_highlight:
                    # Mot en surbrillance (jaune/doré)
                    highlighted_text += f"{{\\c&H00FFFF&}}{word}{{\\c&HFFFFFF&}} "
                else:
                    highlighted_text += f"{word} "
            
            start_time = seconds_to_ass_time(group_start)
            end_time = seconds_to_ass_time(group_end)
            
            ass_content += f"Dialogue: 0,{start_time},{end_time},Dynamic,,0,0,0,,{highlighted_text.strip()}\n"
    
    return ass_content


def seconds_to_ass_time(seconds):
    """Convertit des secondes en temps ASS (H:MM:SS.cc)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    centisecs = int((secs % 1) * 100)
    secs = int(secs)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"


def add_subtitles_to_video(video_path, srt_path=None, srt_content=None, output_path=None, style='dynamic'):
    """
    Ajoute des sous-titres à une vidéo.
    
    Args:
        video_path: Chemin de la vidéo source
        srt_path: Chemin du fichier SRT (optionnel)
        srt_content: Contenu SRT en string (optionnel)
        output_path: Chemin de sortie (optionnel)
        style: 'dynamic' (mot par mot) ou 'classic' (normal)
    """
    if not os.path.exists(video_path):
        print(f"❌ Vidéo non trouvée: {video_path}")
        return False
    
    # Charger les sous-titres
    if srt_path and os.path.exists(srt_path):
        with open(srt_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
    
    if not srt_content:
        print("❌ Aucun sous-titre fourni")
        return False
    
    # Parser les sous-titres
    subtitles = parse_srt(srt_content)
    
    if not subtitles:
        print("❌ Aucun sous-titre valide trouvé")
        return False
    
    print(f"📝 {len(subtitles)} sous-titre(s) trouvé(s)")
    
    # Créer le dossier de sortie
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # Définir le chemin de sortie
    if not output_path:
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(OUTPUT_FOLDER, f"{base_name}_soustitre.mp4")
    
    # Créer le fichier ASS temporaire
    if style == 'dynamic':
        ass_content = create_word_by_word_ass(subtitles)
    else:
        ass_content = create_ass_style()
        for start_sec, end_sec, text in subtitles:
            start_time = seconds_to_ass_time(start_sec)
            end_time = seconds_to_ass_time(end_sec)
            ass_content += f"Dialogue: 0,{start_time},{end_time},Dynamic,,0,0,0,,{text}\n"
    
    # Sauvegarder le fichier ASS temporaire
    ass_temp_path = os.path.join(BASE_DIR, "temp_subtitles.ass")
    with open(ass_temp_path, 'w', encoding='utf-8') as f:
        f.write(ass_content)
    
    print(f"🎬 Incrustation des sous-titres...")
    
    # Commande FFmpeg pour incruster les sous-titres
    # Échapper les caractères spéciaux Windows dans le chemin
    ass_path_escaped = ass_temp_path.replace('\\', '/').replace(':', '\\:')
    
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-i', video_path,
        '-vf', f"ass='{ass_path_escaped}'",
        '-c:v', 'libx264',
        '-c:a', 'copy',
        '-preset', 'fast',
        '-crf', '23',
        output_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ Vidéo créée: {os.path.basename(output_path)}")
            # Nettoyer le fichier temporaire
            if os.path.exists(ass_temp_path):
                os.remove(ass_temp_path)
            return True
        else:
            print(f"❌ Erreur FFmpeg: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout lors de l'incrustation")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def add_simple_text_overlay(video_path, text, position='bottom', output_path=None):
    """
    Ajoute un texte simple (titre, watermark) sur une vidéo.
    
    Args:
        video_path: Chemin de la vidéo source
        text: Texte à afficher
        position: 'top', 'center', 'bottom'
        output_path: Chemin de sortie (optionnel)
    """
    if not os.path.exists(video_path):
        print(f"❌ Vidéo non trouvée: {video_path}")
        return False
    
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    if not output_path:
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(OUTPUT_FOLDER, f"{base_name}_texte.mp4")
    
    # Position du texte
    if position == 'top':
        y_pos = "50"
    elif position == 'center':
        y_pos = "(h-text_h)/2"
    else:  # bottom
        y_pos = "h-text_h-50"
    
    # Filtre drawtext
    drawtext_filter = (
        f"drawtext=text='{text}':"
        f"fontfile='C\\:/Windows/Fonts/arial.ttf':"
        f"fontsize=48:"
        f"fontcolor=white:"
        f"borderw=3:"
        f"bordercolor=black:"
        f"x=(w-text_w)/2:"
        f"y={y_pos}"
    )
    
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-i', video_path,
        '-vf', drawtext_filter,
        '-c:v', 'libx264',
        '-c:a', 'copy',
        '-preset', 'fast',
        '-crf', '23',
        output_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ Vidéo créée: {os.path.basename(output_path)}")
            return True
        else:
            print(f"❌ Erreur FFmpeg: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def main():
    """Fonction principale - test des sous-titres."""
    print("\n" + "=" * 60)
    print("🎬 INCRUSTATION DE SOUS-TITRES DYNAMIQUES")
    print("=" * 60)
    
    # Exemple de sous-titres SRT pour test
    exemple_srt = """1
00:00:00,000 --> 00:00:03,000
Bonjour à tous mes frères et sœurs

2
00:00:03,000 --> 00:00:06,000
Aujourd'hui nous allons parler

3
00:00:06,000 --> 00:00:10,000
de la grâce de notre Seigneur
"""
    
    # Chercher un short existant pour tester
    if os.path.exists(SHORTS_FOLDER):
        shorts = [f for f in os.listdir(SHORTS_FOLDER) if f.endswith('.mp4')]
        if shorts:
            test_video = os.path.join(SHORTS_FOLDER, shorts[0])
            print(f"\n📂 Test avec: {shorts[0]}")
            print("📝 Utilisation de sous-titres exemple...")
            
            success = add_subtitles_to_video(
                test_video,
                srt_content=exemple_srt,
                style='dynamic'
            )
            
            if success:
                print(f"\n✅ Test réussi! Vidéo dans: {OUTPUT_FOLDER}")
            else:
                print("\n❌ Échec du test")
        else:
            print("\n⚠️ Aucun short trouvé pour tester")
            print(f"   Placez des vidéos dans: {SHORTS_FOLDER}")
    else:
        print(f"\n⚠️ Dossier non trouvé: {SHORTS_FOLDER}")
    
    print("\n" + "=" * 60)
    print("💡 Utilisation:")
    print("   from add_subtitles import add_subtitles_to_video")
    print("   add_subtitles_to_video('video.mp4', srt_path='soustitres.srt')")
    print("=" * 60)


if __name__ == "__main__":
    main()
