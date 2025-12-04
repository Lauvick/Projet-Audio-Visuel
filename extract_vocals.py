"""
🎤 Script d'Extraction Vocale - Projet Audio HERMANN
=====================================================
Utilise Demucs (IA de Meta) pour séparer les voix des instruments.

Auteur: Agent IA Copilot
Date: Décembre 2025
"""

import os
import torch
import numpy as np
from scipy.io import wavfile
import soundfile as sf
from pathlib import Path

def extract_vocals(input_file="audio_bruit_test.wav"):
    """
    Extrait les voix d'un fichier audio en utilisant Demucs.
    
    Demucs sépare l'audio en 4 pistes:
    - vocals (voix)
    - drums (batterie/percussions)
    - bass (basse)
    - other (autres instruments)
    """
    print("\n" + "="*60)
    print("🎤 EXTRACTION VOCALE - DEMUCS (Meta AI)")
    print("="*60)
    
    # Vérification du fichier source
    if not os.path.exists(input_file):
        print(f"❌ Fichier introuvable: {input_file}")
        return False
    
    print(f"📂 Fichier source: {input_file}")
    
    try:
        # Import de Demucs
        from demucs.pretrained import get_model
        from demucs.apply import apply_model
        
        print("\n⏳ Chargement du modèle IA htdemucs...")
        
        # Charger le modèle (htdemucs = Hybrid Transformer, meilleure qualité)
        model = get_model('htdemucs')
        model.eval()
        
        # Utiliser GPU si disponible
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"   Appareil: {device.upper()}")
        model.to(device)
        
        # Charger l'audio avec soundfile
        print("\n📂 Chargement de l'audio...")
        audio, sr = sf.read(input_file)
        print(f"   - Fréquence: {sr} Hz")
        print(f"   - Durée: {len(audio)/sr:.2f} secondes")
        print(f"   - Canaux: {audio.shape[1] if len(audio.shape) > 1 else 1}")
        
        # Convertir en stéréo si mono
        if len(audio.shape) == 1:
            audio = np.stack([audio, audio], axis=1)
        
        # S'assurer que c'est en stéréo (2 canaux)
        if audio.shape[1] != 2:
            audio = audio[:, :2]
        
        # Rééchantillonner à 44100 Hz si nécessaire (requis par Demucs)
        target_sr = model.samplerate
        if sr != target_sr:
            print(f"   Rééchantillonnage: {sr} Hz -> {target_sr} Hz")
            from scipy import signal as sig
            num_samples = int(len(audio) * target_sr / sr)
            audio = sig.resample(audio, num_samples)
            sr = target_sr
        
        # Convertir en tensor PyTorch: (batch, channels, samples)
        audio_tensor = torch.tensor(audio.T, dtype=torch.float32).unsqueeze(0)
        audio_tensor = audio_tensor.to(device)
        
        print("\n⏳ Séparation en cours (cela peut prendre quelques minutes)...")
        print("   Le modèle sépare: voix, batterie, basse, autres instruments")
        
        # Appliquer le modèle
        with torch.no_grad():
            sources = apply_model(model, audio_tensor, progress=True)
        
        # sources shape: (batch, n_sources, channels, samples)
        # Sources order: drums, bass, other, vocals
        sources = sources.squeeze(0).cpu().numpy()
        
        source_names = model.sources  # ['drums', 'bass', 'other', 'vocals']
        print(f"\n📋 Sources séparées: {source_names}")
        
        # Sauvegarder chaque source
        input_name = Path(input_file).stem
        output_dir = Path("separated")
        output_dir.mkdir(exist_ok=True)
        
        print("\n💾 Sauvegarde des fichiers...")
        for i, name in enumerate(source_names):
            source_audio = sources[i].T  # (samples, channels)
            output_path = str(output_dir / f"{input_name}_{name}.wav")
            sf.write(output_path, source_audio, sr)
            print(f"   ✅ {output_path}")
        
        # Copier le fichier vocals vers la racine
        vocals_path = str(output_dir / f"{input_name}_vocals.wav")
        final_vocals = f"vocals_{input_name}.wav"
        
        import shutil
        shutil.copy(vocals_path, final_vocals)
        
        print("\n" + "="*60)
        print("✅ EXTRACTION TERMINÉE AVEC SUCCÈS!")
        print("="*60)
        print(f"\n🎤 Fichier vocal principal: {final_vocals}")
        print(f"\n📁 Tous les fichiers dans: {output_dir}/")
        for f in output_dir.glob(f"{input_name}_*.wav"):
            print(f"   - {f.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Point d'entrée principal."""
    print("\n" + "="*60)
    print("🎵 SÉPARATION DE SOURCES AUDIO - PROJET HERMANN")
    print("="*60)
    print("\nCet outil utilise Demucs (Meta AI) pour isoler les voix")
    print("des instruments (batterie, basse, etc.)\n")
    
    # Fichier à traiter
    input_file = "audio_bruit_test.wav"
    
    # Extraction des voix
    success = extract_vocals(input_file)
    
    if success:
        print("\n💡 Conseil: Vous pouvez ensuite appliquer la dénoisation")
        print("   sur le fichier vocal extrait pour un meilleur résultat!")
        print("\n   python denoise_agent.py")


if __name__ == "__main__":
    main()
