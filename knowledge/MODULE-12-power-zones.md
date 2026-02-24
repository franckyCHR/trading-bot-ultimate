# MODULE-12 — POWER ZONES (Zones S/R Automatiques)
# Source : CHARLES_PowerZones.mq4

---

## 🎯 CONCEPT

Détecteur automatique de zones Support/Résistance basé sur :
- Détection de fractals (pivots locaux)
- Comptage du nombre de touches
- Niveaux Pivot Points journaliers et hebdomadaires

---

## 🔢 ALGORITHME DE DÉTECTION DES ZONES S/R

### Détection par Fractals

```
Pour chaque bougie i dans lookback (100 bougies) :

   RESISTANCE (Fractal Haut) :
   SI High[i] > High[i-2] ET High[i] > High[i-1]
      ET High[i] > High[i+1] ET High[i] > High[i+2]
   ALORS
      → Fractal HAUT détecté = résistance potentielle
      → Compter les touches dans (niveau ± 50% de l'épaisseur)
      → SI touches >= 3 (ZoneStrength)
         → Dessiner zone résistance à High[i] ± ZoneThickness

   SUPPORT (Fractal Bas) :
   SI Low[i] < Low[i-2] ET Low[i] < Low[i-1]
      ET Low[i] < Low[i+1] ET Low[i] < Low[i+2]
   ALORS
      → Fractal BAS détecté = support potentiel
      → Compter les touches dans (niveau ± 50% de l'épaisseur)
      → SI touches >= 3
         → Dessiner zone support à Low[i] ± ZoneThickness
```

**Paramètres clés :**
- `LookbackBars = 100` bougies analysées
- `ZoneStrength = 3` touches minimum pour valider
- `ZoneThicknessPips = 10` pips d'épaisseur de zone

---

## 📐 CALCUL DES PIVOT POINTS CLASSIQUES

**Basé sur les OHLC de la veille :**
```
P  = (H + L + C) / 3

R1 = 2×P - L          (Résistance 1)
R2 = P + (H - L)      (Résistance 2)
R3 = H + 2×(P - L)    (Résistance 3)

S1 = 2×P - H          (Support 1)
S2 = P - (H - L)      (Support 2)
S3 = L - 2×(H - P)    (Support 3)
```

---

## 🚨 SYSTÈME D'ALERTE

- Alerte si prix à moins de **3 pips** d'un niveau Daily High/Low
- Distance minimum entre 2 alertes = 10 pips (anti-doublon)

---

## 🎨 CODE COULEUR

| Couleur | Signification |
|---------|---------------|
| 🟢 Vert (lignes) | Zones Support |
| 🔴 Rouge (lignes) | Zones Résistance |
| 🔵 Bleu (pointillés) | D1 High/Low |
| 🟠 Orange (plein) | W1 High/Low |
| 🟡 Jaune | Pivot Points |
| Transparent | Rectangles de zones |

---

## 🧠 INTÉGRATION DANS LE BOT

Le bot utilise cette logique dans `SRDetector` :
1. Pivots locaux avec `scipy.signal.argrelextrema(order=5)`
2. Clustering des niveaux à 0.3% de distance
3. Force 1-3 selon le nombre de touches
4. Ajout des Pivot Points journaliers si ShowPivots=True

**Améliorations possibles** :
- Augmenter `order` à 7-10 pour les pivots plus significatifs
- Ajouter les niveaux W1 (hebdomadaires) dans SRDetector
- Implémenter les Pivot Points P/R1/R2/S1/S2 dans IndicatorEngine
