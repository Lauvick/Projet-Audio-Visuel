"""
🎤 Script d'Extraction Vocale AMÉLIORÉ - Projet Audio HERMANN
==============================================================
Version améliorée avec soustraction des résidus percussifs.

Auteur: Agent IA Copilot
Date: Décembre 2025
"""

import os
import torch
import numpy as np
import soundfile as sf
from scipy import signal as sig
from pathlib import Path

def extract_vocals_clean(input_file="audio_bruit_test.wav", aggressive=True):
    """
    Extrait les voix avec suppression agressive des résidus percussifs.
    
    Méthode:
    1. Séparation Demucs (vocals vs instruments)
    2. Soustraction spectrale des drums/percussions résiduelles
    3. Filtrage passe-bande pour isoler les fréquences vocales
    """
    print("\n" + "="*60)
    print("🎤 EXTRACTION VOCALE AMÉLIORÉE")
    print("="*60)
    
    if not os.path.exists(input_file):
        print(f"❌ Fichier introuvable: {input_file}")
        return False
    
    print(f"📂 Fichier source: {input_file}")
    print(f"🔧 Mode agressif: {'OUI' if aggressive else 'NON'}")
    
    try:
        from demucs.pretrained import get_model
        from demucs.apply import apply_model
        
        # === ÉTAPE 1: Séparation Demucs ===
        print("\n" + "-"*40)
        print("📌 ÉTAPE 1: Séparation Demucs")
        print("-"*40)
        
        # Essayer le modèle fine-tuné pour une meilleure séparation vocale
        model_name = 'htdemucs_ft' if aggressive else 'htdemucs'
        try:
            print(f"⏳ Chargement du modèle {model_name}...")
            model = get_model(model_name)
        except:
            print(f"⚠️  Modèle {model_name} non disponible, utilisation de htdemucs")
            model = get_model('htdemucs')
        
        model.eval()
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"   Appareil: {device.upper()}")
        model.to(device)
        
        # Charger l'audio
        audio, sr = sf.read(input_file)
        original_sr = sr
        print(f"   - Fréquence: {sr} Hz")
        print(f"   - Durée: {len(audio)/sr:.2f} secondes")
        
        # Convertir en stéréo si mono
        if len(audio.shape) == 1:
            audio = np.stack([audio, audio], axis=1)
        if audio.shape[1] != 2:
            audio = audio[:, :2]
        
        # Rééchantillonner si nécessaire
        target_sr = model.samplerate
        if sr != target_sr:
            print(f"   Rééchantillonnage: {sr} Hz -> {target_sr} Hz")
            num_samples = int(len(audio) * target_sr / sr)
            audio = sig.resample(audio, num_samples)
            sr = target_sr
        
        # Appliquer Demucs
        audio_tensor = torch.tensor(audio.T, dtype=torch.float32).unsqueeze(0).to(device)
        
        print("\n⏳ Séparation en cours...")
        with torch.no_grad():
            sources = apply_model(model, audio_tensor, progress=True)
        
        sources = sources.squeeze(0).cpu().numpy()
        source_names = model.sources  # ['drums', 'bass', 'other', 'vocals']
        
        # Récupérer les sources
        drums_idx = source_names.index('drums')
        vocals_idx = source_names.index('vocals')
        other_idx = source_names.index('other')
        
        vocals = sources[vocals_idx].T  # (samples, channels)
        drums = sources[drums_idx].T
        other = sources[other_idx].T
        
        print(f"✅ Séparation initiale terminée")
        
        # === ÉTAPE 2: Soustraction des résidus percussifs ===
        print("\n" + "-"*40)
        print("📌 ÉTAPE 2: Suppression des résidus percussifs")
        print("-"*40)
        
        # Convertir en mono pour le traitement
        vocals_mono = np.mean(vocals, axis=1)
        drums_mono = np.mean(drums, axis=1)
        
        # STFT pour analyse spectrale
        nperseg = 2048
        noverlap = nperseg * 3 // 4
        
        f, t, vocals_stft = sig.stft(vocals_mono, sr, nperseg=nperseg, noverlap=noverlap)
        _, _, drums_stft = sig.stft(drums_mono, sr, nperseg=nperseg, noverlap=noverlap)
        
        vocals_mag = np.abs(vocals_stft)
        vocals_phase = np.angle(vocals_stft)
        drums_mag = np.abs(drums_stft)
        
        # Soustraction spectrale agressive des résidus de drums
        # On soustrait une version amplifiée du spectre des drums
        subtraction_factor = 2.5 if aggressive else 1.5
        vocals_mag_clean = np.maximum(vocals_mag - subtraction_factor * drums_mag, 0)
        
        print(f"   Facteur de soustraction: {subtraction_factor}x")
        
        # === ÉTAPE 3: Filtrage passe-bande vocal ===
        print("\n" + "-"*40)
        print("📌 ÉTAPE 3: Filtrage fréquentiel vocal")
        print("-"*40)
        
        # Les voix sont principalement entre 80 Hz et 8000 Hz
        # Les maracas/hi-hats sont plutôt > 5000 Hz
        freq_low = 80    # Hz - couper les basses fréquences
        freq_high = 6000 if aggressive else 8000  # Hz - couper les hautes fréquences (maracas)
        
        print(f"   Bande passante: {freq_low} Hz - {freq_high} Hz")
        
        # Créer un masque fréquentiel
        freq_mask = np.ones_like(vocals_mag_clean)
        
        # Atténuer les hautes fréquences (où se trouvent les maracas)
        high_freq_idx = np.where(f > freq_high)[0]
        for idx in high_freq_idx:
            # Atténuation progressive
            attenuation = np.exp(-0.001 * (f[idx] - freq_high))
            freq_mask[idx, :] = attenuation
        
        # Atténuer les très basses fréquences
        low_freq_idx = np.where(f < freq_low)[0]
        for idx in low_freq_idx:
            freq_mask[idx, :] = 0.1
        
        vocals_mag_filtered = vocals_mag_clean * freq_mask
        
        # === ÉTAPE 4: Reconstruction ===
        print("\n" + "-"*40)
        print("📌 ÉTAPE 4: Reconstruction du signal")
        print("-"*40)
        
        # Reconstruire le signal
        vocals_stft_clean = vocals_mag_filtered * np.exp(1j * vocals_phase)
        _, vocals_clean = sig.istft(vocals_stft_clean, sr, nperseg=nperseg, noverlap=noverlap)
        
        # Ajuster la longueur
        target_len = len(vocals_mono)
        if len(vocals_clean) > target_len:
            vocals_clean = vocals_clean[:target_len]
        elif len(vocals_clean) < target_len:
            vocals_clean = np.pad(vocals_clean, (0, target_len - len(vocals_clean)))
        
        # Normalisation
        max_val = np.max(np.abs(vocals_clean))
        if max_val > 0:
            vocals_clean = vocals_clean / max_val * 0.95
        
        # Convertir en stéréo
        vocals_clean_stereo = np.stack([vocals_clean, vocals_clean], axis=1)
        
        # === Sauvegarde ===
        print("\n" + "-"*40)
        print("📌 Sauvegarde des fichiers")
        print("-"*40)
        
        input_name = Path(input_file).stem
        output_dir = Path("separated")
        output_dir.mkdir(exist_ok=True)
        
        # Sauvegarder la version nettoyée
        output_clean = f"vocals_clean_{input_name}.wav"
        sf.write(output_clean, vocals_clean_stereo, sr)
        print(f"   ✅ {output_clean} (vocals nettoyés)")
        
        # Sauvegarder aussi dans separated/
        sf.write(str(output_dir / f"{input_name}_vocals_clean.wav"), vocals_clean_stereo, sr)
        
        print("\n" + "="*60)
        print("✅ EXTRACTION AMÉLIORÉE TERMINÉE!")
        print("="*60)
        print(f"\n🎤 Fichier principal: {output_clean}")
        print("\n📋 Traitements appliqués:")
        print("   1. Séparation Demucs (IA)")
        print("   2. Soustraction spectrale des percussions")
        print(f"   3. Filtrage passe-bande ({freq_low}-{freq_high} Hz)")
        print("   4. Normalisation")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*60)
    print("🎵 EXTRACTION VOCALE AMÉLIORÉE - PROJET HERMANN")
    print("="*60)
    print("\nCette version supprime mieux les résidus de maracas/percussions")
    
    input_file = "audio_bruit_test.wav"
    
    # Mode agressif = meilleure suppression des percussions
    # mais peut légèrement affecter la qualité vocale
    extract_vocals_clean(input_file, aggressive=True)


if __name__ == "__main__":
    main()
