"""
📝 Script de Transcription Vidéo/Audio - Projet Audio HERMANN
==============================================================
Utilise Whisper (OpenAI) pour transcrire l'audio en texte.

Formats supportés: MP4, MKV, AVI, MOV, WAV, MP3, etc.
Langues: Détection automatique ou spécifiée

Auteur: Agent IA Copilot
Date: Décembre 2025
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import whisper


def get_ffmpeg_path():
    """Trouve le chemin de ffmpeg."""
    conda_env = Path(r"c:\Users\nichi\Documents\HERMANN\Projet_audio\.conda")
    ffmpeg_conda = conda_env / "Library" / "bin" / "ffmpeg.exe"
    
    if ffmpeg_conda.exists():
        return str(ffmpeg_conda)
    
    result = shutil.which("ffmpeg")
    if result:
        return result
    
    return "ffmpeg"


def transcribe_media(input_file, language=None, model_size="base", output_formats=["txt", "srt"]):
    """
    Transcrit l'audio d'un fichier vidéo ou audio.
    
    Args:
        input_file: Chemin vers le fichier (vidéo ou audio)
        language: Code langue (ex: "fr", "en") ou None pour détection auto
        model_size: Taille du modèle ("tiny", "base", "small", "medium", "large")
        output_formats: Formats de sortie ["txt", "srt", "vtt", "json"]
    
    Returns:
        Dictionnaire avec les chemins des fichiers générés
    """
    print("\n" + "="*60)
    print("📝 TRANSCRIPTION - WHISPER (OpenAI)")
    print("="*60)
    
    if not os.path.exists(input_file):
        print(f"❌ Fichier introuvable: {input_file}")
        return None
    
    input_path = Path(input_file)
    print(f"📂 Fichier source: {input_file}")
    print(f"🧠 Modèle Whisper: {model_size}")
    print(f"🌍 Langue: {language if language else 'Détection automatique'}")
    
    ffmpeg = get_ffmpeg_path()
    temp_dir = tempfile.mkdtemp(prefix="whisper_")
    temp_audio = os.path.join(temp_dir, "audio.wav")
    
    try:
        # === ÉTAPE 1: Extraire/Convertir l'audio ===
        print("\n" + "-"*40)
        print("📌 ÉTAPE 1: Préparation de l'audio")
        print("-"*40)
        
        # Vérifier si c'est une vidéo ou un audio
        video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.m4v', '.flv']
        is_video = input_path.suffix.lower() in video_extensions
        
        if is_video:
            print(f"   🎬 Extraction de l'audio de la vidéo...")
            cmd = [
                ffmpeg, "-i", input_file,
                "-vn", "-acodec", "pcm_s16le",
                "-ar", "16000", "-ac", "1",
                "-y", temp_audio
            ]
            subprocess.run(cmd, capture_output=True, text=True)
        else:
            # Convertir l'audio au format requis par Whisper
            print(f"   🎵 Conversion de l'audio...")
            cmd = [
                ffmpeg, "-i", input_file,
                "-ar", "16000", "-ac", "1",
                "-y", temp_audio
            ]
            subprocess.run(cmd, capture_output=True, text=True)
        
        if not os.path.exists(temp_audio):
            print(f"❌ Échec de la préparation audio")
            return None
        
        print(f"   ✅ Audio préparé")
        
        # === ÉTAPE 2: Charger le modèle Whisper ===
        print("\n" + "-"*40)
        print("📌 ÉTAPE 2: Chargement du modèle Whisper")
        print("-"*40)
        
        print(f"   ⏳ Chargement du modèle '{model_size}'...")
        print(f"   (Premier chargement = téléchargement, peut prendre du temps)")
        model = whisper.load_model(model_size)
        print(f"   ✅ Modèle chargé!")
        
        # === ÉTAPE 3: Transcription ===
        print("\n" + "-"*40)
        print("📌 ÉTAPE 3: Transcription en cours")
        print("-"*40)
        
        print(f"   ⏳ Analyse et transcription...")
        
        # Options de transcription
        options = {
            "fp16": False,  # Désactiver FP16 sur CPU
            "verbose": False
        }
        
        if language:
            options["language"] = language
        
        result = model.transcribe(temp_audio, **options)
        
        detected_lang = result.get("language", "unknown")
        print(f"   ✅ Transcription terminée!")
        print(f"   🌍 Langue détectée: {detected_lang}")
        
        # === ÉTAPE 4: Sauvegarder les résultats ===
        print("\n" + "-"*40)
        print("📌 ÉTAPE 4: Sauvegarde des résultats")
        print("-"*40)
        
        output_files = {}
        base_name = input_path.stem
        
        # Texte brut (.txt)
        if "txt" in output_formats:
            txt_path = str(input_path.parent / f"{base_name}_transcription.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"Transcription de: {input_file}\n")
                f.write(f"Langue: {detected_lang}\n")
                f.write(f"Modèle: Whisper {model_size}\n")
                f.write("="*50 + "\n\n")
                f.write(result["text"])
            output_files["txt"] = txt_path
            print(f"   ✅ {txt_path}")
        
        # Sous-titres SRT (.srt)
        if "srt" in output_formats:
            srt_path = str(input_path.parent / f"{base_name}_subtitles.srt")
            with open(srt_path, "w", encoding="utf-8") as f:
                for i, segment in enumerate(result["segments"], 1):
                    start = format_timestamp_srt(segment["start"])
                    end = format_timestamp_srt(segment["end"])
                    text = segment["text"].strip()
                    f.write(f"{i}\n")
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{text}\n\n")
            output_files["srt"] = srt_path
            print(f"   ✅ {srt_path}")
        
        # Sous-titres VTT (.vtt)
        if "vtt" in output_formats:
            vtt_path = str(input_path.parent / f"{base_name}_subtitles.vtt")
            with open(vtt_path, "w", encoding="utf-8") as f:
                f.write("WEBVTT\n\n")
                for i, segment in enumerate(result["segments"], 1):
                    start = format_timestamp_vtt(segment["start"])
                    end = format_timestamp_vtt(segment["end"])
                    text = segment["text"].strip()
                    f.write(f"{i}\n")
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{text}\n\n")
            output_files["vtt"] = vtt_path
            print(f"   ✅ {vtt_path}")
        
        # === Résumé ===
        print("\n" + "="*60)
        print("✅ TRANSCRIPTION TERMINÉE!")
        print("="*60)
        
        print(f"\n📊 Résumé:")
        print(f"   - Langue: {detected_lang}")
        print(f"   - Segments: {len(result['segments'])}")
        print(f"   - Caractères: {len(result['text'])}")
        
        print(f"\n📝 Texte transcrit (extrait):")
        print("-"*40)
        preview = result["text"][:500]
        if len(result["text"]) > 500:
            preview += "..."
        print(preview)
        print("-"*40)
        
        print(f"\n📁 Fichiers générés:")
        for fmt, path in output_files.items():
            print(f"   - {path}")
        
        return output_files
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


def format_timestamp_srt(seconds):
    """Formate un timestamp pour SRT (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_timestamp_vtt(seconds):
    """Formate un timestamp pour VTT (HH:MM:SS.mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def main():
    print("\n" + "="*60)
    print("📝 TRANSCRIPTION VIDÉO/AUDIO - PROJET HERMANN")
    print("="*60)
    print("\nUtilise Whisper (OpenAI) pour convertir la parole en texte")
    print("\n📋 Modèles disponibles:")
    print("   - tiny   : Très rapide, moins précis")
    print("   - base   : Bon équilibre (recommandé)")
    print("   - small  : Plus précis, plus lent")
    print("   - medium : Très précis, lent")
    print("   - large  : Maximum précision, très lent")
    
    # Transcrire diane_ann
    video_file = "diane_ann.mp4"
    
    if os.path.exists(video_file):
        print(f"\n🎯 Transcription de: {video_file}")
        transcribe_media(
            video_file,
            language=None,  # Détection automatique
            model_size="medium",  # Plus précis pour meilleure transcription
            output_formats=["txt", "srt"]
        )
    else:
        print(f"\n⚠️ Fichier {video_file} non trouvé")


if __name__ == "__main__":
    main()
