#!/usr/bin/env python3
"""
Script pour récupérer la transcription d'une vidéo YouTube
et extraire uniquement les parties en anglais.
"""

from youtube_transcript_api import YouTubeTranscriptApi
import re

def get_video_id(url):
    """Extrait l'ID de la vidéo depuis l'URL YouTube."""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def is_english_text(text):
    """
    Détecte si le texte est principalement en anglais.
    """
    english_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
        'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
        'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above',
        'below', 'between', 'under', 'again', 'further', 'then', 'once',
        'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few',
        'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
        'own', 'same', 'so', 'than', 'too', 'very', 'just', 'and', 'but',
        'if', 'or', 'because', 'until', 'while', 'this', 'that', 'these',
        'those', 'what', 'which', 'who', 'whom', 'i', 'you', 'he', 'she', 'it',
        'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his',
        'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours', 'theirs',
        'god', 'lord', 'jesus', 'christ', 'spirit', 'holy', 'prayer', 'pray',
        'church', 'faith', 'love', 'hope', 'grace', 'blessing', 'amen',
        'people', 'man', 'woman', 'children', 'life', 'world', 'time', 'year',
        'day', 'way', 'thing', 'word', 'work', 'know', 'think', 'see', 'come',
        'want', 'give', 'use', 'find', 'tell', 'ask', 'seem', 'feel', 'try',
        'leave', 'call', 'good', 'new', 'first', 'last', 'long', 'great',
        'little', 'own', 'old', 'right', 'big', 'high', 'different', 'small',
        'large', 'next', 'early', 'young', 'important', 'public', 'bad',
        'same', 'able', 'excellence', 'award', 'thank', 'thanks', 'please',
        'welcome', 'hello', 'yes', 'okay', 'now', 'today', 'tonight', 'morning',
        'evening', 'night', 'minister', 'ministry', 'pastor', 'brother', 'sister'
    }
    
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    if len(words) < 3:
        return False
    
    english_count = sum(1 for word in words if word in english_words)
    ratio = english_count / len(words) if words else 0
    
    return ratio > 0.25

def get_transcript(video_id):
    """Récupère la transcription de la vidéo YouTube."""
    try:
        ytt_api = YouTubeTranscriptApi()
        
        # Lister les transcriptions disponibles
        transcript_list = ytt_api.list(video_id)
        available = list(transcript_list)
        
        print("📋 Sous-titres disponibles:")
        for t in available:
            generated = "[Auto-généré]" if t.is_generated else "[Manuel]"
            print(f"   - {t.language} ({t.language_code}) {generated}")
        print()
        
        # Choisir la transcription
        chosen = None
        for t in available:
            if 'en' in t.language_code.lower():
                chosen = t
                break
        
        if chosen is None and available:
            chosen = available[0]
        
        if chosen:
            print(f"✅ Utilisation des sous-titres: {chosen.language}")
            # Fetch avec l'objet Transcript directement
            fetched = chosen.fetch()
            
            # Convertir en liste de dictionnaires
            result = []
            for snippet in fetched.snippets:
                result.append({
                    'text': snippet.text,
                    'start': snippet.start,
                    'duration': snippet.duration
                })
            return result
        
        return None
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None

def extract_english_parts(transcript):
    """Extrait uniquement les parties en anglais de la transcription."""
    if not transcript:
        return []
    
    # Plages horaires à inclure de force (en secondes)
    # [02:07:10 - 02:09:22] Dr. University of Johannesburg speech continuation
    # 2h07m10s = 7630s
    # 2h09m22s = 7762s
    # [03:03:48 - 03:12:59] Dr. Anne Josianne speech
    # 3h03m48s = 11028s
    # 3h12m59s = 11579s
    # [03:34:50 - 03:40:40] Prof. Dieudonné Njamen (English summary)
    # 3h34m50s = 12890s
    # 3h40m40s = 13240s
    FORCE_INCLUDE_RANGES = [
        (7630, 7762),
        (11028, 11579),
        (12890, 13240)
    ]
    
    english_segments = []
    current_english_block = []
    
    for entry in transcript:
        text = entry['text'].strip()
        start_time = entry['start']
        
        if not text or text in ['[Musique]', '[Music]', '[Applause]', '[Applaudissements]']:
            continue
        
        # Vérifier si on est dans une plage forcée
        is_forced = False
        for start_range, end_range in FORCE_INCLUDE_RANGES:
            if start_range <= start_time <= end_range:
                is_forced = True
                break

        if is_forced or is_english_text(text):
            current_english_block.append({
                'text': text,
                'start': entry['start'],
                'duration': entry.get('duration', 0)
            })
        else:
            if current_english_block:
                english_segments.append(current_english_block)
                current_english_block = []
    
    if current_english_block:
        english_segments.append(current_english_block)
    
    return english_segments

def format_time(seconds):
    """Convertit les secondes en format HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def main():
    video_url = "https://www.youtube.com/watch?v=Fp3WFkqfOB0"
    video_id = get_video_id(video_url)
    
    print("=" * 60)
    print("🎬 EXTRACTION DES PARTIES ANGLAISES - YOUTUBE")
    print("=" * 60)
    print()
    print(f"📹 ID de la vidéo: {video_id}")
    print(f"🔗 URL: {video_url}")
    print()
    
    # Récupérer la transcription
    transcript = get_transcript(video_id)
    
    if not transcript:
        print("❌ Impossible de récupérer la transcription")
        return
    
    print(f"\n📊 Total segments dans la vidéo: {len(transcript)}")

    # Sauvegarder la transcription brute pour analyse
    with open("raw_transcript.txt", "w", encoding="utf-8") as f:
        for entry in transcript:
            start = format_time(entry['start'])
            f.write(f"[{start}] {entry['text']}\n")
    print("💾 Transcription brute sauvegardée dans raw_transcript.txt")
    
    # Extraire les parties anglaises
    english_parts = extract_english_parts(transcript)
    
    print(f"🇬🇧 Blocs en anglais trouvés: {len(english_parts)}")
    print()
    print("=" * 60)
    print("📝 TRANSCRIPTION ANGLAISE")
    print("=" * 60)
    print()
    
    for i, block in enumerate(english_parts, 1):
        if block:
            start_time = format_time(block[0]['start'])
            end_time = format_time(block[-1]['start'] + block[-1]['duration'])
            
            print(f"--- Bloc {i} [{start_time} - {end_time}] ---")
            
            block_text = ' '.join([entry['text'] for entry in block])
            print(block_text)
            print()
    
    # Sauvegarder dans un fichier
    output_file = "youtube_english_transcript.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Transcription anglaise de: {video_url}\n")
        f.write("=" * 60 + "\n\n")
        
        for i, block in enumerate(english_parts, 1):
            if block:
                start_time = format_time(block[0]['start'])
                end_time = format_time(block[-1]['start'] + block[-1]['duration'])
                
                f.write(f"--- Bloc {i} [{start_time} - {end_time}] ---\n")
                block_text = ' '.join([entry['text'] for entry in block])
                f.write(block_text + "\n\n")
    
    print("=" * 60)
    print(f"✅ Transcription sauvegardée dans: {output_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
