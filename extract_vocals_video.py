"""
🎬 Script d'Extraction Vocale Vidéo - Projet Audio HERMANN
==========================================================
Extrait uniquement les voix d'une vidéo (supprime musique/instruments).

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
import torch
from scipy import signal as sig


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


def extract_vocals_from_video(input_video, output_video=None):
    """
    Extrait uniquement les voix d'une vidéo.
    
    Args:
        input_video: Chemin vers la vidéo source
        output_video: Chemin de sortie (optionnel)
    
    Returns:
        Chemin vers la vidéo avec voix uniquement
    """
    print("\n" + "="*60)
    print("🎬 EXTRACTION VOCALE VIDÉO - PROJET HERMANN")
    print("="*60)
    
    if not os.path.exists(input_video):
        print(f"❌ Fichier introuvable: {input_video}")
        return None
    
    ffmpeg = get_ffmpeg_path()
    print(f"📂 Vidéo source: {input_video}")
    print(f"🔧 FFmpeg: {ffmpeg}")
    
    # Générer le nom de sortie
    input_path = Path(input_video)
    if output_video is None:
        output_video = str(input_path.parent / f"{input_path.stem}_vocals_only{input_path.suffix}")
    
    print(f"📁 Vidéo sortie: {output_video}")
    
    # Dossier temporaire
    temp_dir = tempfile.mkdtemp(prefix="video_vocals_")
    temp_audio = os.path.join(temp_dir, "audio_extracted.wav")
    temp_audio_vocals = os.path.join(temp_dir, "audio_vocals.wav")
    
    try:
        # === ÉTAPE 1: Extraire l'audio ===
        print("\n" + "-"*40)
        print("📌 ÉTAPE 1: Extraction de l'audio")
        print("-"*40)
        
        cmd_extract = [
            ffmpeg, "-i", input_video,
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "44100", "-ac", "2",
            "-y", temp_audio
        ]
        
        print(f"   Extraction en cours...")
        subprocess.run(cmd_extract, capture_output=True, text=True)
        
        if not os.path.exists(temp_audio):
            print(f"❌ Échec de l'extraction audio")
            return None
        
        print(f"   ✅ Audio extrait")
        
        # === ÉTAPE 2: Séparation vocale avec Demucs ===
        print("\n" + "-"*40)
        print("📌 ÉTAPE 2: Séparation vocale (Demucs IA)")
        print("-"*40)
        
        from demucs.pretrained import get_model
        from demucs.apply import apply_model
        
        # Charger le modèle
        print("   ⏳ Chargement du modèle htdemucs_ft...")
        try:
            model = get_model('htdemucs_ft')
        except:
            print("   ⚠️ htdemucs_ft non disponible, utilisation de htdemucs")
            model = get_model('htdemucs')
        
        model.eval()
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"   Appareil: {device.upper()}")
        model.to(device)
        
        # Charger l'audio
        audio, sr = sf.read(temp_audio)
        print(f"   - Fréquence: {sr} Hz")
        print(f"   - Durée: {len(audio)/sr:.2f} secondes")
        
        # Préparer pour Demucs
        if len(audio.shape) == 1:
            audio = np.stack([audio, audio], axis=1)
        
        target_sr = model.samplerate
        if sr != target_sr:
            print(f"   Rééchantillonnage: {sr} Hz -> {target_sr} Hz")
            num_samples = int(len(audio) * target_sr / sr)
            audio = sig.resample(audio, num_samples)
            sr = target_sr
        
        # Appliquer Demucs
        audio_tensor = torch.tensor(audio.T, dtype=torch.float32).unsqueeze(0).to(device)
        
        print("\n   ⏳ Séparation en cours (peut prendre quelques minutes)...")
        with torch.no_grad():
            sources = apply_model(model, audio_tensor, progress=True)
        
        sources = sources.squeeze(0).cpu().numpy()
        source_names = model.sources
        
        # Extraire les voix
        vocals_idx = source_names.index('vocals')
        vocals = sources[vocals_idx].T
        
        print(f"   ✅ Voix extraites!")
        
        # === ÉTAPE 3: Post-traitement des voix ===
        print("\n" + "-"*40)
        print("📌 ÉTAPE 3: Nettoyage des voix")
        print("-"*40)
        
        # Filtrage pour supprimer les résidus d'instruments
        # Appliquer noisereduce sur les voix
        try:
            import noisereduce as nr
            print("   🧠 Application de noisereduce...")
            
            vocals_clean_L = nr.reduce_noise(y=vocals[:, 0], sr=sr, stationary=False, prop_decrease=0.6)
            vocals_clean_R = nr.reduce_noise(y=vocals[:, 1], sr=sr, stationary=False, prop_decrease=0.6)
            vocals_clean = np.stack([vocals_clean_L, vocals_clean_R], axis=1)
        except:
            vocals_clean = vocals
        
        # Normalisation
        max_val = np.max(np.abs(vocals_clean))
        if max_val > 0:
            vocals_clean = vocals_clean / max_val * 0.95
        
        # Sauvegarder
        sf.write(temp_audio_vocals, vocals_clean, sr)
        print(f"   ✅ Audio vocal sauvegardé")
        
        # === ÉTAPE 4: Reconstruire la vidéo ===
        print("\n" + "-"*40)
        print("📌 ÉTAPE 4: Reconstruction de la vidéo")
        print("-"*40)
        
        cmd_merge = [
            ffmpeg,
            "-i", input_video,
            "-i", temp_audio_vocals,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            "-y",
            output_video
        ]
        
        print(f"   Reconstruction en cours...")
        subprocess.run(cmd_merge, capture_output=True, text=True)
        
        if not os.path.exists(output_video):
            print(f"❌ Échec de la reconstruction")
            return None
        
        print(f"   ✅ Vidéo reconstruite!")
        
        # === Résumé ===
        print("\n" + "="*60)
        print("✅ EXTRACTION VOCALE VIDÉO TERMINÉE!")
        print("="*60)
        
        input_size = os.path.getsize(input_video) / 1024 / 1024
        output_size = os.path.getsize(output_video) / 1024 / 1024
        
        print(f"\n📊 Résumé:")
        print(f"   - Vidéo originale: {input_size:.2f} MB")
        print(f"   - Vidéo vocale: {output_size:.2f} MB")
        print(f"\n🎬 Fichier de sortie: {output_video}")
        print(f"\n🎤 Cette vidéo contient UNIQUEMENT les voix!")
        
        return output_video
        
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


def main():
    print("\n" + "="*60)
    print("🎬 EXTRACTION VOCALE VIDÉO - PROJET HERMANN")
    print("="*60)
    print("\nExtrait uniquement les voix d'une vidéo")
    print("(supprime musique, instruments, bruits de fond)")
    
    # Traiter com_frat.mp4
    video_file = "com_frat.mp4"
    
    if os.path.exists(video_file):
        print(f"\n🎯 Traitement de: {video_file}")
        extract_vocals_from_video(video_file)
    else:
        print(f"\n⚠️ Fichier {video_file} non trouvé")


if __name__ == "__main__":
    main()
