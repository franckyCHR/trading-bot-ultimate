# MODULE-15 — LIGNES DE TENDANCE (3-Touch Validation)
# Source : TrueTL V1.01.mq4

---

## 🎯 CONCEPT

Détection automatique de lignes de tendance basée sur :
- Algorithme fractal pour identifier pivots hauts/bas
- Validation **3 touches** avec tolérance ATR
- Confirmation de niveaux Support/Résistance dynamiques

---

## 📐 ALGORITHME DE DÉTECTION

### Étape 1 — Trouver les Pivots (Fractals)

**Ligne descendante (résistance dynamique) :**
```
Chercher premier HIGH fractal :
   Pour bar de 1 à 50 :
      SI (Fractal_Haut[bar] > 0 ET bar > 2) OU
         (Close[bar+1] > Open[bar+1]  ← bougie haussière
         ET (Close[bar+1]-Low[bar+1]) < 60% du range
         ET Close[bar] < Open[bar])   ← suivi d'une bearish
      ALORS → Point de départ trouvé
```

**Ligne montante (support dynamique) :**
- Même algorithme mais cherchant les LOW fractals
- Bougies baissières suivies de haussières

### Étape 2 — Construire la Ligne

```
De ce point vers l'historique :
   SI la valeur de la ligne au bar actuel < High[bar] ALORS
      → Ajuster le point final au High plus élevé
      → Marquer comme résistance potentielle
```

### Étape 3 — Validation 3 Touches (Confirmation ATR)

```
Pour chaque ligne détectée :

   SI 6 < barsDansRange < min(500, 1000) ALORS
      → Créer une ligne de validation temporaire

      Calculer seuil ATR :
         ATR_threshold = ATR(période) / Point / 10
         validation_width = 8 × ATR_threshold

      Compter les touches dans la tolérance ATR :
         Pour chaque bar dans la plage :
            SI |prix_ligne - prix_bar| <= ATR_threshold ALORS
               touches++
               SI touches >= 3 ALORS
                  → Vérification finale :
                     SI |ligne_originale - ligne_validation| > validation_width ALORS
                        → SUPPRIMER (trop loin)
                     SINON
                        → VALIDER comme ligne "3 touches"
                        → Afficher en BLANC + épaisseur 2
```

---

## 🎨 CODE COULEUR DES LIGNES

| Couleur | Signification |
|---------|---------------|
| ⬜ Blanc épais | **Ligne 3 touches confirmée** — signal fort |
| 🟡 Goldenrod | Ligne ancienne (≥ 500 bougies) = très importante |
| ⬜ Gainsboro | Ligne normale (< 500 bougies) |
| 🔴/🔵 Épaisses | High/Low les plus extrêmes du range |

---

## 📊 RÈGLES DE TRADING AVEC LES TRENDLINES

### Ligne de Tendance Haussière (Support Dynamique)
```
LONG quand :
   ✅ Prix revient tester la ligne haussière
   ✅ Ligne validée 3 touches (blanc)
   ✅ Bougie de reversal bullish sur la ligne
   ✅ Direction conforme à la tendance HTF
```

### Ligne de Tendance Baissière (Résistance Dynamique)
```
SHORT quand :
   ✅ Prix revient tester la ligne baissière
   ✅ Ligne validée 3 touches (blanc)
   ✅ Bougie de reversal bearish sur la ligne
   ✅ Direction conforme à la tendance HTF
```

### Cassure de Ligne de Tendance
```
RUPTURE BULLISH :
   ✅ Prix casse la ligne baissière en clôture
   ✅ Retour en pullback sur la ligne cassée (ex-résistance → support)
   ✅ Entrée sur le test de la ligne cassée

RUPTURE BEARISH :
   ✅ Prix casse la ligne haussière en clôture
   ✅ Retour en pullback sur la ligne cassée (ex-support → résistance)
   ✅ Entrée sur le test de la ligne cassée
```

---

## 🧠 INTÉGRATION DANS LE BOT

La détection de lignes de tendance peut être ajoutée à `PatternDetector` :

**Signal TRENDLINE_BOUNCE** :
- Prix à < ATR distance d'une trendline confirmée
- Pattern reversal candle présent
- Direction alignée avec HTF

**Signal TRENDLINE_BREAK** :
- Clôture au-dessus/dessous d'une trendline forte
- Attente du pullback
- Entrée au retest

**Importance** : Une ligne de tendance **3 touches validée** est équivalente en force à une zone S/R horizontale.
