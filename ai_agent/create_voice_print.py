import os
import torch
import torchaudio
import soundfile as sf
from speechbrain.inference.classifiers import EncoderClassifier
from pydub import AudioSegment
import numpy as np

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_FOLDER = os.path.join(BASE_DIR, "audios_theodore")
PROCESSED_FOLDER = os.path.join(BASE_DIR, "processed_audio")
MODEL_SOURCE = "speechbrain/spkrec-xvect-voxceleb"
MODEL_SAVEDIR = os.path.join(BASE_DIR, "pretrained_models/spkrec-xvect-voxceleb")
SAVE_FILE = os.path.join(BASE_DIR, "theodore_voice_print.pt")

def convert_to_wav(source_path, dest_path):
    """Convertit un fichier audio en WAV 16kHz Mono compatible avec SpeechBrain"""
    try:
        audio = AudioSegment.from_file(source_path)
        # Conversion en mono et 16000Hz
        audio = audio.set_channels(1).set_frame_rate(16000)
        audio.export(dest_path, format="wav")
        return True
    except Exception as e:
        print(f"Erreur lors de la conversion de {source_path}: {e}")
        return False

def create_voice_print():
    # 1. Préparation des dossiers
    if not os.path.exists(PROCESSED_FOLDER):
        os.makedirs(PROCESSED_FOLDER)

    # 2. Chargement du modèle de reconnaissance vocale
    print("Chargement du modèle IA (cela peut prendre un moment la première fois)...")
    classifier = EncoderClassifier.from_hparams(source=MODEL_SOURCE, savedir=MODEL_SAVEDIR)

    embeddings_list = []

    # 3. Traitement des fichiers
    files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.m4a', '.mp3', '.opus', '.wav'))]
    
    if not files:
        print(f"Aucun fichier audio trouvé dans {SOURCE_FOLDER}")
        return

    print(f"Traitement de {len(files)} fichiers audio pour l'apprentissage...")

    for filename in files:
        source_path = os.path.join(SOURCE_FOLDER, filename)
        wav_filename = os.path.splitext(filename)[0] + ".wav"
        wav_path = os.path.join(PROCESSED_FOLDER, wav_filename)

        # Conversion
        print(f"Conversion de {filename}...")
        if convert_to_wav(source_path, wav_path):
            # Création de l'empreinte (Embedding)
            print(f"Analyse de la voix dans {filename}...")
            # Utilisation de soundfile pour éviter les problèmes de backend torchaudio
            signal_np, fs = sf.read(wav_path)
            signal = torch.from_numpy(signal_np).float()
            
            # Si le signal est (Time,), on le passe en (1, Time) pour SpeechBrain
            if len(signal.shape) == 1:
                signal = signal.unsqueeze(0)
            
            with torch.no_grad():
                embedding = classifier.encode_batch(signal)
                # L'embedding est de forme [1, 1, 192] généralement
                embeddings_list.append(embedding.squeeze().numpy())

    # 4. Création de l'empreinte moyenne (Master Print)
    if embeddings_list:
        # On fait la moyenne de tous les vecteurs pour avoir une signature robuste
        master_embedding = np.mean(embeddings_list, axis=0)
        
        # Sauvegarde
        torch.save(torch.from_numpy(master_embedding), SAVE_FILE)
        print(f"\n✅ SUCCÈS ! L'empreinte vocale du Frère Théodore a été créée.")
        print(f"Sauvegardée dans : {os.path.abspath(SAVE_FILE)}")
        print(f"Basée sur {len(embeddings_list)} fichiers audio.")
    else:
        print("❌ Échec : Impossible de créer l'empreinte vocale.")

if __name__ == "__main__":
    create_voice_print()
