"""
🎬 Script de Débruitage Vidéo - Projet Audio HERMANN
====================================================
Extrait l'audio d'une vidéo, élimine le bruit, et reconstruit la vidéo.

Formats supportés: MP4, MKV, AVI, MOV, WEBM, etc.

Auteur: Agent IA Copilot
Date: Décembre 2025
"""

import os
import subprocess
import numpy as np
import soundfile as sf
from pathlib import Path
import tempfile
import shutil

# Import de noisereduce pour la dénoisation
try:
    import noisereduce as nr
    NOISEREDUCE_AVAILABLE = True
except ImportError:
    NOISEREDUCE_AVAILABLE = False
    print("⚠️ noisereduce non disponible")


def get_ffmpeg_path():
    """Trouve le chemin de ffmpeg."""
    # Chercher dans l'environnement conda
    conda_env = Path(r"c:\Users\nichi\Documents\HERMANN\Projet_audio\.conda")
    ffmpeg_conda = conda_env / "Library" / "bin" / "ffmpeg.exe"
    
    if ffmpeg_conda.exists():
        return str(ffmpeg_conda)
    
    # Sinon chercher dans le PATH
    result = shutil.which("ffmpeg")
    if result:
        return result
    
    return "ffmpeg"  # Espérer que c'est dans le PATH


def denoise_video(input_video, output_video=None, extract_vocals=False):
    """
    Débruite l'audio d'une vidéo.
    
    Args:
        input_video: Chemin vers la vidéo source
        output_video: Chemin de sortie (optionnel, auto-généré si non fourni)
        extract_vocals: Si True, extrait aussi uniquement les voix
    
    Returns:
        Chemin vers la vidéo débruitée
    """
    print("\n" + "="*60)
    print("🎬 DÉBRUITAGE VIDÉO - PROJET HERMANN")
    print("="*60)
    
    # Vérifications
    if not os.path.exists(input_video):
        print(f"❌ Fichier introuvable: {input_video}")
        return None
    
    ffmpeg = get_ffmpeg_path()
    print(f"📂 Vidéo source: {input_video}")
    print(f"🔧 FFmpeg: {ffmpeg}")
    
    # Générer le nom de sortie si non fourni
    input_path = Path(input_video)
    if output_video is None:
        output_video = str(input_path.parent / f"{input_path.stem}_denoised{input_path.suffix}")
    
    print(f"📁 Vidéo sortie: {output_video}")
    
    # Créer un dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="video_denoise_")
    temp_audio = os.path.join(temp_dir, "audio_extracted.wav")
    temp_audio_clean = os.path.join(temp_dir, "audio_clean.wav")
    
    try:
        # === ÉTAPE 1: Extraire l'audio de la vidéo ===
        print("\n" + "-"*40)
        print("📌 ÉTAPE 1: Extraction de l'audio")
        print("-"*40)
        
        cmd_extract = [
            ffmpeg, "-i", input_video,
            "-vn",  # Pas de vidéo
            "-acodec", "pcm_s16le",  # Format WAV 16-bit
            "-ar", "48000",  # 48kHz
            "-ac", "2",  # Stéréo
            "-y",  # Écraser si existe
            temp_audio
        ]
        
        print(f"   Extraction en cours...")
        result = subprocess.run(cmd_extract, capture_output=True, text=True)
        
        if not os.path.exists(temp_audio):
            print(f"❌ Échec de l'extraction audio")
            print(f"   Erreur: {result.stderr}")
            return None
        
        print(f"   ✅ Audio extrait: {os.path.getsize(temp_audio) / 1024 / 1024:.2f} MB")
        
        # === ÉTAPE 2: Charger et débruiter l'audio ===
        print("\n" + "-"*40)
        print("📌 ÉTAPE 2: Débruitage de l'audio")
        print("-"*40)
        
        # Charger l'audio
        audio, sr = sf.read(temp_audio)
        print(f"   - Fréquence: {sr} Hz")
        print(f"   - Durée: {len(audio)/sr:.2f} secondes")
        print(f"   - Canaux: {audio.shape[1] if len(audio.shape) > 1 else 1}")
        
        # Débruitage avec noisereduce
        if NOISEREDUCE_AVAILABLE:
            print(f"\n   🧠 Application de noisereduce (IA)...")
            
            # Traiter chaque canal séparément si stéréo
            if len(audio.shape) > 1 and audio.shape[1] == 2:
                audio_clean_L = nr.reduce_noise(
                    y=audio[:, 0], 
                    sr=sr,
                    stationary=False,
                    prop_decrease=0.85,
                    freq_mask_smooth_hz=500,
                    time_mask_smooth_ms=50
                )
                audio_clean_R = nr.reduce_noise(
                    y=audio[:, 1], 
                    sr=sr,
                    stationary=False,
                    prop_decrease=0.85,
                    freq_mask_smooth_hz=500,
                    time_mask_smooth_ms=50
                )
                audio_clean = np.stack([audio_clean_L, audio_clean_R], axis=1)
            else:
                # Mono
                if len(audio.shape) > 1:
                    audio_mono = np.mean(audio, axis=1)
                else:
                    audio_mono = audio
                    
                audio_clean = nr.reduce_noise(
                    y=audio_mono, 
                    sr=sr,
                    stationary=False,
                    prop_decrease=0.85,
                    freq_mask_smooth_hz=500,
                    time_mask_smooth_ms=50
                )
                # Convertir en stéréo
                audio_clean = np.stack([audio_clean, audio_clean], axis=1)
            
            print(f"   ✅ Débruitage terminé!")
        else:
            print("   ⚠️ noisereduce non disponible, audio non modifié")
            audio_clean = audio
        
        # Normalisation
        max_val = np.max(np.abs(audio_clean))
        if max_val > 0:
            audio_clean = audio_clean / max_val * 0.95
        
        # Sauvegarder l'audio nettoyé
        sf.write(temp_audio_clean, audio_clean, sr)
        print(f"   ✅ Audio nettoyé sauvegardé")
        
        # === ÉTAPE 3: Reconstruire la vidéo ===
        print("\n" + "-"*40)
        print("📌 ÉTAPE 3: Reconstruction de la vidéo")
        print("-"*40)
        
        cmd_merge = [
            ffmpeg, 
            "-i", input_video,  # Vidéo originale
            "-i", temp_audio_clean,  # Audio nettoyé
            "-c:v", "copy",  # Copier la vidéo sans ré-encoder
            "-c:a", "aac",  # Encoder l'audio en AAC
            "-b:a", "192k",  # Bitrate audio
            "-map", "0:v:0",  # Prendre la vidéo du premier fichier
            "-map", "1:a:0",  # Prendre l'audio du second fichier
            "-shortest",  # S'arrêter au plus court
            "-y",  # Écraser si existe
            output_video
        ]
        
        print(f"   Reconstruction en cours...")
        result = subprocess.run(cmd_merge, capture_output=True, text=True)
        
        if not os.path.exists(output_video):
            print(f"❌ Échec de la reconstruction")
            print(f"   Erreur: {result.stderr}")
            return None
        
        print(f"   ✅ Vidéo reconstruite!")
        
        # === Résumé ===
        print("\n" + "="*60)
        print("✅ DÉBRUITAGE VIDÉO TERMINÉ!")
        print("="*60)
        
        input_size = os.path.getsize(input_video) / 1024 / 1024
        output_size = os.path.getsize(output_video) / 1024 / 1024
        
        print(f"\n📊 Résumé:")
        print(f"   - Vidéo originale: {input_size:.2f} MB")
        print(f"   - Vidéo débruitée: {output_size:.2f} MB")
        print(f"\n🎬 Fichier de sortie: {output_video}")
        
        return output_video
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        # Nettoyer les fichiers temporaires
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


def main():
    """Point d'entrée principal."""
    print("\n" + "="*60)
    print("🎬 DÉBRUITAGE VIDÉO - PROJET HERMANN")
    print("="*60)
    print("\nCe script élimine le bruit de fond d'une vidéo.")
    print("\n📋 Formats supportés: MP4, MKV, AVI, MOV, WEBM, etc.")
    
    # Chercher les fichiers vidéo dans le dossier
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.m4v', '.flv']
    videos_found = []
    
    for ext in video_extensions:
        videos_found.extend(Path(".").glob(f"*{ext}"))
    
    if videos_found:
        print(f"\n📁 Vidéos trouvées dans le dossier:")
        for i, v in enumerate(videos_found, 1):
            size = v.stat().st_size / 1024 / 1024
            print(f"   {i}. {v.name} ({size:.2f} MB)")
        
        # Traiter la première vidéo trouvée
        video_to_process = str(videos_found[0])
        print(f"\n🎯 Traitement de: {video_to_process}")
        denoise_video(video_to_process)
    else:
        print("\n⚠️ Aucune vidéo trouvée dans le dossier.")
        print("   Placez votre fichier vidéo (MP4, MKV, etc.) dans ce dossier")
        print("   puis relancez le script.")
        print("\n   Ou utilisez directement:")
        print("   >>> from denoise_video import denoise_video")
        print("   >>> denoise_video('votre_video.mp4')")


if __name__ == "__main__":
    main()
