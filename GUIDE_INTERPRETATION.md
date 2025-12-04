# 📈 Guide d'Interprétation des Résultats FFT

## 🎯 Objectif
Ce guide vous aide à comprendre le graphique `comparaison_fft_denoise.png` généré par le script de dénoisation IA.

---

## 📊 Structure du Graphique

Le graphique est divisé en **2 zones principales**:

### Zone 1 (Haut): Comparaison Spectrale FFT
**Ce que vous voyez**:
- **Courbe ROUGE**: Spectre du signal audio bruité (original)
- **Courbe VERTE**: Spectre du signal audio nettoyé (après IA)

**Ce que ça signifie**:
- L'axe X = Fréquences (0 à 24000 Hz pour audio 48kHz)
- L'axe Y = Magnitude en décibels (dB)
- Plus la valeur est haute = plus cette fréquence est présente

**Comment interpréter**:
✅ **BON SIGNE**: La courbe verte est **en dessous** de la rouge sur les zones de bruit
✅ **BON SIGNE**: Les pics restent similaires (signal préservé)
❌ **ATTENTION**: Si la courbe verte coupe trop le signal (trop de réduction)

### Zone 2 (Bas): Profil du Bruit Éliminé
**Ce que vous voyez**:
- **Zone BLEUE**: Différence entre original et nettoyé

**Ce que ça signifie**:
- Plus la zone bleue est **haute** = plus de bruit éliminé à cette fréquence
- Plus la zone est **uniforme** = bruit large bande (bonne détection)

---

## 🔢 Métriques Importantes

### 1. Plancher de Bruit (Noise Floor)
**Définition**: Niveau de bruit de fond moyen dans l'audio

```
Plancher original: 6.10 dB
Plancher nettoyé:  2.79 dB
```

**Interprétation**:
- Plus le chiffre est **BAS** = moins de bruit
- La différence = **réduction effective**

### 2. Réduction du Bruit
**Formule**: $\Delta_{bruit} = \text{Plancher}_{\text{original}} - \text{Plancher}_{\text{nettoyé}}$

```
Réduction: 3.30 dB
```

**Échelle de référence**:
- **< 1 dB**: Réduction faible (peu audible)
- **1-3 dB**: Réduction modérée (audible)
- **3-6 dB**: Réduction significative (très audible) ⭐ ← NOTRE CAS
- **> 6 dB**: Réduction majeure (risque d'artefacts)

### 3. Conversion dB en Pourcentage
```
3 dB ≈ 41% de réduction en amplitude
6 dB ≈ 50% de réduction en amplitude
10 dB ≈ 68% de réduction en amplitude
```

Donc **3.30 dB ≈ 32% de bruit en moins** 🎉

---

## ✅ Critères de Qualité

### Le graphique est BON si:
1. ✅ La courbe verte est **globalement en dessous** de la rouge
2. ✅ Les **pics de signal** (hautes valeurs) restent similaires
3. ✅ La zone bleue montre une **réduction uniforme** sur le spectre
4. ✅ La réduction est entre **2-6 dB** (sweet spot)

### Le graphique montre un problème si:
1. ❌ Les pics de signal sont **trop réduits** (signal dégradé)
2. ❌ La courbe verte a des **oscillations importantes** (artefacts)
3. ❌ La réduction est **< 1 dB** (inefficace)
4. ❌ La réduction est **> 10 dB** (trop agressive, risque de distorsion)

---

## 🎧 Validation Audio

### Après avoir vu le graphique, ÉCOUTEZ:
1. **Fichier original**: `audio_bruit_test1.wav`
   - Notez le niveau de bruit de fond
   
2. **Fichier nettoyé**: `audio_nettoye_ia.wav`
   - Le bruit est-il réduit?
   - Le signal principal sonne-t-il naturel?
   - Y a-t-il des artefacts audibles?

### Questions à se poser:
- ✅ Le bruit est-il moins gênant?
- ✅ La voix/musique reste-t-elle claire?
- ✅ Y a-t-il des "bulles" ou effets étranges? (artefacts)

---

## 🔧 Ajustements si Nécessaire

### Si la réduction est trop FAIBLE (< 2 dB):
Éditez `denoise_agent.py`, ligne ~160:
```python
prop_decrease=0.95,  # Augmenter (max 1.0)
```

### Si la réduction est trop FORTE (> 6 dB avec artefacts):
```python
prop_decrease=0.7,   # Diminuer (min 0.0)
```

### Si le bruit est très variable:
```python
stationary=False,    # Déjà configuré pour bruit non-stationnaire
```

---

## 📊 Exemple d'Interprétation

### Scénario 1: Réduction Idéale
```
Plancher original: 8.5 dB
Plancher nettoyé:  3.2 dB
Réduction:         5.3 dB ✅
```
**Verdict**: Excellent! Réduction significative sans risque d'artefacts.

### Scénario 2: Réduction Modérée
```
Plancher original: 5.0 dB
Plancher nettoyé:  3.8 dB
Réduction:         1.2 dB ⚠️
```
**Verdict**: Réduction faible. Augmenter `prop_decrease` ou le bruit était déjà léger.

### Scénario 3: Réduction Agressive
```
Plancher original: 12.0 dB
Plancher nettoyé:  1.5 dB
Réduction:         10.5 dB ⚠️
```
**Verdict**: Réduction excessive. Vérifier les artefacts audio. Diminuer `prop_decrease`.

---

## 🎓 Concepts Techniques

### FFT (Fast Fourier Transform)
Transforme le signal **temporel** (amplitude vs temps) en signal **fréquentiel** (magnitude vs fréquence).

**Pourquoi utile?**
- Visualise quelles fréquences sont présentes
- Identifie le bruit large bande
- Valide objectivement la réduction

### Bruit Large Bande
Bruit qui affecte **tout le spectre** de fréquences (comme le bruit blanc, rose, bruit environnemental).

**Contraire**: Bruit à bande étroite (bourdonnement 50Hz, sifflement aigu)

### Décibel (dB)
Échelle **logarithmique** pour mesurer l'amplitude:
- +6 dB = **double** d'amplitude
- -6 dB = **moitié** d'amplitude
- 0 dB = référence

---

## 🚀 Prochaines Étapes

1. **Analysez** le graphique généré
2. **Écoutez** les deux fichiers audio
3. **Ajustez** les paramètres si nécessaire
4. **Réexécutez** le script: `python denoise_agent.py`
5. **Comparez** les nouvelles métriques

---

## 📞 FAQ

**Q: Pourquoi mon graphique montre peu de différence?**
R: Le bruit initial était peut-être faible, ou `prop_decrease` trop bas.

**Q: Comment savoir si c'est assez bon?**
R: Écoutez l'audio! Si ça sonne bien = c'est bon. Le graphique confirme objectivement.

**Q: La réduction est négative, c'est normal?**
R: Non, cela indique un problème. Réexécutez le script.

**Q: Puis-je utiliser ce script pour de la musique?**
R: Oui, mais testez! La musique peut avoir des passages "silence" qui ressemblent à du bruit.

---

*Guide créé pour le Projet HERMANN - Production Audio/Vidéo*  
*Pour questions techniques, consultez README.md ou denoise_agent.py*
