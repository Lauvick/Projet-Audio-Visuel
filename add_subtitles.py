"""
🎬 Script d'Incrustation de Sous-titres - Projet Audio HERMANN
================================================================
Incruste les sous-titres SRT directement dans la vidéo (hardcoded).
Utilise MoviePy pour un rendu permanent des sous-titres.

Auteur: Agent IA Copilot
Date: Décembre 2025
"""

import os
import re
from pathlib import Path
from moviepy import VideoFileClip, TextClip, CompositeVideoClip


def parse_srt(srt_path):
    """
    Parse un fichier SRT et retourne une liste de sous-titres.
    
    Returns:
        Liste de tuples (start_time, end_time, text)
    """
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern pour extraire les sous-titres
    pattern = r'(\d+)\s+(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})\s+(.+?)(?=\n\n|\n*$)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    subtitles = []
    for match in matches:
        num = int(match[0])
        
        # Temps de début en secondes
        start_h, start_m, start_s, start_ms = int(match[1]), int(match[2]), int(match[3]), int(match[4])
        start_time = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000
        
        # Temps de fin en secondes
        end_h, end_m, end_s, end_ms = int(match[5]), int(match[6]), int(match[7]), int(match[8])
        end_time = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000
        
        # Texte
        text = match[9].strip().replace('\n', ' ')
        
        subtitles.append((start_time, end_time, text))
    
    return subtitles


def create_subtitle_clip(text, video_size, font_size=28, font_color='white', 
                         stroke_color='black', stroke_width=2):
    """
    Crée un clip de texte pour un sous-titre.
    Utilise une police Windows avec support complet des accents français.
    """
    # Police Windows avec support Unicode complet (accents français)
    # Arial Unicode MS ou Segoe UI supportent bien les accents
    fonts_to_try = [
        'C:/Windows/Fonts/arial.ttf',      # Arial standard
        'C:/Windows/Fonts/segoeui.ttf',    # Segoe UI
        'C:/Windows/Fonts/calibri.ttf',    # Calibri
        'Arial',                            # Nom simple
    ]
    
    for font_path in fonts_to_try:
        try:
            txt_clip = TextClip(
                text=text,
                font_size=font_size,
                color=font_color,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                font=font_path,
                method='caption',
                size=(video_size[0] - 40, None),  # Largeur avec marge
                text_align='center'
            )
            return txt_clip
        except Exception:
            continue
    
    # Dernier fallback sans police spécifique
    txt_clip = TextClip(
        text=text,
        font_size=font_size,
        color=font_color,
        stroke_color=stroke_color,
        stroke_width=stroke_width,
        method='caption',
        size=(video_size[0] - 40, None),
        text_align='center'
    )
    
    return txt_clip


def add_subtitles_to_video(video_path, srt_path, output_path=None):
    """
    Incruste les sous-titres SRT dans une vidéo avec MoviePy.
    """
    
    print("\n" + "="*60)
    print("🎬 INCRUSTATION DE SOUS-TITRES (MoviePy)")
    print("="*60)
    
    video_path = Path(video_path)
    srt_path = Path(srt_path)
    
    # Vérifications
    if not video_path.exists():
        print(f"❌ Vidéo non trouvée: {video_path}")
        return None
    
    if not srt_path.exists():
        print(f"❌ Fichier SRT non trouvé: {srt_path}")
        return None
    
    # Générer le nom de sortie
    if output_path is None:
        output_path = video_path.parent / f"{video_path.stem}_subtitled{video_path.suffix}"
    else:
        output_path = Path(output_path)
    
    print(f"📂 Vidéo source: {video_path}")
    print(f"📝 Sous-titres: {srt_path}")
    print(f"📤 Sortie: {output_path}")
    
    # Parser les sous-titres
    print("\n🔄 Lecture des sous-titres...")
    subtitles = parse_srt(str(srt_path))
    print(f"   ✅ {len(subtitles)} sous-titres trouvés")
    
    # Charger la vidéo
    print("\n🔄 Chargement de la vidéo...")
    video = VideoFileClip(str(video_path))
    video_size = video.size
    print(f"   ✅ Durée: {video.duration:.1f}s, Taille: {video_size[0]}x{video_size[1]}")
    
    # Créer les clips de sous-titres
    print("\n🔄 Création des sous-titres...")
    subtitle_clips = []
    
    for i, (start, end, text) in enumerate(subtitles):
        # Créer le clip de texte
        txt_clip = create_subtitle_clip(
            text=text,
            video_size=video_size,
            font_size=28,
            font_color='white',
            stroke_color='black',
            stroke_width=2
        )
        
        # Positionner en bas de l'écran avec marge
        txt_clip = txt_clip.with_position(('center', video_size[1] - 80))
        
        # Définir la durée et le temps de début
        txt_clip = txt_clip.with_start(start).with_duration(end - start)
        
        subtitle_clips.append(txt_clip)
        
        if (i + 1) % 5 == 0 or i == len(subtitles) - 1:
            print(f"   📝 {i + 1}/{len(subtitles)} sous-titres préparés")
    
    # Composer la vidéo finale
    print("\n🔄 Composition de la vidéo...")
    final_video = CompositeVideoClip([video] + subtitle_clips)
    
    # Exporter avec haute qualité
    print("\n🔄 Export en cours (haute qualité - cela peut prendre quelques minutes)...")
    print("-"*40)
    
    # Calculer un bitrate adapté à la résolution
    # Pour 720x1280 (vertical HD), on utilise environ 8-10 Mbps
    video_bitrate = "10M"  # 10 Mbps pour une excellente qualité
    audio_bitrate = "192k"  # 192 kbps pour l'audio
    
    final_video.write_videofile(
        str(output_path),
        codec='libx264',
        audio_codec='aac',
        fps=video.fps,
        preset='slow',          # Plus lent mais meilleure qualité
        bitrate=video_bitrate,  # Bitrate vidéo élevé
        audio_bitrate=audio_bitrate,  # Bitrate audio
        threads=4,
        logger='bar',
        ffmpeg_params=[
            '-crf', '18',       # Qualité constante (0-51, plus bas = meilleur)
            '-pix_fmt', 'yuv420p',  # Format pixel compatible
            '-profile:v', 'high',   # Profil H.264 haute qualité
            '-level', '4.1'         # Niveau de compatibilité
        ]
    )
    
    # Fermer les ressources
    video.close()
    final_video.close()
    
    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"\n✅ Vidéo créée avec succès!")
        print(f"   📁 Fichier: {output_path}")
        print(f"   📊 Taille: {size_mb:.2f} MB")
        return str(output_path)
    else:
        print("❌ Le fichier de sortie n'a pas été créé")
        return None


def main():
    print("\n" + "="*60)
    print("🎬 AJOUT DE SOUS-TITRES - PROJET HERMANN")
    print("="*60)
    print("\nIncruste les sous-titres SRT directement dans la vidéo")
    print("Les sous-titres seront visibles en permanence (hardcoded)")
    
    # Configuration
    video_file = "diane_ann.mp4"
    srt_file = "diane_ann_subtitles.srt"
    
    # Vérifier que les fichiers existent
    if not os.path.exists(video_file):
        print(f"\n⚠️ Vidéo non trouvée: {video_file}")
        return
    
    if not os.path.exists(srt_file):
        print(f"\n⚠️ Fichier SRT non trouvé: {srt_file}")
        print("   Lancez d'abord transcribe_video.py pour générer les sous-titres")
        return
    
    # Incruster les sous-titres
    result = add_subtitles_to_video(
        video_path=video_file,
        srt_path=srt_file
    )
    
    if result:
        print("\n" + "="*60)
        print("🎉 TERMINÉ!")
        print("="*60)
        print(f"\n📹 Vidéo avec sous-titres: {result}")
        print("\n✨ Les sous-titres sont maintenant incrustés en permanence!")
        print("   Vous pouvez lire la vidéo avec n'importe quel lecteur.")


if __name__ == "__main__":
    main()
