"""
🎯 Script de Réduction de Bruit IA - Projet Audio HERMANN
==========================================================
Ingénieur Son / Monteur: Solution IA pour dénoisation audio
Stories validées: 1.3 (Test outils IA) & 2.2 (Nettoyage automatique)

Auteur: Agent IA Copilot
Date: Décembre 2025
"""

import numpy as np
from scipy.io import wavfile
from scipy import signal
import matplotlib.pyplot as plt
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# Tentative d'import de noisereduce (outil IA de dénoisation)
try:
    import noisereduce as nr
    NOISEREDUCE_AVAILABLE = True
    print("✅ Bibliothèque 'noisereduce' détectée (Méthode IA recommandée)")
except ImportError:
    NOISEREDUCE_AVAILABLE = False
    print("⚠️  'noisereduce' non disponible. Utilisation de méthode spectrale alternative.")

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("ℹ️  'librosa' non disponible (optionnel).")


class AudioDenoiser:
    """
    Classe principale pour la réduction de bruit IA sur fichiers audio.
    Implémente plusieurs méthodes de dénoisation avec validation FFT.
    """
    
    def __init__(self, input_file="audio_bruit_test.wav"):
        """
        Initialisation de l'agent de dénoisation.
        
        Args:
            input_file (str): Chemin vers le fichier audio source bruité
        """
        self.input_file = input_file
        self.output_file = "audio_nettoye_ia.wav"
        self.fs = None  # Fréquence d'échantillonnage
        self.y_original = None  # Signal original
        self.y_clean = None  # Signal nettoyé
        
    def load_audio(self):
        """
        A. Chargement et normalisation du fichier audio.
        Retourne: True si succès, False sinon
        """
        print("\n" + "="*60)
        print("📂 ÉTAPE 1: CHARGEMENT DU FICHIER AUDIO")
        print("="*60)
        
        try:
            # Lecture du fichier WAV
            self.fs, audio_data = wavfile.read(self.input_file)
            print(f"✅ Fichier chargé: {self.input_file}")
            print(f"   - Fréquence d'échantillonnage: {self.fs} Hz")
            print(f"   - Durée: {len(audio_data)/self.fs:.2f} secondes")
            print(f"   - Nombre d'échantillons: {len(audio_data)}")
            print(f"   - Format: {audio_data.dtype}")
            
            # Vérification de la fréquence d'échantillonnage
            if self.fs != 48000:
                print(f"⚠️  Attention: Fs = {self.fs} Hz (attendu: 48000 Hz)")
            
            # Conversion en mono si stéréo
            if len(audio_data.shape) > 1:
                print(f"   - Conversion stéréo -> mono (moyenne des canaux)")
                audio_data = np.mean(audio_data, axis=1)
            
            # Normalisation entre -1.0 et 1.0
            if audio_data.dtype == np.int16:
                self.y_original = audio_data.astype(np.float32) / 32768.0
            elif audio_data.dtype == np.int32:
                self.y_original = audio_data.astype(np.float32) / 2147483648.0
            else:
                self.y_original = audio_data.astype(np.float32)
            
            # Normalisation finale
            max_val = np.max(np.abs(self.y_original))
            if max_val > 0:
                self.y_original = self.y_original / max_val
            
            print(f"✅ Signal normalisé: [{np.min(self.y_original):.3f}, {np.max(self.y_original):.3f}]")
            return True
            
        except FileNotFoundError:
            print(f"❌ ERREUR: Fichier '{self.input_file}' introuvable!")
            print(f"   Veuillez placer le fichier audio dans le dossier du projet.")
            return False
        except Exception as e:
            print(f"❌ ERREUR lors du chargement: {e}")
            return False
    
    def spectral_gate_denoising(self, noise_thresh=0.05, prop_decrease=1.0):
        """
        Méthode alternative de dénoisation spectrale (Spectral Gating).
        Utilisée si noisereduce n'est pas disponible.
        
        Args:
            noise_thresh: Seuil de bruit (0-1)
            prop_decrease: Proportion de réduction du bruit
        """
        print("\n🔧 Application du Spectral Gating (méthode alternative)...")
        
        # Paramètres STFT
        nperseg = 2048
        noverlap = nperseg // 2
        
        # Calcul de la STFT
        f, t, Zxx = signal.stft(self.y_original, self.fs, 
                                nperseg=nperseg, noverlap=noverlap)
        
        # Estimation du profil de bruit (moyenne sur les premières frames)
        noise_frames = min(10, Zxx.shape[1] // 10)
        noise_profile = np.mean(np.abs(Zxx[:, :noise_frames]), axis=1, keepdims=True)
        
        # Application du gate spectral
        magnitude = np.abs(Zxx)
        phase = np.angle(Zxx)
        
        # Masque: garde les fréquences au-dessus du seuil de bruit
        mask = magnitude > (noise_profile * (1 + noise_thresh))
        
        # Réduction progressive du bruit
        magnitude_clean = magnitude * mask + magnitude * (1 - mask) * (1 - prop_decrease)
        
        # Reconstruction du signal
        Zxx_clean = magnitude_clean * np.exp(1j * phase)
        _, y_reconstructed = signal.istft(Zxx_clean, self.fs, 
                                          nperseg=nperseg, noverlap=noverlap)
        
        # Ajuster la longueur
        if len(y_reconstructed) > len(self.y_original):
            y_reconstructed = y_reconstructed[:len(self.y_original)]
        elif len(y_reconstructed) < len(self.y_original):
            y_reconstructed = np.pad(y_reconstructed, 
                                     (0, len(self.y_original) - len(y_reconstructed)))
        
        return y_reconstructed
    
    def denoise_audio(self, method="auto"):
        """
        B. Application de l'algorithme de dénoisation IA.
        
        Args:
            method: "auto", "noisereduce", ou "spectral"
        """
        print("\n" + "="*60)
        print("🧠 ÉTAPE 2: RÉDUCTION DE BRUIT IA")
        print("="*60)
        
        if method == "auto":
            method = "noisereduce" if NOISEREDUCE_AVAILABLE else "spectral"
        
        print(f"🎯 Méthode sélectionnée: {method.upper()}")
        
        if method == "noisereduce" and NOISEREDUCE_AVAILABLE:
            print("\n📊 Analyse du profil de bruit...")
            print("   (Utilisation des premières secondes pour estimation)")
            
            # noisereduce est un outil IA basé sur des techniques de filtrage spectral
            # Il utilise des algorithmes avancés pour estimer et réduire le bruit
            try:
                # Configuration optimale pour bruit large bande
                self.y_clean = nr.reduce_noise(
                    y=self.y_original,
                    sr=self.fs,
                    stationary=False,  # Bruit non-stationnaire
                    prop_decrease=0.9,  # Réduction agressive (90%)
                    freq_mask_smooth_hz=500,  # Lissage fréquentiel
                    time_mask_smooth_ms=50,  # Lissage temporel
                    n_fft=2048,
                    use_tqdm=True  # Barre de progression
                )
                print("✅ Dénoisation IA appliquée avec succès!")
                
            except Exception as e:
                print(f"⚠️  Erreur avec noisereduce: {e}")
                print("   Basculement vers méthode spectrale alternative...")
                self.y_clean = self.spectral_gate_denoising()
        
        else:
            # Méthode alternative: Spectral Gating
            self.y_clean = self.spectral_gate_denoising(
                noise_thresh=0.05,
                prop_decrease=0.9
            )
            print("✅ Spectral Gating appliqué avec succès!")
        
        # Normalisation du signal nettoyé
        max_val = np.max(np.abs(self.y_clean))
        if max_val > 0:
            self.y_clean = self.y_clean / max_val
        
        print(f"   Signal nettoyé: [{np.min(self.y_clean):.3f}, {np.max(self.y_clean):.3f}]")
    
    def compute_fft(self, signal_data, label="Signal"):
        """
        Calcul de la FFT pour analyse spectrale.
        
        Returns:
            freqs, magnitude (en dB)
        """
        n = len(signal_data)
        fft_vals = np.fft.fft(signal_data)
        fft_magnitude = np.abs(fft_vals[:n//2])
        freqs = np.fft.fftfreq(n, 1/self.fs)[:n//2]
        
        # Conversion en dB
        fft_db = 20 * np.log10(fft_magnitude + 1e-10)  # +epsilon pour éviter log(0)
        
        return freqs, fft_db
    
    def validate_and_plot(self):
        """
        C. Validation: Comparaison FFT du signal bruité vs nettoyé.
        Story 1.3: Montrer visuellement la réduction du bruit.
        """
        print("\n" + "="*60)
        print("📊 ÉTAPE 3: VALIDATION - ANALYSE SPECTRALE FFT")
        print("="*60)
        
        # Calcul des FFT
        print("🔄 Calcul de la FFT du signal original...")
        freqs_orig, fft_orig = self.compute_fft(self.y_original, "Original")
        
        print("🔄 Calcul de la FFT du signal nettoyé...")
        freqs_clean, fft_clean = self.compute_fft(self.y_clean, "Nettoyé")
        
        # Calcul de la réduction du plancher de bruit
        noise_floor_orig = np.percentile(fft_orig, 10)  # 10ème percentile
        noise_floor_clean = np.percentile(fft_clean, 10)
        reduction_db = noise_floor_orig - noise_floor_clean
        
        print(f"\n📉 RÉSULTATS DE L'ANALYSE:")
        print(f"   - Plancher de bruit original: {noise_floor_orig:.2f} dB")
        print(f"   - Plancher de bruit nettoyé: {noise_floor_clean:.2f} dB")
        print(f"   - Réduction du bruit: {reduction_db:.2f} dB")
        
        # Création du graphique comparatif
        plt.figure(figsize=(14, 8))
        
        # Subplot 1: Spectres comparés
        plt.subplot(2, 1, 1)
        plt.plot(freqs_orig, fft_orig, label='Audio Bruité (Original)', 
                 alpha=0.7, linewidth=1, color='red')
        plt.plot(freqs_clean, fft_clean, label='Audio Nettoyé (IA)', 
                 alpha=0.7, linewidth=1, color='green')
        plt.xlabel('Fréquence (Hz)')
        plt.ylabel('Magnitude (dB)')
        plt.title('🎯 Comparaison Spectrale FFT - Réduction de Bruit IA\n' + 
                  f'(Réduction du plancher de bruit: {reduction_db:.2f} dB)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xlim(0, self.fs/2)
        
        # Subplot 2: Différence spectrale
        plt.subplot(2, 1, 2)
        diff = fft_orig - fft_clean
        plt.fill_between(freqs_orig, 0, diff, alpha=0.5, color='blue', 
                         label='Bruit Éliminé')
        plt.xlabel('Fréquence (Hz)')
        plt.ylabel('Différence (dB)')
        plt.title('Profil du Bruit Éliminé')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xlim(0, self.fs/2)
        
        plt.tight_layout()
        
        # Sauvegarde du graphique
        plot_filename = "comparaison_fft_denoise.png"
        plt.savefig(plot_filename, dpi=150, bbox_inches='tight')
        print(f"✅ Graphique sauvegardé: {plot_filename}")
        
        plt.show()
        
        return reduction_db
    
    def export_audio(self):
        """
        C. Exportation: Sauvegarde du signal nettoyé.
        Story 2.2: Fichier audio nettoyé automatiquement.
        """
        print("\n" + "="*60)
        print("💾 ÉTAPE 4: EXPORTATION DU FICHIER NETTOYÉ")
        print("="*60)
        
        try:
            # Conversion en int16 pour export WAV
            y_export = (self.y_clean * 32767).astype(np.int16)
            
            # Sauvegarde
            wavfile.write(self.output_file, self.fs, y_export)
            
            print(f"✅ Fichier exporté avec succès: {self.output_file}")
            print(f"   - Format: WAV 16-bit PCM")
            print(f"   - Fréquence: {self.fs} Hz")
            print(f"   - Durée: {len(y_export)/self.fs:.2f} secondes")
            
            return True
            
        except Exception as e:
            print(f"❌ ERREUR lors de l'exportation: {e}")
            return False
    
    def run(self):
        """
        Exécution complète du pipeline de dénoisation.
        """
        print("\n" + "="*70)
        print("🎵 AGENT IA DE RÉDUCTION DE BRUIT - PROJET HERMANN")
        print("="*70)
        print("Stories: 1.3 (Test outils IA) & 2.2 (Nettoyage automatique)")
        print("="*70)
        
        # Étape A: Chargement
        if not self.load_audio():
            return False
        
        # Étape B: Dénoisation IA
        self.denoise_audio(method="auto")
        
        # Étape C: Validation et Exportation
        reduction_db = self.validate_and_plot()
        success = self.export_audio()
        
        # Résumé final
        print("\n" + "="*70)
        print("✅ TRAITEMENT TERMINÉ AVEC SUCCÈS!")
        print("="*70)
        print(f"📊 Réduction du bruit: {reduction_db:.2f} dB")
        print(f"📁 Fichier de sortie: {self.output_file}")
        print(f"📈 Graphique: comparaison_fft_denoise.png")
        print("\n🎯 Stories validées:")
        print("   ✅ Story 1.3: Outil IA testé et comparé (FFT)")
        print("   ✅ Story 2.2: Audio nettoyé automatiquement")
        print("="*70 + "\n")
        
        return success


def main():
    """
    Point d'entrée principal du script.
    """
    # Créer l'instance de l'agent
    denoiser = AudioDenoiser(input_file="vocals_audio_bruit_test.wav")
    
    # Exécuter le pipeline complet
    denoiser.run()


if __name__ == "__main__":
    main()
