"""
Script de détection du Frère Théodore dans une vidéo longue.
Analyse l'audio, compare chaque segment à l'empreinte vocale de référence,
et génère un fichier avec les timestamps où Théodore parle.
"""

import os
import sys
import io

# Forcer l'encodage UTF-8 pour la console Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuration FFmpeg AVANT import de pydub
CONDA_ENV = os.path.dirname(sys.executable)
FFMPEG_PATH = os.path.join(CONDA_ENV, "Library", "bin", "ffmpeg.exe")
FFPROBE_PATH = os.path.join(CONDA_ENV, "Library", "bin", "ffprobe.exe")

# Ajouter le dossier FFmpeg au PATH pour que pydub le trouve
if os.path.exists(os.path.dirname(FFMPEG_PATH)):
    os.environ["PATH"] = os.path.dirname(FFMPEG_PATH) + os.pathsep + os.environ.get("PATH", "")

import torch
import soundfile as sf
import numpy as np
import pydub
from pydub import AudioSegment
from speechbrain.inference.classifiers import EncoderClassifier
from scipy.spatial.distance import cosine

# Configurer explicitement pydub
if os.path.exists(FFMPEG_PATH):
    pydub.AudioSegment.converter = FFMPEG_PATH
    pydub.AudioSegment.ffmpeg = FFMPEG_PATH
if os.path.exists(FFPROBE_PATH):
    pydub.AudioSegment.ffprobe = FFPROBE_PATH

# ============================================================
# CONFIGURATION
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOICE_PRINT_FILE = os.path.join(BASE_DIR, "theodore_voice_print.pt")
PROCESSED_FOLDER = os.path.join(BASE_DIR, "processed_audio")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output_segments")
MODEL_SOURCE = "speechbrain/spkrec-xvect-voxceleb"

# Paramètres de détection
SEGMENT_DURATION_SEC = 3       # Durée de chaque segment à analyser (en secondes)
SIMILARITY_THRESHOLD = 0.95    # Seuil de similarité (0 à 1). Plus c'est haut, plus c'est strict.
MIN_CONSECUTIVE_SEGMENTS = 1   # Nombre minimum de segments consécutifs pour valider une détection
DEBUG_MODE = True              # Afficher les scores de tous les segments pour diagnostic


def convert_to_wav(source_path, dest_path):
    """Convertit un fichier audio/vidéo en WAV 16kHz Mono"""
    try:
        print(f"   Extraction/Conversion audio de : {os.path.basename(source_path)}...")
        audio = AudioSegment.from_file(source_path)
        audio = audio.set_channels(1).set_frame_rate(16000)
        audio.export(dest_path, format="wav")
        return True
    except Exception as e:
        print(f"   Erreur lors de la conversion: {e}")
        return False


def get_embedding(classifier, audio_segment_np):
    """Calcule l'embedding d'un segment audio numpy"""
    signal = torch.from_numpy(audio_segment_np).float()
    if len(signal.shape) == 1:
        signal = signal.unsqueeze(0)
    
    with torch.no_grad():
        embedding = classifier.encode_batch(signal)
    return embedding.squeeze().numpy()


def calculate_similarity(embedding1, embedding2):
    """Calcule la similarité cosinus entre deux embeddings (1 = identique, 0 = différent)"""
    return 1 - cosine(embedding1, embedding2)


def format_time(seconds):
    """Convertit des secondes en format HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def detect_theodore_segments(video_path):
    """
    Fonction principale : Détecte les segments où Théodore parle.
    
    Args:
        video_path: Chemin vers le fichier vidéo/audio à analyser
    
    Returns:
        Liste de tuples (start_time, end_time) en secondes
    """
    
    # 1. Vérifications
    if not os.path.exists(VOICE_PRINT_FILE):
        print("❌ Erreur: L'empreinte vocale de Théodore n'existe pas.")
        print("   Veuillez d'abord exécuter create_voice_print.py")
        return []
    
    if not os.path.exists(video_path):
        print(f"❌ Erreur: Le fichier vidéo n'existe pas: {video_path}")
        return []
    
    # Création des dossiers
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # 2. Chargement de l'empreinte de référence
    print("\n" + "="*60)
    print("🔍 DÉTECTION DU FRÈRE THÉODORE")
    print("="*60)
    print(f"\n📂 Fichier à analyser: {os.path.basename(video_path)}")
    
    print("\n📥 Chargement de l'empreinte vocale de référence...")
    theodore_embedding = torch.load(VOICE_PRINT_FILE, weights_only=True).numpy()
    
    # 3. Chargement du modèle IA
    print("🤖 Chargement du modèle IA...")
    classifier = EncoderClassifier.from_hparams(
        source=MODEL_SOURCE, 
        savedir=os.path.join(BASE_DIR, "pretrained_models/spkrec-xvect-voxceleb")
    )
    
    # 4. Conversion du fichier en WAV
    wav_path = os.path.join(PROCESSED_FOLDER, "temp_analysis.wav")
    if not convert_to_wav(video_path, wav_path):
        return []
    
    # 5. Chargement de l'audio
    print("\n📊 Analyse de l'audio en cours...")
    audio_data, sample_rate = sf.read(wav_path)
    total_duration = len(audio_data) / sample_rate
    print(f"   Durée totale: {format_time(total_duration)}")
    
    segment_samples = int(SEGMENT_DURATION_SEC * sample_rate)
    total_segments = int(len(audio_data) / segment_samples)
    print(f"   Nombre de segments à analyser: {total_segments}")
    
    # 6. Analyse segment par segment
    print("\n🎯 Recherche de la voix de Théodore...")
    detections = []  # Liste des segments détectés (index)
    all_similarities = []  # Pour le diagnostic
    
    for i in range(total_segments):
        start_sample = i * segment_samples
        end_sample = start_sample + segment_samples
        segment = audio_data[start_sample:end_sample]
        
        # Debug : afficher les statistiques du premier segment
        if i == 0 and DEBUG_MODE:
            print(f"   DEBUG - Premier segment: max={np.max(np.abs(segment)):.6f}, mean={np.mean(np.abs(segment)):.6f}")
        
        # Ignorer les segments trop silencieux
        if np.max(np.abs(segment)) < 0.005:
            continue
        
        # Calcul de l'embedding du segment
        try:
            segment_embedding = get_embedding(classifier, segment)
            similarity = calculate_similarity(theodore_embedding, segment_embedding)
            all_similarities.append((i, similarity))
            
            # Mode debug : afficher les premiers calculs
            if DEBUG_MODE and i < 5:
                start_time = i * SEGMENT_DURATION_SEC
                print(f"   DEBUG Segment {i}: {format_time(start_time)} → Similarité: {similarity:.2%}")
            
            # Mode debug : afficher les meilleurs scores
            if DEBUG_MODE and similarity >= 0.30:
                start_time = i * SEGMENT_DURATION_SEC
                status = "✓ MATCH" if similarity >= SIMILARITY_THRESHOLD else "  proche"
                print(f"   {status} à {format_time(start_time)} (similarité: {similarity:.2%})")
            
            if similarity >= SIMILARITY_THRESHOLD:
                detections.append(i)
        except Exception as e:
            if DEBUG_MODE and i < 5:
                print(f"   DEBUG Erreur segment {i}: {e}")
            continue
        
        # Affichage de la progression tous les 10%
        progress = (i + 1) / total_segments * 100
        if (i + 1) % max(1, total_segments // 10) == 0:
            print(f"   Progression: {progress:.0f}%")
    
    # Diagnostic : Afficher les 10 meilleurs scores
    if DEBUG_MODE and all_similarities:
        all_similarities.sort(key=lambda x: x[1], reverse=True)
        print("\n📈 Top 10 des segments les plus similaires:")
        for idx, (seg_idx, sim) in enumerate(all_similarities[:10], 1):
            time_str = format_time(seg_idx * SEGMENT_DURATION_SEC)
            print(f"   {idx}. {time_str} → Similarité: {sim:.2%}")
    
    # 7. Consolidation des segments consécutifs
    print("\n📋 Consolidation des résultats...")
    consolidated_segments = []
    
    if detections:
        current_start = detections[0]
        current_end = detections[0]
        
        for idx in detections[1:]:
            if idx == current_end + 1:
                # Segment consécutif
                current_end = idx
            else:
                # Nouveau groupe
                if (current_end - current_start + 1) >= MIN_CONSECUTIVE_SEGMENTS:
                    start_sec = current_start * SEGMENT_DURATION_SEC
                    end_sec = (current_end + 1) * SEGMENT_DURATION_SEC
                    consolidated_segments.append((start_sec, end_sec))
                current_start = idx
                current_end = idx
        
        # Ajouter le dernier groupe
        if (current_end - current_start + 1) >= MIN_CONSECUTIVE_SEGMENTS:
            start_sec = current_start * SEGMENT_DURATION_SEC
            end_sec = (current_end + 1) * SEGMENT_DURATION_SEC
            consolidated_segments.append((start_sec, end_sec))
    
    # 8. Affichage du résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ")
    print("="*60)
    
    if consolidated_segments:
        total_theodore_time = sum(end - start for start, end in consolidated_segments)
        print(f"\n✅ {len(consolidated_segments)} séquences de Théodore détectées:")
        print(f"   Durée totale: {format_time(total_theodore_time)}")
        print("\n   Détail des séquences:")
        for i, (start, end) in enumerate(consolidated_segments, 1):
            duration = end - start
            print(f"   {i}. {format_time(start)} → {format_time(end)} (durée: {duration:.0f}s)")
        
        # Sauvegarde dans un fichier texte
        output_file = os.path.join(OUTPUT_FOLDER, "theodore_timestamps.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("Séquences où le Frère Théodore parle:\n")
            f.write("="*40 + "\n\n")
            for i, (start, end) in enumerate(consolidated_segments, 1):
                f.write(f"{i}. {format_time(start)} → {format_time(end)}\n")
        print(f"\n💾 Timestamps sauvegardés dans: {output_file}")
    else:
        print("\n⚠️ Aucune séquence de Théodore n'a été détectée.")
        print("   Suggestions:")
        print("   - Vérifiez que le fichier contient bien sa voix")
        print("   - Essayez de diminuer le seuil SIMILARITY_THRESHOLD")
    
    return consolidated_segments


# ============================================================
# POINT D'ENTRÉE
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("="*60)
        print("🎬 DÉTECTEUR DE VOIX - FRÈRE THÉODORE")
        print("="*60)
        print("\nUsage: python detect_theodore.py <chemin_video>")
        print("\nExemple:")
        print('  python detect_theodore.py "C:\\Videos\\culte_dimanche.mp4"')
        print('  python detect_theodore.py "C:\\Videos\\conference.m4a"')
        sys.exit(1)
    
    video_file = sys.argv[1]
    segments = detect_theodore_segments(video_file)
