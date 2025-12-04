#!/usr/bin/env python3
"""
Test complet de génération de Short avec sous-titres MOT PAR MOT.
"""
import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_shorts import extract_short, group_words_for_display
from transcription_engine import get_engine

def test_full_generation():
    """Teste la génération complète avec sous-titres mot par mot."""
    
    # Trouver une vidéo de test
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    video_path = os.path.join(project_root, "com_frat.mp4")
    
    if not os.path.exists(video_path):
        print("❌ Vidéo com_frat.mp4 non trouvée")
        return
    
    # Créer le dossier shorts s'il n'existe pas
    shorts_dir = os.path.join(os.path.dirname(__file__), "shorts")
    os.makedirs(shorts_dir, exist_ok=True)
    
    output_path = os.path.join(shorts_dir, "test_word_sync_final.mp4")
    
    print("🎬 TEST GÉNÉRATION AVEC SOUS-TITRES MOT PAR MOT")
    print("=" * 55)
    print(f"📹 Source: {os.path.basename(video_path)}")
    print(f"📁 Sortie: {os.path.basename(output_path)}")
    print()
    
    # Test du groupement de mots
    print("🔹 Test du groupement de mots (4 mots par groupe):")
    engine = get_engine()
    words = engine.transcribe_video_segment_words(video_path, 0, 5)
    
    if words:
        groups = group_words_for_display(words, words_per_group=4)
        print(f"   {len(words)} mots → {len(groups)} groupes")
        for start, end, text in groups:
            print(f"   [{start:.2f}s - {end:.2f}s] \"{text}\"")
    
    print()
    print("🔹 Génération du Short (5 secondes)...")
    
    # Générer le short
    success = extract_short(
        video_path=video_path,
        start_sec=0,
        end_sec=5,
        output_path=output_path,
        vertical=False,
        add_subtitles=True
    )
    
    print()
    if success and os.path.exists(output_path):
        size_kb = os.path.getsize(output_path) / 1024
        print(f"✅ SHORT GÉNÉRÉ AVEC SUCCÈS!")
        print(f"   📁 Fichier: {output_path}")
        print(f"   📊 Taille: {size_kb:.1f} KB")
        print()
        print("🎯 Ouvrez le fichier pour voir les sous-titres mot par mot!")
    else:
        print("❌ Échec de la génération")


if __name__ == "__main__":
    test_full_generation()
