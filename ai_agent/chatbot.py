"""
Chatbot IA local avec Ollama.
Agent conversationnel capable d'exécuter des actions sur les vidéos.
"""

import os
import sys
import json
import subprocess
import ollama

# ============================================================
# CONFIGURATION
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_NAME = "gpt-oss:120b-cloud"  # Modèle Ollama cloud (rapide)

# Couleurs pour le terminal
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# ============================================================
# OUTILS DISPONIBLES POUR L'IA
# ============================================================

def analyser_video(video_path: str) -> str:
    """Analyse une vidéo pour détecter la voix du Frère Théodore."""
    script_path = os.path.join(BASE_DIR, "detect_theodore.py")
    
    # Chercher la vidéo dans le dossier videos_theodore si pas de chemin absolu
    if not os.path.isabs(video_path):
        video_folder = os.path.join(BASE_DIR, "videos_theodore")
        full_path = os.path.join(video_folder, video_path)
        if os.path.exists(full_path):
            video_path = full_path
    
    if not os.path.exists(video_path):
        return f"Vidéo non trouvée: {video_path}"
    
    try:
        result = subprocess.run(
            [sys.executable, script_path, video_path],
            capture_output=True,
            timeout=600,  # 10 minutes max
            encoding='utf-8',
            errors='replace'
        )
        return (result.stdout or "") + (result.stderr or "")
    except subprocess.TimeoutExpired:
        return "Timeout: L'analyse a pris trop de temps."
    except Exception as e:
        return f"Erreur: {e}"


def generer_shorts(video_path: str) -> str:
    """Génère les shorts à partir des timestamps détectés."""
    script_path = os.path.join(BASE_DIR, "generate_shorts.py")
    
    # Chercher la vidéo dans le dossier videos_theodore si pas de chemin absolu
    if not os.path.isabs(video_path):
        video_folder = os.path.join(BASE_DIR, "videos_theodore")
        full_path = os.path.join(video_folder, video_path)
        if os.path.exists(full_path):
            video_path = full_path
    
    if not os.path.exists(video_path):
        return f"Vidéo non trouvée: {video_path}"
    
    try:
        result = subprocess.run(
            [sys.executable, script_path, video_path],
            capture_output=True,
            timeout=600,
            encoding='utf-8',
            errors='replace'
        )
        return (result.stdout or "") + (result.stderr or "")
    except subprocess.TimeoutExpired:
        return "Timeout: La génération a pris trop de temps."
    except Exception as e:
        return f"Erreur: {e}"


def lister_videos() -> str:
    """Liste les vidéos disponibles dans le dossier videos_theodore."""
    video_folder = os.path.join(BASE_DIR, "videos_theodore")
    
    if not os.path.exists(video_folder):
        return "❌ Dossier videos_theodore non trouvé."
    
    videos = [f for f in os.listdir(video_folder) 
              if f.endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm'))]
    
    if not videos:
        return "📂 Aucune vidéo trouvée dans le dossier videos_theodore."
    
    result = f"📂 {len(videos)} vidéo(s) disponible(s):\n"
    for i, v in enumerate(videos, 1):
        result += f"   {i}. {v}\n"
    return result


def lister_shorts() -> str:
    """Liste les shorts générés."""
    shorts_folder = os.path.join(BASE_DIR, "shorts_theodore")
    
    if not os.path.exists(shorts_folder):
        return "❌ Dossier shorts_theodore non trouvé."
    
    shorts = [f for f in os.listdir(shorts_folder) if f.endswith('.mp4')]
    
    if not shorts:
        return "📂 Aucun short généré pour le moment."
    
    result = f"🎬 {len(shorts)} short(s) généré(s):\n"
    for i, s in enumerate(shorts, 1):
        result += f"   {i}. {s}\n"
    return result


def voir_configuration() -> str:
    """Affiche la configuration actuelle de détection."""
    detect_script = os.path.join(BASE_DIR, "detect_theodore.py")
    
    try:
        with open(detect_script, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraire les paramètres
        result = "⚙️ Configuration actuelle:\n"
        
        for line in content.split('\n'):
            if 'SEGMENT_DURATION_SEC' in line and '=' in line and not line.strip().startswith('#'):
                result += f"   • Durée des segments: {line.split('=')[1].split('#')[0].strip()}s\n"
            elif 'SIMILARITY_THRESHOLD' in line and '=' in line and not line.strip().startswith('#'):
                val = line.split('=')[1].split('#')[0].strip()
                result += f"   • Seuil de similarité: {float(val)*100:.0f}%\n"
            elif 'MIN_CONSECUTIVE_SEGMENTS' in line and '=' in line and not line.strip().startswith('#'):
                result += f"   • Segments consécutifs min: {line.split('=')[1].split('#')[0].strip()}\n"
        
        return result
    except Exception as e:
        return f"❌ Erreur lecture config: {e}"


def analyser_batch() -> str:
    """Analyse toutes les vidéos du dossier en parallèle."""
    script_path = os.path.join(BASE_DIR, "detect_batch.py")
    
    if not os.path.exists(script_path):
        return "Erreur: Script detect_batch.py non trouvé."
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            timeout=3600,  # 1 heure max
            encoding='utf-8',
            errors='replace'
        )
        return (result.stdout or "") + (result.stderr or "")
    except subprocess.TimeoutExpired:
        return "Timeout: L'analyse en batch a pris trop de temps (>1h)."
    except Exception as e:
        return f"Erreur: {e}"


def voir_resultats_batch() -> str:
    """Affiche les derniers résultats d'analyse en batch."""
    results_folder = os.path.join(BASE_DIR, "batch_results")
    
    if not os.path.exists(results_folder):
        return "Aucun résultat de batch disponible. Lancez d'abord une analyse en batch."
    
    # Trouver le fichier le plus récent
    files = [f for f in os.listdir(results_folder) if f.startswith('batch_results_')]
    if not files:
        return "Aucun résultat de batch disponible."
    
    latest_file = sorted(files)[-1]
    file_path = os.path.join(results_folder, latest_file)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Erreur lecture résultats: {e}"


def pipeline_complet(video_path: str) -> str:
    """
    Pipeline COMPLET : Détection de Théodore + Génération de shorts avec sous-titres MOT PAR MOT.
    C'est l'outil principal qui fait tout automatiquement !
    """
    # Import du module de génération
    try:
        sys.path.insert(0, BASE_DIR)
        from generate_shorts import extract_short
    except ImportError as e:
        return f"Erreur import generate_shorts: {e}"
    
    # Chercher la vidéo
    if not os.path.isabs(video_path):
        video_folder = os.path.join(BASE_DIR, "videos_theodore")
        full_path = os.path.join(video_folder, video_path)
        if os.path.exists(full_path):
            video_path = full_path
    
    if not os.path.exists(video_path):
        return f"❌ Vidéo non trouvée: {video_path}"
    
    video_name = os.path.basename(video_path).replace('.mp4', '')
    output_dir = os.path.join(BASE_DIR, "shorts_theodore")
    os.makedirs(output_dir, exist_ok=True)
    
    result_text = []
    result_text.append("🎬 PIPELINE COMPLET - FRÈRE THÉODORE")
    result_text.append("=" * 50)
    result_text.append(f"📹 Vidéo: {os.path.basename(video_path)}")
    result_text.append("")
    
    # Étape 1: Détection de la voix
    result_text.append("📌 ÉTAPE 1: Détection de la voix de Théodore...")
    
    try:
        # Lancer l'analyse via subprocess
        detection_result = subprocess.run(
            [sys.executable, os.path.join(BASE_DIR, "detect_theodore.py"), video_path],
            capture_output=True,
            timeout=600,
            encoding='utf-8',
            errors='replace'
        )
        
        # Parser les timestamps depuis le fichier généré
        timestamps_file = os.path.join(BASE_DIR, "output_segments", "theodore_timestamps.txt")
        
        if not os.path.exists(timestamps_file):
            result_text.append("   ⚠️ Aucun segment détecté (Théodore ne parle pas dans cette vidéo)")
            return "\n".join(result_text)
        
        # Lire les timestamps
        sequences = []
        with open(timestamps_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '→' in line and line[0].isdigit():
                    parts = line.split('→')
                    if len(parts) == 2:
                        start_str = parts[0].split('.')[-1].strip()
                        end_str = parts[1].strip()
                        
                        try:
                            start_parts = start_str.split(':')
                            end_parts = end_str.split(':')
                            
                            start_sec = int(start_parts[0]) * 3600 + int(start_parts[1]) * 60 + int(start_parts[2])
                            end_sec = int(end_parts[0]) * 3600 + int(end_parts[1]) * 60 + int(end_parts[2])
                            
                            sequences.append((start_sec, end_sec))
                        except (ValueError, IndexError):
                            continue
        
        if not sequences:
            result_text.append("   ⚠️ Aucun segment valide trouvé")
            return "\n".join(result_text)
        
        result_text.append(f"   ✅ {len(sequences)} séquence(s) détectée(s)")
        for i, (start, end) in enumerate(sequences, 1):
            result_text.append(f"      {i}. {start//60:02d}:{start%60:02d} → {end//60:02d}:{end%60:02d} ({end-start}s)")
        
    except subprocess.TimeoutExpired:
        result_text.append("   ❌ Timeout lors de la détection")
        return "\n".join(result_text)
    except Exception as e:
        result_text.append(f"   ❌ Erreur: {e}")
        return "\n".join(result_text)
    
    # Étape 2: Génération des shorts avec sous-titres MOT PAR MOT
    result_text.append("")
    result_text.append("📌 ÉTAPE 2: Génération des shorts avec sous-titres MOT PAR MOT...")
    
    shorts_generes = []
    
    for i, (start_sec, end_sec) in enumerate(sequences, 1):
        short_name = f"{video_name}_theodore_{i:02d}.mp4"
        output_path = os.path.join(output_dir, short_name)
        duration = end_sec - start_sec
        
        result_text.append(f"   🎬 Short {i}: {start_sec//60:02d}:{start_sec%60:02d} → {end_sec//60:02d}:{end_sec%60:02d}")
        
        try:
            success = extract_short(
                video_path=video_path,
                start_sec=start_sec,
                end_sec=end_sec,
                output_path=output_path,
                vertical=False,
                add_subtitles=True
            )
            
            if success and os.path.exists(output_path):
                size_kb = os.path.getsize(output_path) / 1024
                result_text.append(f"      ✅ {short_name} ({size_kb:.0f} KB)")
                shorts_generes.append(short_name)
            else:
                result_text.append(f"      ❌ Échec génération")
        except Exception as e:
            result_text.append(f"      ❌ Erreur: {e}")
    
    # Résumé final
    result_text.append("")
    result_text.append("=" * 50)
    result_text.append("📊 RÉSUMÉ")
    result_text.append(f"   ✅ {len(shorts_generes)} short(s) généré(s) dans shorts_theodore/")
    result_text.append("   📝 Sous-titres: MOT PAR MOT synchronisés (style YouTube)")
    
    for s in shorts_generes:
        result_text.append(f"      • {s}")
    
    return "\n".join(result_text)


# Dictionnaire des outils disponibles
OUTILS = {
    "analyser_video": analyser_video,
    "generer_shorts": generer_shorts,
    "lister_videos": lister_videos,
    "lister_shorts": lister_shorts,
    "voir_configuration": voir_configuration,
    "analyser_batch": analyser_batch,
    "voir_resultats_batch": voir_resultats_batch,
    "pipeline_complet": pipeline_complet,
}

# Description des outils pour l'IA
OUTILS_DESCRIPTION = """
Tu es un assistant IA spécialisé dans l'analyse de vidéos pour détecter la voix du Frère Théodore.

Tu as accès aux outils suivants (utilise-les en répondant avec le format JSON approprié):

1. **pipeline_complet** ⭐ OUTIL PRINCIPAL - Fait TOUT automatiquement:
   - Analyse la vidéo pour détecter Théodore
   - Découpe les segments où il parle
   - Génère les shorts avec sous-titres MOT PAR MOT synchronisés (style YouTube/TikTok)
   Paramètre: video_path (nom du fichier vidéo)
   Exemple: {"outil": "pipeline_complet", "params": {"video_path": "test1.mp4"}}
   UTILISE CET OUTIL quand l'utilisateur dit: "fais des shorts", "génère les shorts de Théodore", 
   "découpe la vidéo", "traite cette vidéo", "extrais les passages de Théodore"

2. **analyser_video** - Analyse UNIQUEMENT (sans générer de shorts)
   Paramètre: video_path (nom du fichier vidéo)
   Exemple: {"outil": "analyser_video", "params": {"video_path": "test1.mp4"}}

3. **generer_shorts** - Génère les shorts à partir des timestamps déjà détectés
   Paramètre: video_path (nom du fichier vidéo source)
   Exemple: {"outil": "generer_shorts", "params": {"video_path": "test1.mp4"}}

4. **lister_videos** - Liste les vidéos disponibles dans le dossier
   Pas de paramètres
   Exemple: {"outil": "lister_videos", "params": {}}

5. **lister_shorts** - Liste les shorts déjà générés
   Pas de paramètres
   Exemple: {"outil": "lister_shorts", "params": {}}

6. **voir_configuration** - Affiche les paramètres actuels de détection
   Pas de paramètres
   Exemple: {"outil": "voir_configuration", "params": {}}

7. **analyser_batch** - Analyse TOUTES les vidéos du dossier en parallèle
   Pas de paramètres
   Exemple: {"outil": "analyser_batch", "params": {}}

8. **voir_resultats_batch** - Affiche les derniers résultats d'analyse en batch
   Pas de paramètres
   Exemple: {"outil": "voir_resultats_batch", "params": {}}

IMPORTANT - Fonctionnalités des sous-titres:
- Les shorts ont des sous-titres MOT PAR MOT synchronisés en temps réel
- Chaque groupe de 4 mots apparaît exactement quand il est prononcé
- Style professionnel YouTube/TikTok
- Transcription automatique avec faster-whisper large-v3

Quand l'utilisateur te demande d'effectuer une action, réponds UNIQUEMENT avec le JSON de l'outil.
Pour les conversations normales, réponds normalement en français.
"""

# ============================================================
# CHATBOT
# ============================================================

class Chatbot:
    def __init__(self):
        self.historique = []
        self.model = MODEL_NAME
        
    def extraire_json(self, texte: str) -> dict:
        """Extrait un objet JSON d'une réponse texte."""
        try:
            # Chercher un bloc JSON dans la réponse
            start = texte.find('{')
            end = texte.rfind('}') + 1
            if start != -1 and end > start:
                json_str = texte[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        return None
    
    def executer_outil(self, outil_data: dict) -> str:
        """Exécute un outil et retourne le résultat."""
        nom_outil = outil_data.get("outil")
        params = outil_data.get("params", {})
        
        if nom_outil in OUTILS:
            print(f"\n{Colors.YELLOW}🔧 Exécution de {nom_outil}...{Colors.RESET}")
            try:
                resultat = OUTILS[nom_outil](**params)
                return resultat
            except Exception as e:
                return f"❌ Erreur lors de l'exécution: {e}"
        else:
            return f"❌ Outil inconnu: {nom_outil}"
    
    def chat(self, message: str) -> str:
        """Envoie un message et reçoit une réponse."""
        
        # Ajouter le contexte système au premier message
        if not self.historique:
            self.historique.append({
                "role": "system",
                "content": OUTILS_DESCRIPTION
            })
        
        # Ajouter le message utilisateur
        self.historique.append({
            "role": "user",
            "content": message
        })
        
        try:
            # Appeler Ollama
            response = ollama.chat(
                model=self.model,
                messages=self.historique
            )
            
            reponse_texte = response['message']['content']
            
            # Vérifier si la réponse contient un appel d'outil
            outil_data = self.extraire_json(reponse_texte)
            
            if outil_data and "outil" in outil_data:
                # Exécuter l'outil
                resultat_outil = self.executer_outil(outil_data)
                
                # Ajouter le résultat à l'historique
                self.historique.append({
                    "role": "assistant",
                    "content": reponse_texte
                })
                self.historique.append({
                    "role": "user",
                    "content": f"Résultat de l'outil:\n{resultat_outil}"
                })
                
                # Essayer de demander un résumé, mais ne pas échouer si Ollama a un problème
                try:
                    response2 = ollama.chat(
                        model=self.model,
                        messages=self.historique + [{
                            "role": "user",
                            "content": "Résume ce résultat de manière claire et concise pour l'utilisateur."
                        }]
                    )
                    
                    reponse_finale = response2['message']['content']
                    self.historique.append({
                        "role": "assistant",
                        "content": reponse_finale
                    })
                    
                    return f"{resultat_outil}\n\n{Colors.CYAN}💬 {reponse_finale}{Colors.RESET}"
                except Exception:
                    # Si le résumé échoue, afficher juste le résultat de l'outil
                    return resultat_outil
            else:
                # Réponse normale
                self.historique.append({
                    "role": "assistant",
                    "content": reponse_texte
                })
                return reponse_texte
                
        except Exception as e:
            # Si Ollama échoue complètement, essayer de détecter l'intention et exécuter directement
            message_lower = message.lower()
            
            # Détection d'intention simple pour les commandes courantes
            if any(mot in message_lower for mot in ["short", "génère", "fais", "traite", "découpe", "extrais"]):
                # Extraire le nom de la vidéo
                import re
                match = re.search(r'(test\d+\.mp4|[\w-]+\.mp4)', message)
                if match:
                    video_name = match.group(1)
                    print(f"\n{Colors.YELLOW}🔧 Exécution de pipeline_complet (mode direct)...{Colors.RESET}")
                    return pipeline_complet(video_name)
            
            if "liste" in message_lower and "video" in message_lower:
                return lister_videos()
            
            if "liste" in message_lower and "short" in message_lower:
                return lister_shorts()
            
            if "config" in message_lower:
                return voir_configuration()
            
            return f"❌ Erreur de communication avec Ollama: {e}\nAssurez-vous qu'Ollama est lancé (ollama serve)\n\n💡 Tip: Vous pouvez aussi taper directement:\n   - 'fais des shorts de test1.mp4'\n   - 'liste les videos'\n   - 'liste les shorts'"
    
    def reset(self):
        """Réinitialise l'historique de conversation."""
        self.historique = []
        print(f"{Colors.YELLOW}🔄 Conversation réinitialisée.{Colors.RESET}")


def main():
    """Fonction principale - Interface de chat en terminal."""
    
    print(f"""
{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗
║           🤖 ASSISTANT IA - FRÈRE THÉODORE                   ║
║                                                              ║
║  Je peux analyser des vidéos pour détecter la voix de        ║
║  Théodore et générer automatiquement des shorts.             ║
║                                                              ║
║  Commandes spéciales:                                        ║
║    /quitter  - Quitter le chat                               ║
║    /reset    - Réinitialiser la conversation                 ║
║    /aide     - Afficher l'aide                               ║
╚══════════════════════════════════════════════════════════════╝{Colors.RESET}
""")
    
    bot = Chatbot()
    
    while True:
        try:
            # Prompt utilisateur
            message = input(f"\n{Colors.GREEN}👤 Vous: {Colors.RESET}").strip()
            
            if not message:
                continue
            
            # Commandes spéciales
            if message.lower() == "/quitter":
                print(f"\n{Colors.CYAN}👋 Au revoir!{Colors.RESET}")
                break
            elif message.lower() == "/reset":
                bot.reset()
                continue
            elif message.lower() == "/aide":
                print(f"""
{Colors.YELLOW}📚 Aide - Exemples de questions:{Colors.RESET}
  • "Quelles vidéos sont disponibles ?"
  • "Fais des shorts de test1.mp4" ⭐ (pipeline complet)
  • "Traite la vidéo test2.mp4 et génère les shorts"
  • "Analyse la vidéo test1.mp4" (détection seule)
  • "Montre-moi les shorts générés"
  • "Quelle est la configuration actuelle ?"
  
{Colors.CYAN}💡 Le pipeline complet:{Colors.RESET}
  1. Détecte la voix de Frère Théodore
  2. Découpe les segments où il parle
  3. Génère des shorts avec sous-titres MOT PAR MOT
""")
                continue
            
            # Envoyer au chatbot
            print(f"\n{Colors.CYAN}🤖 Assistant: {Colors.RESET}", end="")
            reponse = bot.chat(message)
            print(reponse)
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.CYAN}👋 Au revoir!{Colors.RESET}")
            break
        except Exception as e:
            print(f"\n{Colors.RED}❌ Erreur: {e}{Colors.RESET}")


if __name__ == "__main__":
    main()
