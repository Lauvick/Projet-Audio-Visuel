#!/usr/bin/env python3
"""
Test de la transcription mot par mot pour sous-titres temps réel.
"""
import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transcription_engine import get_engine

def test_word_transcription():
    """Teste la transcription mot par mot."""
    
    # Trouver une vidéo de test
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_videos = [
        os.path.join(project_root, "com_frat.mp4"),
        os.path.join(project_root, "diane_ann.mp4"),
    ]
    
    video_path = None
    for v in test_videos:
        if os.path.exists(v):
            video_path = v
            break
    
    if not video_path:
        print("❌ Aucune vidéo de test trouvée")
        return
    
    print(f"📹 Vidéo de test: {os.path.basename(video_path)}")
    print("=" * 50)
    
    # Test 1: Transcription par phrase (existante)
    print("\n🔹 Test 1: Transcription par PHRASE")
    engine = get_engine()
    phrases = engine.transcribe_video_segment(video_path, 0, 5)
    
    if phrases:
        print(f"   ✅ {len(phrases)} phrase(s):")
        for start, end, text in phrases[:3]:
            print(f"      [{start:.2f}s - {end:.2f}s] {text[:50]}...")
    else:
        print("   ⚠️ Pas de phrases")
    
    # Test 2: Transcription mot par mot (nouvelle)
    print("\n🔹 Test 2: Transcription MOT PAR MOT")
    words = engine.transcribe_video_segment_words(video_path, 0, 5)
    
    if words:
        print(f"   ✅ {len(words)} mot(s) avec timestamps:")
        for start, end, word in words[:10]:
            print(f"      [{start:.3f}s - {end:.3f}s] '{word}'")
        if len(words) > 10:
            print(f"      ... et {len(words) - 10} autres mots")
    else:
        print("   ⚠️ Pas de mots détectés")
        print("   Debug: Vérifions la méthode transcribe_words...")
        
        # Debug supplémentaire
        audio = engine.extract_audio(video_path, 0, 5)
        if audio:
            print(f"   Audio extrait: {audio}")
            result = engine.transcribe_words(audio)
            print(f"   Résultat transcribe_words: {result}")
    
    print("\n" + "=" * 50)
    print("✅ Test terminé!")


if __name__ == "__main__":
    test_word_transcription()
