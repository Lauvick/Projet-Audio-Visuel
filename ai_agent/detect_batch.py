"""
Script de détection en batch - Analyse plusieurs vidéos en parallèle.
Utilise le multiprocessing pour accélérer le traitement.
"""

import os
import sys
import io
import time
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import timedelta

# Forcer l'encodage UTF-8 pour la console Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuration FFmpeg AVANT import de pydub
CONDA_ENV = os.path.dirname(sys.executable)
FFMPEG_PATH = os.path.join(CONDA_ENV, "Library", "bin", "ffmpeg.exe")
FFPROBE_PATH = os.path.join(CONDA_ENV, "Library", "bin", "ffprobe.exe")

# Ajouter le dossier FFmpeg au PATH
if os.path.exists(os.path.dirname(FFMPEG_PATH)):
    os.environ["PATH"] = os.path.dirname(FFMPEG_PATH) + os.pathsep + os.environ.get("PATH", "")

# ============================================================
# CONFIGURATION
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEOS_FOLDER = os.path.join(BASE_DIR, "videos_theodore")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output_segments")
RESULTS_FOLDER = os.path.join(BASE_DIR, "batch_results")

# Nombre de processus parallèles (ajuster selon votre CPU/RAM)
# 16 Go RAM → 4 workers recommandé
MAX_WORKERS = 4


def format_duration(seconds):
    """Formate une durée en HH:MM:SS"""
    return str(timedelta(seconds=int(seconds)))


def analyze_single_video(video_path):
    """
    Analyse une seule vidéo et retourne les résultats.
    Cette fonction est exécutée dans un processus séparé.
    """
    import torch
    import soundfile as sf
    import numpy as np
    import pydub
    from pydub import AudioSegment
    from speechbrain.inference.classifiers import EncoderClassifier
    from scipy.spatial.distance import cosine
    import warnings
    
    # Supprimer les warnings pour un affichage plus propre
    warnings.filterwarnings('ignore')
    
    # Configurer pydub
    if os.path.exists(FFMPEG_PATH):
        pydub.AudioSegment.converter = FFMPEG_PATH
        pydub.AudioSegment.ffmpeg = FFMPEG_PATH
    if os.path.exists(FFPROBE_PATH):
        pydub.AudioSegment.ffprobe = FFPROBE_PATH
    
    video_name = os.path.basename(video_path)
    result = {
        'video': video_name,
        'status': 'error',
        'segments': [],
        'total_duration': 0,
        'theodore_duration': 0,
        'error': None
    }
    
    try:
        # Paramètres
        VOICE_PRINT_FILE = os.path.join(BASE_DIR, "theodore_voice_print.pt")
        SEGMENT_DURATION_SEC = 3
        SIMILARITY_THRESHOLD = 0.95
        MIN_CONSECUTIVE_SEGMENTS = 1
        
        # Charger l'empreinte vocale
        if not os.path.exists(VOICE_PRINT_FILE):
            result['error'] = "Empreinte vocale non trouvée"
            return result
        
        reference_embedding = torch.load(VOICE_PRINT_FILE, weights_only=True)
        
        # Charger le modèle
        classifier = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-xvect-voxceleb",
            savedir=os.path.join(BASE_DIR, "models_cache"),
            run_opts={"device": "cpu"}
        )
        
        # Convertir la vidéo en audio
        temp_wav = os.path.join(BASE_DIR, "processed_audio", f"temp_{os.getpid()}_{video_name}.wav")
        os.makedirs(os.path.dirname(temp_wav), exist_ok=True)
        
        audio = AudioSegment.from_file(video_path)
        audio = audio.set_channels(1).set_frame_rate(16000)
        audio.export(temp_wav, format="wav")
        
        # Charger l'audio
        signal, sr = sf.read(temp_wav)
        total_duration = len(signal) / sr
        result['total_duration'] = total_duration
        
        # Analyser par segments
        num_segments = int(total_duration / SEGMENT_DURATION_SEC)
        matches = []
        
        for i in range(num_segments):
            start_sample = int(i * SEGMENT_DURATION_SEC * sr)
            end_sample = int((i + 1) * SEGMENT_DURATION_SEC * sr)
            segment = signal[start_sample:end_sample]
            
            if len(segment) < sr:
                continue
            
            # Normaliser
            segment = segment.astype(np.float32)
            max_val = np.max(np.abs(segment))
            if max_val > 0:
                segment = segment / max_val
            
            # Calculer l'embedding
            segment_tensor = torch.tensor(segment).unsqueeze(0)
            embedding = classifier.encode_batch(segment_tensor)
            embedding = embedding.squeeze().detach().numpy()
            
            # Comparer
            similarity = 1 - cosine(reference_embedding.numpy().flatten(), embedding.flatten())
            
            if similarity >= SIMILARITY_THRESHOLD:
                matches.append({
                    'start': i * SEGMENT_DURATION_SEC,
                    'end': (i + 1) * SEGMENT_DURATION_SEC,
                    'similarity': similarity
                })
        
        # Consolider les segments consécutifs
        if matches:
            consolidated = []
            current_start = matches[0]['start']
            current_end = matches[0]['end']
            
            for m in matches[1:]:
                if m['start'] <= current_end:
                    current_end = m['end']
                else:
                    consolidated.append({'start': current_start, 'end': current_end})
                    current_start = m['start']
                    current_end = m['end']
            
            consolidated.append({'start': current_start, 'end': current_end})
            result['segments'] = consolidated
            result['theodore_duration'] = sum(s['end'] - s['start'] for s in consolidated)
        
        result['status'] = 'success'
        
        # Nettoyer le fichier temporaire
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
            
    except Exception as e:
        result['error'] = str(e)
    
    return result


def save_results(results, output_file):
    """Sauvegarde les résultats dans un fichier."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("RÉSULTATS DE L'ANALYSE EN BATCH\n")
        f.write("=" * 70 + "\n\n")
        
        total_videos = len(results)
        success_count = sum(1 for r in results if r['status'] == 'success')
        total_theodore_time = sum(r['theodore_duration'] for r in results)
        
        f.write(f"Vidéos analysées: {total_videos}\n")
        f.write(f"Analyses réussies: {success_count}\n")
        f.write(f"Temps total de Théodore: {format_duration(total_theodore_time)}\n\n")
        
        for r in results:
            f.write("-" * 50 + "\n")
            f.write(f"Vidéo: {r['video']}\n")
            f.write(f"Statut: {r['status']}\n")
            
            if r['status'] == 'success':
                f.write(f"Durée totale: {format_duration(r['total_duration'])}\n")
                f.write(f"Temps de Théodore: {format_duration(r['theodore_duration'])}\n")
                
                if r['segments']:
                    f.write(f"Segments ({len(r['segments'])}):\n")
                    for i, seg in enumerate(r['segments'], 1):
                        f.write(f"  {i}. {format_duration(seg['start'])} -> {format_duration(seg['end'])}\n")
                else:
                    f.write("Aucun segment détecté\n")
            else:
                f.write(f"Erreur: {r['error']}\n")
            f.write("\n")


def main():
    print("\n" + "=" * 70)
    print("🚀 ANALYSE EN BATCH - DÉTECTION DU FRÈRE THÉODORE")
    print("=" * 70)
    
    parser = argparse.ArgumentParser(description='Analyse plusieurs vidéos en parallèle')
    parser.add_argument('videos', nargs='*', help='Chemins des vidéos à analyser')
    parser.add_argument('--folder', '-f', help='Dossier contenant les vidéos')
    parser.add_argument('--workers', '-w', type=int, default=MAX_WORKERS,
                        help=f'Nombre de processus parallèles (défaut: {MAX_WORKERS})')
    args = parser.parse_args()
    
    # Collecter les vidéos à analyser
    video_files = []
    
    if args.videos:
        for v in args.videos:
            if os.path.isabs(v):
                video_files.append(v)
            else:
                # Chercher dans le dossier videos_theodore
                full_path = os.path.join(VIDEOS_FOLDER, v)
                if os.path.exists(full_path):
                    video_files.append(full_path)
                elif os.path.exists(v):
                    video_files.append(os.path.abspath(v))
    
    if args.folder:
        folder = args.folder if os.path.isabs(args.folder) else os.path.join(BASE_DIR, args.folder)
        if os.path.exists(folder):
            for f in os.listdir(folder):
                if f.endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm')):
                    video_files.append(os.path.join(folder, f))
    
    # Si aucune vidéo spécifiée, utiliser toutes les vidéos du dossier videos_theodore
    if not video_files and os.path.exists(VIDEOS_FOLDER):
        for f in os.listdir(VIDEOS_FOLDER):
            if f.endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm')):
                video_files.append(os.path.join(VIDEOS_FOLDER, f))
    
    if not video_files:
        print("\n❌ Aucune vidéo trouvée à analyser.")
        print(f"   Placez vos vidéos dans: {VIDEOS_FOLDER}")
        return
    
    # Supprimer les doublons
    video_files = list(set(video_files))
    
    print(f"\n📂 {len(video_files)} vidéo(s) à analyser:")
    for v in video_files:
        print(f"   • {os.path.basename(v)}")
    
    print(f"\n⚙️  Processus parallèles: {args.workers}")
    print(f"🔄 Démarrage de l'analyse...\n")
    
    # Créer le dossier de résultats
    os.makedirs(RESULTS_FOLDER, exist_ok=True)
    
    # Lancer l'analyse en parallèle
    start_time = time.time()
    results = []
    
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        # Soumettre toutes les tâches
        future_to_video = {
            executor.submit(analyze_single_video, video): video 
            for video in video_files
        }
        
        # Récupérer les résultats au fur et à mesure
        completed = 0
        for future in as_completed(future_to_video):
            video = future_to_video[future]
            completed += 1
            
            try:
                result = future.result()
                results.append(result)
                
                status_icon = "✅" if result['status'] == 'success' else "❌"
                if result['status'] == 'success':
                    print(f"   [{completed}/{len(video_files)}] {status_icon} {result['video']} "
                          f"- {len(result['segments'])} segment(s), "
                          f"{format_duration(result['theodore_duration'])} de Théodore")
                else:
                    print(f"   [{completed}/{len(video_files)}] {status_icon} {result['video']} "
                          f"- Erreur: {result['error']}")
                    
            except Exception as e:
                print(f"   [{completed}/{len(video_files)}] ❌ {os.path.basename(video)} - Exception: {e}")
                results.append({
                    'video': os.path.basename(video),
                    'status': 'error',
                    'segments': [],
                    'total_duration': 0,
                    'theodore_duration': 0,
                    'error': str(e)
                })
    
    elapsed_time = time.time() - start_time
    
    # Sauvegarder les résultats
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(RESULTS_FOLDER, f"batch_results_{timestamp}.txt")
    save_results(results, results_file)
    
    # Afficher le résumé
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ")
    print("=" * 70)
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    total_theodore_time = sum(r['theodore_duration'] for r in results)
    total_video_time = sum(r['total_duration'] for r in results)
    
    print(f"\n✅ Vidéos analysées: {success_count}/{len(video_files)}")
    print(f"⏱️  Temps d'analyse: {format_duration(elapsed_time)}")
    print(f"🎬 Durée totale des vidéos: {format_duration(total_video_time)}")
    print(f"🎤 Temps total de Théodore: {format_duration(total_theodore_time)}")
    print(f"\n💾 Résultats sauvegardés: {results_file}")
    
    # Afficher les vidéos avec le plus de contenu
    if results:
        sorted_results = sorted(
            [r for r in results if r['status'] == 'success'],
            key=lambda x: x['theodore_duration'],
            reverse=True
        )
        
        if sorted_results:
            print(f"\n🏆 Top vidéos (plus de contenu Théodore):")
            for i, r in enumerate(sorted_results[:5], 1):
                print(f"   {i}. {r['video']} - {format_duration(r['theodore_duration'])}")


if __name__ == "__main__":
    main()
