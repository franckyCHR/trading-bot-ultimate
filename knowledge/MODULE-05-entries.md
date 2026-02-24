# MODULE-05 — CALCUL DES POINTS D'ENTRÉE
# Chaque figure a sa propre formule — aucune approximation
# 📅 Version : 1.0

## PRINCIPE
Le bot affiche TOUJOURS 4 prix exacts :
- ⬆️/⬇️ ENTRÉE  : prix précis de déclenchement
- 🔴 SL          : invalidation de la figure
- 🟠 TP1         : 50% de l'objectif
- 🟢 TP2         : objectif complet

## FORMULES PAR FIGURE

### ETE Bearish
- Entrée  = neckline_price
- SL      = epaule_droite_high + (ATR × 0.5)
- TP1     = neckline − (hauteur × 0.5)
- TP2     = neckline − hauteur
- hauteur = tete_high − neckline

### ETE Inversé Bullish
- Entrée  = neckline_price
- SL      = epaule_droite_low − (ATR × 0.5)
- TP1     = neckline + (hauteur × 0.5)
- TP2     = neckline + hauteur

### Double Top
- Entrée  = creux_intermediaire
- SL      = max(top1, top2) + (ATR × 0.5)
- TP1     = entrée − (hauteur × 0.5)
- TP2     = entrée − hauteur

### Double Bottom
- Entrée  = pic_intermediaire
- SL      = min(bot1, bot2) − (ATR × 0.5)
- TP1     = entrée + (hauteur × 0.5)
- TP2     = entrée + hauteur

### Drapeau Haussier
- Entrée  = canal_haut_drapeau
- SL      = canal_bas_drapeau − (ATR × 0.3)
- TP1     = entrée + (hauteur_mât × 0.5)
- TP2     = entrée + hauteur_mât

### Drapeau Baissier
- Entrée  = canal_bas_drapeau
- SL      = canal_haut_drapeau + (ATR × 0.3)
- TP1     = entrée − (hauteur_mât × 0.5)
- TP2     = entrée − hauteur_mât

### Biseau Ascendant (Bearish)
- Entrée  = ligne_support_biseau
- SL      = ligne_resistance_biseau + (ATR × 0.5)
- TP1     = entrée − (largeur_base × 0.5)
- TP2     = entrée − largeur_base

### Biseau Descendant (Bullish)
- Entrée  = ligne_resistance_biseau
- SL      = ligne_support_biseau − (ATR × 0.5)
- TP1     = entrée + (largeur_base × 0.5)
- TP2     = entrée + largeur_base

### Triangle Ascendant
- Entrée  = resistance_horizontale
- SL      = dernier_creux_support − (ATR × 0.3)
- TP1     = entrée + (hauteur × 0.5)
- TP2     = entrée + hauteur

### Triangle Descendant
- Entrée  = support_horizontal
- SL      = dernier_sommet + (ATR × 0.3)
- TP1     = entrée − (hauteur × 0.5)
- TP2     = entrée − hauteur

### Triangle Symétrique
- Attendre cassure puis :
- LONG  : entrée = résistance | SL = support − ATR×0.3 | TP = entrée + base
- SHORT : entrée = support    | SL = résistance + ATR×0.3 | TP = entrée − base

### Butterfly
- Entrée  = point_D (PRZ)
- SL      = D − (XA × 0.15) si LONG | D + (XA × 0.15) si SHORT
- TP1     = retour vers C
- TP2     = retour vers A

### Shark
- Entrée  = point_C
- SL      = C − (XA × 0.10) si LONG | C + (XA × 0.10) si SHORT
- TP1     = retour vers B
- TP2     = retour vers A

### Compression
- Entrée  = cassure haute ou basse de la zone
- SL      = côté opposé − ATR×0.3
- TP1     = entrée ± amplitude × 1
- TP2     = entrée ± amplitude × 2

### Reversal Candle
- Entrée  = close de la bougie signal
- SL      = low − ATR×0.3 (Bullish) | high + ATR×0.3 (Bearish)
- TP1     = RR 1:1
- TP2     = RR 1:2

## ─── TES AJOUTS ────────────────────────────────────
