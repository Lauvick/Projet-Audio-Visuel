"""
Script de génération d'un fichier audio de test avec bruit.
Utilisé pour démonstration si audio_bruit_test1.wav n'est pas disponible.
"""

import numpy as np
from scipy.io import wavfile

def generate_test_audio(filename="audio_bruit_test1.wav", duration=5):
    """
    Génère un fichier audio de test avec signal + bruit large bande.
    
    Args:
        filename: Nom du fichier de sortie
        duration: Durée en secondes
    """
    print(f"🎵 Génération d'un fichier audio de test: {filename}")
    
    # Paramètres
    fs = 48000  # Fréquence d'échantillonnage
    t = np.linspace(0, duration, int(fs * duration))
    
    # Signal propre: combinaison de plusieurs fréquences (voix simulée)
    signal = (
        0.3 * np.sin(2 * np.pi * 220 * t) +      # Fondamentale (La3)
        0.2 * np.sin(2 * np.pi * 440 * t) +      # Harmonique 2 (La4)
        0.15 * np.sin(2 * np.pi * 880 * t) +     # Harmonique 3
        0.1 * np.sin(2 * np.pi * 330 * t)        # Composante intermédiaire
    )
    
    # Bruit large bande (bruit blanc)
    noise_amplitude = 0.4  # Bruit relativement fort
    noise = noise_amplitude * np.random.randn(len(t))
    
    # Ajout de bruit coloré (bruit rose - plus réaliste)
    # Filtrage du bruit blanc pour simuler un bruit environnemental
    from scipy.signal import butter, lfilter
    
    def pink_noise(white_noise):
        """Convertit bruit blanc en bruit rose (1/f)"""
        b, a = butter(1, 0.1, btype='low')
        pink = lfilter(b, a, white_noise)
        return pink / np.max(np.abs(pink)) * noise_amplitude
    
    colored_noise = pink_noise(noise)
    
    # Signal bruité = signal + bruit
    noisy_signal = signal + colored_noise
    
    # Normalisation
    noisy_signal = noisy_signal / np.max(np.abs(noisy_signal)) * 0.8
    
    # Conversion en int16
    noisy_signal_int16 = (noisy_signal * 32767).astype(np.int16)
    
    # Sauvegarde
    wavfile.write(filename, fs, noisy_signal_int16)
    
    print(f"✅ Fichier créé avec succès!")
    print(f"   - Durée: {duration} secondes")
    print(f"   - Fréquence: {fs} Hz")
    print(f"   - SNR approximatif: ~5 dB (bruit significatif)")
    print(f"\n💡 Vous pouvez maintenant exécuter: python denoise_agent.py")

if __name__ == "__main__":
    generate_test_audio()
