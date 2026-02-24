# 🧠 PROMPT MAÎTRE — BOT DE TRADING ÉVOLUTIF
# Version : 2.2 — DÉTECTION VISUELLE OBLIGATOIRE DE TOUTES LES FIGURES
# Dernière mise à jour : [DATE]
# Auteur : [TON NOM]
#
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMENT UTILISER CE PROMPT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. Colle ce fichier entier dans ton terminal Claude Code
# 2. Pour ajouter une compétence → va dans le MODULE correspondant
# 3. Pour ajouter une formation/vidéo → enregistre-la dans le tableau SOURCES
# 4. Tu peux ajouter des MODULES entiers (Wyckoff, SMC, etc.)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

---

## 🎭 RÔLE DE CLAUDE CODE

Tu es mon assistant expert en trading technique et développement Python/Pine Script/MQL4.
Tu connais toutes mes règles de trading car elles sont dans ce fichier.
Tu codes, tu analyses, et tu évolues avec moi à chaque nouvelle formation que j'intègre.

---

## 🚨 RÈGLES ABSOLUES — AUCUNE EXCEPTION

```
╔══════════════════════════════════════════════════════════════╗
║  RÈGLE N°1 — JAMAIS de signal sans zone S/R identifiée      ║
║  RÈGLE N°2 — JAMAIS de signal sans figure chartiste         ║
║              CLAIREMENT FORMÉE                               ║
║              OU reversal pattern chandelier CONFIRMÉ         ║
║                                                              ║
║  Si une seule règle n'est pas respectée :                    ║
║  → Le bot NE génère PAS de signal                           ║
║  → Aucun point dessiné sur le graphique                     ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 🖼️ RÈGLE VISUELLE ABSOLUE — NON NÉGOCIABLE

```
╔══════════════════════════════════════════════════════════════════╗
║  TOUTES LES FIGURES DÉTECTÉES DOIVENT ÊTRE DESSINÉES            ║
║  VISUELLEMENT SUR LE GRAPHIQUE — SANS EXCEPTION                 ║
║                                                                  ║
║  Une figure non dessinée = une figure non détectée              ║
║  Le trader doit VOIR la figure sans chercher                     ║
║  Si ça ne saute pas aux yeux → le bot ne la dessine PAS         ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 🎨 MODULE VISUEL — CE QUE LE BOT DESSINE POUR CHAQUE FIGURE

### Règle universelle de dessin
Pour chaque figure détectée, le bot dessine TOUJOURS ces 5 éléments :
1. **Le squelette de la figure** (lignes, points, neckline...)
2. **La zone colorée** (rectangle ou polygone sur la figure)
3. **Le label** (nom + direction en haut de la figure)
4. **Les 3 niveaux de prix** (entrée, SL, TP1, TP2) avec lignes horizontales
5. **La flèche d'entrée** au prix exact

---

### 1. ÉPAULE-TÊTE-ÉPAULE (ETE) — Bearish 🔴

```
Ce que tu vois sur le graphique :

         [LABEL : "ETE BEARISH ⬇️"]
    🔵──────🔵──────🔵          ← 3 points (épaules + tête) reliés
    |Ép.G|  |Tête|  |Ép.D|
    |    |  |    |  |    |
    ███████████████████████      ← Rectangle rouge transparent sur la figure
    ━━━━━━━━━━━━━━━━━━━━━━━      ← Neckline (ligne pleine rouge)
                    ⬇️ [ENTRÉE : 42 000]
    - - - - - - - - - - - -      ← SL (ligne rouge tiretée)  ex: 43 200
    ·····················        ← TP1 (ligne orange pointillée) ex: 41 000
    ─────────────────────        ← TP2 (ligne verte pleine) ex: 39 800
```

**Pine Script :**
```pinescript
// Points de la figure
label.new(bar_index[epaule_g], high[epaule_g], "👈 Ép.G", style=label.style_label_down, color=color.blue)
label.new(bar_index[tete],     high[tete],     "👑 Tête", style=label.style_label_down, color=color.red, size=size.large)
label.new(bar_index[epaule_d], high[epaule_d], "Ép.D 👉", style=label.style_label_down, color=color.blue)

// Lignes reliant les 3 sommets
line.new(bar_index[epaule_g], high[epaule_g], bar_index[tete],     high[tete],     color=color.red, width=2)
line.new(bar_index[tete],     high[tete],     bar_index[epaule_d], high[epaule_d], color=color.red, width=2)

// Neckline horizontale
line.new(bar_index[epaule_g], neckline, bar_index + 10, neckline, color=color.red, width=2, style=line.style_dashed)

// Zone colorée
box.new(bar_index[epaule_g], math.max(high[epaule_g], high[tete], high[epaule_d]),
        bar_index[epaule_d], neckline,
        bgcolor=color.new(color.red, 85), border_color=color.red, border_width=1)

// Label principal
label.new(bar_index[tete], high[tete] * 1.002, "ETE BEARISH ⬇️\nEntrée: " + str.tostring(neckline),
          style=label.style_label_down, color=color.red, textcolor=color.white, size=size.large)
```

---

### 2. ETE INVERSÉ — Bullish 🟢

```
    ━━━━━━━━━━━━━━━━━━━━━━━━      ← Neckline
    ███████████████████████       ← Rectangle vert transparent
    |Ép.G|  |Tête|  |Ép.D|
    🔵──────🔵──────🔵           ← 3 creux reliés
                    ⬆️ [ENTRÉE]
    ─────────────────────         ← TP2 vert
    ·····················         ← TP1 orange
    - - - - - - - - - - -         ← SL rouge
```

---

### 3. DOUBLE TOP (M) — Bearish 🔴

```
    [LABEL : "DOUBLE TOP M ⬇️"]
    🔴──────────────🔴            ← Les 2 tops reliés (ligne rouge)
    |   Top 1   |   Top 2   |
    |           |           |
    ████████████████████████      ← Rectangle rouge entre les 2 tops
    ━━━━━━━━━━━━━━━━━━━━━━━       ← Ligne du creux intermédiaire (neckline M)
                    ⬇️ ENTRÉE
```

**Pine Script :**
```pinescript
// Ligne reliant les 2 tops
line.new(bar_index[top1], high[top1], bar_index[top2], high[top2], color=color.red, width=2)

// Creux intermédiaire = neckline
line.new(bar_index[top1], valley, bar_index + 10, valley, color=color.orange, width=2, style=line.style_dashed)

// Zone M colorée
box.new(bar_index[top1], math.max(high[top1], high[top2]),
        bar_index[top2], valley,
        bgcolor=color.new(color.red, 88), border_color=color.red)

label.new(bar_index[top1] + math.round((bar_index[top2]-bar_index[top1])/2),
          math.max(high[top1], high[top2]), "M ⬇️ DOUBLE TOP",
          style=label.style_label_down, color=color.red, textcolor=color.white)
```

---

### 4. DOUBLE BOTTOM (W) — Bullish 🟢

```
    ━━━━━━━━━━━━━━━━━━━━━━━       ← Ligne du pic intermédiaire
    ████████████████████████      ← Rectangle vert
    🔵──────────────🔵            ← Les 2 bottoms reliés
                    ⬆️ ENTRÉE
    [LABEL : "DOUBLE BOTTOM W ⬆️"]
```

---

### 5. DRAPEAU HAUSSIER — Bullish 🟢

```
    [LABEL : "BULL FLAG ⬆️"]
    ║                              ← Mât : rectangle bleu vertical
    ║   /¯¯¯¯¯¯\                  ← Canal du drapeau : 2 lignes parallèles
    ║  /        \                    légèrement inclinées vers le bas
    ║ /          \
    ║/            \___
                    ⬆️ ENTRÉE (cassure haute du canal)
```

**Pine Script :**
```pinescript
// Mât (rectangle bleu)
box.new(bar_index[debut_mat], high[debut_mat], bar_index[fin_mat], low[debut_mat],
        bgcolor=color.new(color.blue, 80), border_color=color.blue)

// Canal du drapeau (2 lignes parallèles)
line.new(bar_index[fin_mat], canal_haut_debut, bar_index, canal_haut_fin,
         color=color.orange, width=2)
line.new(bar_index[fin_mat], canal_bas_debut, bar_index, canal_bas_fin,
         color=color.orange, width=2)

// Zone du drapeau colorée
box.new(bar_index[fin_mat], canal_haut_debut, bar_index, canal_bas_fin,
        bgcolor=color.new(color.orange, 85), border_color=color.orange)

label.new(bar_index, canal_haut_fin, "🚩 BULL FLAG ⬆️",
          style=label.style_label_down, color=color.green, textcolor=color.white)
```

---

### 6. DRAPEAU BAISSIER — Bearish 🔴

```
    ⬇️ ENTRÉE (cassure basse du canal)
    \\___           ← Canal légèrement incliné vers le HAUT
         \¯¯\
          \  \
           \  \_____
    ║               ← Mât baissier (rectangle rouge)
    ║
```

---

### 7. BISEAU ASCENDANT — Bearish 🔴

```
    [LABEL : "BISEAU ASCENDANT ⬇️"]
              /──── Résistance montante (ligne rouge)
          /──/
      /──/  ████████ ← Zone colorée rouge entre les 2 lignes
  /──/──── Support montant (ligne orange)
  ⬇️ ENTRÉE à la cassure du support
```

**Pine Script :**
```pinescript
// Les 2 trendlines convergentes
line.new(bar_index[debut], resistance_debut, bar_index, resistance_fin,
         color=color.red, width=2)
line.new(bar_index[debut], support_debut, bar_index, support_fin,
         color=color.orange, width=2)

// Zone colorée entre les 2 lignes
linefill.new(
    line.new(bar_index[debut], resistance_debut, bar_index, resistance_fin, color=color.red),
    line.new(bar_index[debut], support_debut,    bar_index, support_fin,    color=color.orange),
    color=color.new(color.red, 85)
)
label.new(bar_index, resistance_fin, "📐 BISEAU ASCENDANT ⬇️",
          style=label.style_label_down, color=color.red, textcolor=color.white)
```

---

### 8. BISEAU DESCENDANT — Bullish 🟢

```
    Résistance descendante (ligne rouge) ────\
    ████████████████████ ← Zone colorée verte  \
    Support descendant (ligne orange) ──────────\
    ⬆️ ENTRÉE à la cassure de la résistance
```

---

### 9. TRIANGLE ASCENDANT — Bullish 🟢

```
    [LABEL : "TRIANGLE ASCENDANT ⬆️"]
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━     ← Résistance HORIZONTALE (ligne pleine)
    ███████████████████████████████    ← Zone verte transparente
       /──/──/──/──/──/──/──/──/       ← Support montant (ligne diagonale)
    ⬆️ ENTRÉE à la cassure de la résistance horizontale
```

**Pine Script :**
```pinescript
// Résistance horizontale (ligne plate)
line.new(bar_index[debut], resistance_level, bar_index + 15, resistance_level,
         color=color.green, width=3, style=line.style_solid)

// Support diagonal montant
line.new(bar_index[debut], support_debut, bar_index, support_fin,
         color=color.green, width=2)

// Zone colorée
linefill.new(
    line.new(bar_index[debut], resistance_level, bar_index, resistance_level, color=color.green),
    line.new(bar_index[debut], support_debut,    bar_index, support_fin,      color=color.green),
    color=color.new(color.green, 88)
)
label.new(bar_index[debut] + math.round((bar_index-bar_index[debut])/2),
          resistance_level, "📐 TRIANGLE ASC ⬆️",
          style=label.style_label_down, color=color.green, textcolor=color.white)
```

---

### 10. TRIANGLE DESCENDANT — Bearish 🔴

```
    Résistance descendante ──────────────\
    ████████████████████████████████████  \   ← Zone rouge
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━      ← Support HORIZONTAL (ligne pleine)
    ⬇️ ENTRÉE à la cassure du support horizontal
```

---

### 11. TRIANGLE SYMÉTRIQUE — Neutre 🟡

```
    [LABEL : "TRIANGLE SYM ⚡ ATTENDRE CASSURE"]
    ────────────────────\          ← Résistance descendante
    ████████████████████ \         ← Zone JAUNE transparente
    ────────────────────/          ← Support montant
    ⚡ Flèche double (haut et bas) jusqu'à la cassure
```

---

### 12. FANION (PENNANT) — Continuation

```
    ║            ← Mât (rectangle bleu)
    ║   \    /
    ║    \  /    ← Triangle symétrique serré (zone jaune)
    ║     \/
    ⬆️ ou ⬇️ selon direction du mât
```

---

### 13. 🦋 BUTTERFLY — Harmonique

```
    [LABEL : "🦋 BUTTERFLY BULLISH/BEARISH"]

    X ●
       \
        ● A         ● C
         \         / \
          ● B     /   \
                 /     ● D  ← PRZ (zone rouge/verte)
                            ← ⬆️/⬇️ ENTRÉE

    Lignes : X→A (bleu), A→B (orange), B→C (vert), C→D (violet)
    Chaque ratio Fibonacci affiché sur la ligne (ex: "0.786 AB/XA")
    PRZ = rectangle coloré autour du point D
```

**Pine Script :**
```pinescript
// Les 4 segments du pattern colorés différemment
line.new(bar_index[X], price_X, bar_index[A], price_A, color=color.blue,   width=2)
line.new(bar_index[A], price_A, bar_index[B], price_B, color=color.orange, width=2)
line.new(bar_index[B], price_B, bar_index[C], price_C, color=color.green,  width=2)
line.new(bar_index[C], price_C, bar_index[D], price_D, color=color.purple, width=2)

// Labels des ratios sur chaque segment
label.new(math.round((bar_index[X]+bar_index[A])/2), (price_X+price_A)/2,
          "XA", style=label.style_label_right, color=color.blue, size=size.small)
label.new(math.round((bar_index[A]+bar_index[B])/2), (price_A+price_B)/2,
          "AB\n0.786", style=label.style_label_right, color=color.orange, size=size.small)
label.new(math.round((bar_index[B]+bar_index[C])/2), (price_B+price_C)/2,
          "BC\n0.618", style=label.style_label_right, color=color.green, size=size.small)
label.new(math.round((bar_index[C]+bar_index[D])/2), (price_C+price_D)/2,
          "CD\n1.618", style=label.style_label_right, color=color.purple, size=size.small)

// PRZ = zone d'entrée colorée autour de D
box.new(bar_index[D] - 3, price_D * 1.003, bar_index[D] + 3, price_D * 0.997,
        bgcolor=color.new(color.red, 70), border_color=color.red, border_width=2)

// Label principal
label.new(bar_index[D], price_D, "🦋 BUTTERFLY\n⬆️ PRZ VALIDÉE",
          style=label.style_label_up, color=color.red, textcolor=color.white, size=size.large)
```

---

### 14. 🦈 SHARK — Harmonique

```
    [LABEL : "🦈 SHARK BULLISH/BEARISH"]

    ● O
       \
        \      ● B
         \    / \
          ● A /   \
              /     ● C  ← ENTRÉE (pas de D sur le Shark)
             /
    Lignes : O→X→A→B→C avec ratios affichés
    Zone d'entrée autour de C
```

---

### 15. ZONE DE COMPRESSION

```
    [LABEL : "⚡ COMPRESSION — EXPLOSION IMMINENTE"]

    ┌────────────────────────────────────┐  ← Bord haut (résistance)
    │ | | | | | | | | | | | | | | | |   │  ← Bougies serrées (rectangle JAUNE)
    └────────────────────────────────────┘  ← Bord bas (support)

    ⬆️ Flèche haut si cassure haussière   → prix entrée = haut du rectangle
    ⬇️ Flèche bas si cassure baissière    → prix entrée = bas du rectangle
    TP1 = amplitude du rectangle × 1
    TP2 = amplitude du rectangle × 2
```

**Pine Script :**
```pinescript
// Rectangle de compression (jaune vif)
box.new(bar_index[debut_compression], high_compression,
        bar_index,                    low_compression,
        bgcolor      = color.new(color.yellow, 75),
        border_color = color.yellow,
        border_width = 2)

// Label clignotant
label.new(bar_index, high_compression,
          "⚡ COMPRESSION\n" + str.tostring(nb_bougies) + " bougies",
          style=label.style_label_down, color=color.yellow, textcolor=color.black, size=size.large)
```

---

### 16. CHANDELIERS REVERSAL

```
    Pin Bar haussier :          Bearish Engulfing :
         |                          ┌─┐   Rouge
         |  ← mèche haute petite   │ │
        ┌┤                         ├─┤
        └┤  ← corps petit          │ │
         |                         │ │
         |                         └─┘
         |  ← mèche basse longue
         |

    Le bot dessine un CERCLE coloré autour du chandelier signal
    + flèche directionnelle au prix de clôture
```

**Pine Script :**
```pinescript
// Cercle autour du chandelier reversal
label.new(bar_index, direction == "BULLISH" ? low - atr*0.3 : high + atr*0.3,
          "🔵",   // cercle visuel
          style   = direction == "BULLISH" ? label.style_label_up : label.style_label_down,
          color   = direction == "BULLISH" ? color.green : color.red,
          size    = size.huge)

// Nom du pattern affiché
label.new(bar_index, direction == "BULLISH" ? low - atr*0.8 : high + atr*0.8,
          pattern_name + "\n" + direction,
          style   = label.style_label_center,
          color   = direction == "BULLISH" ? color.new(color.green, 60) : color.new(color.red, 60),
          textcolor = color.white,
          size    = size.normal)
```

---

## 🔧 INSTRUCTIONS POUR LE CODE — visualizer.py

```python
# RÈGLE ABSOLUE dans visualizer.py :
# Chaque figure a sa propre fonction de dessin
# Aucune figure ne peut être retournée sans son code visuel associé

class Visualizer:

    def draw_figure(self, signal) -> dict:
        """
        Retourne TOUJOURS un dict avec :
        - pine_script : str   → code Pine Script complet, prêt à coller
        - mql4_script : str   → code MQL4 complet, prêt à coller
        - elements    : list  → liste de tous les éléments dessinés
        """
        drawers = {
            "ETE"                   : self._draw_head_shoulders,
            "ETE_INVERSE"           : self._draw_inverse_hs,
            "DOUBLE_TOP"            : self._draw_double_top,
            "DOUBLE_BOTTOM"         : self._draw_double_bottom,
            "BULL_FLAG"             : self._draw_bull_flag,
            "BEAR_FLAG"             : self._draw_bear_flag,
            "PENNANT"               : self._draw_pennant,
            "BISEAU_ASCENDANT"      : self._draw_rising_wedge,
            "BISEAU_DESCENDANT"     : self._draw_falling_wedge,
            "TRIANGLE_ASCENDANT"    : self._draw_ascending_triangle,
            "TRIANGLE_DESCENDANT"   : self._draw_descending_triangle,
            "TRIANGLE_SYMETRIQUE"   : self._draw_symmetric_triangle,
            "BUTTERFLY"             : self._draw_butterfly,
            "SHARK"                 : self._draw_shark,
            "COMPRESSION"           : self._draw_compression,
            "PIN_BAR"               : self._draw_reversal_candle,
            "ENGULFING"             : self._draw_reversal_candle,
            "MORNING_STAR"          : self._draw_reversal_candle,
            "EVENING_STAR"          : self._draw_reversal_candle,
            "MARTEAU"               : self._draw_reversal_candle,
            "ETOILE_FILANTE"        : self._draw_reversal_candle,
        }

        if signal.pattern not in drawers:
            raise ValueError(f"Aucun drawer défini pour {signal.pattern}")

        return drawers[signal.pattern](signal)

    # Chaque méthode _draw_xxx retourne le code Pine + MQL4
    # avec les 5 éléments obligatoires :
    # 1. Squelette de la figure
    # 2. Zone colorée
    # 3. Label
    # 4. Lignes ENTRÉE / SL / TP1 / TP2
    # 5. Flèche d'entrée
```

---

```
Le bot doit détecter et afficher sur le graphique :

  ┌──────────────────────────────────────────────┐
  │                                              │
  │   ▲  POINT D'ENTRÉE EXACT (prix précis)      │  ← Le plus important
  │                                              │
  │   ─  STOP LOSS (invalidation de la figure)  │
  │                                              │
  │   ─  TAKE PROFIT 1 (premier objectif)       │
  │   ─  TAKE PROFIT 2 (objectif principal)     │
  │                                              │
  └──────────────────────────────────────────────┘

PAS de notation. PAS de score. PAS de probabilité.
JUSTE les 3 prix à voir clairement sur le graphique.
```

---

## 📐 COMMENT LE BOT CALCULE LE POINT D'ENTRÉE

### Logique d'entrée selon chaque figure

Le point d'entrée n'est PAS aléatoire. Il est calculé précisément selon la figure détectée.

---

### 1. Épaule-Tête-Épaule → Entrée SHORT

```
               Tête
              /    \
  Épaule G  /      \  Épaule D
     /\    /        \    /\
    /  \  /          \  /  \
   /    \/            \/    \
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ← NECKLINE
                                 ← ⬇️ POINT D'ENTRÉE = clôture sous neckline
                                    SL = au-dessus épaule droite
                                    TP1 = 50% de la hauteur tête→neckline
                                    TP2 = 100% de la hauteur tête→neckline
```

**Calcul précis :**
```python
entree    = neckline_price                          # Prix exact de la neckline
stop_loss = epaule_droite_high + (atr * 0.5)       # Au-dessus épaule droite
hauteur   = tete_high - neckline_price              # Amplitude de la figure
tp1       = neckline_price - (hauteur * 0.5)        # 50% de l'objectif
tp2       = neckline_price - hauteur                # 100% de l'objectif
```

---

### 2. Épaule-Tête-Épaule Inversé → Entrée LONG

```python
entree    = neckline_price
stop_loss = epaule_droite_low - (atr * 0.5)
hauteur   = neckline_price - tete_low
tp1       = neckline_price + (hauteur * 0.5)
tp2       = neckline_price + hauteur
```

---

### 3. Double Top → Entrée SHORT

```
    /\      /\
   /  \    /  \
  /    \  /    \
━━━━━━━━\/━━━━━━━  ← CREUX INTERMÉDIAIRE
                   ← ⬇️ POINT D'ENTRÉE = cassure sous creux
```

```python
entree    = creux_intermediaire                     # Prix du creux entre les 2 tops
stop_loss = max(top1, top2) + (atr * 0.5)
hauteur   = max(top1, top2) - creux_intermediaire
tp1       = entree - (hauteur * 0.5)
tp2       = entree - hauteur
```

---

### 4. Double Bottom → Entrée LONG

```python
entree    = pic_intermediaire                       # Prix du pic entre les 2 bottoms
stop_loss = min(bottom1, bottom2) - (atr * 0.5)
hauteur   = pic_intermediaire - min(bottom1, bottom2)
tp1       = entree + (hauteur * 0.5)
tp2       = entree + hauteur
```

---

### 5. Drapeau Haussier → Entrée LONG

```
   |     ← Mât
   |  /¯¯\     ← Drapeau (consolidation)
   | /    \
   |/      \___
                ← ⬇️ POINT D'ENTRÉE = cassure haute du canal du drapeau
```

```python
entree    = canal_haut_drapeau                      # Ligne haute du canal
stop_loss = canal_bas_drapeau - (atr * 0.3)
hauteur_mat = prix_fin_mat - prix_debut_mat
tp1       = entree + (hauteur_mat * 0.5)
tp2       = entree + hauteur_mat
```

---

### 6. Drapeau Baissier → Entrée SHORT

```python
entree    = canal_bas_drapeau
stop_loss = canal_haut_drapeau + (atr * 0.3)
hauteur_mat = prix_debut_mat - prix_fin_mat
tp1       = entree - (hauteur_mat * 0.5)
tp2       = entree - hauteur_mat
```

---

### 7. Biseau Ascendant → Entrée SHORT

```python
entree    = ligne_support_biseau                    # Ligne basse du biseau
stop_loss = ligne_resistance_biseau + (atr * 0.5)  # Au-dessus du biseau
largeur   = debut_biseau_high - debut_biseau_low
tp1       = entree - (largeur * 0.5)
tp2       = entree - largeur                        # Base du biseau
```

---

### 8. Biseau Descendant → Entrée LONG

```python
entree    = ligne_resistance_biseau
stop_loss = ligne_support_biseau - (atr * 0.5)
largeur   = debut_biseau_high - debut_biseau_low
tp1       = entree + (largeur * 0.5)
tp2       = entree + largeur
```

---

### 9. Triangle Ascendant → Entrée LONG

```python
entree    = resistance_horizontale                  # La ligne plate en haut
stop_loss = dernier_creux_support - (atr * 0.3)
hauteur   = resistance_horizontale - premier_creux
tp1       = entree + (hauteur * 0.5)
tp2       = entree + hauteur
```

---

### 10. Triangle Descendant → Entrée SHORT

```python
entree    = support_horizontal
stop_loss = dernier_sommet_resistance + (atr * 0.3)
hauteur   = premier_sommet - support_horizontal
tp1       = entree - (hauteur * 0.5)
tp2       = entree - hauteur
```

---

### 11. Triangle Symétrique → Entrée dans le sens de la cassure

```python
# Attendre la cassure d'un côté
if cassure_haussiere:
    entree    = ligne_resistance_au_moment_cassure
    stop_loss = ligne_support_au_moment_cassure - (atr * 0.3)
    hauteur   = base_triangle_high - base_triangle_low
    tp1       = entree + (hauteur * 0.5)
    tp2       = entree + hauteur
else:
    entree    = ligne_support_au_moment_cassure
    stop_loss = ligne_resistance_au_moment_cassure + (atr * 0.3)
    tp1       = entree - (hauteur * 0.5)
    tp2       = entree - hauteur
```

---

### 12. Reversal Pattern Chandelier sur S/R → Entrée

Quand pas de figure chartiste MAIS chandelier reversal confirmé sur une zone S/R :

```python
# Bullish (Pin Bar, Marteau, Engulf haussier)
entree    = close_bougie_reversal                   # Clôture de la bougie signal
stop_loss = low_bougie_reversal - (atr * 0.3)       # Sous la mèche basse
tp1       = entree + (entree - stop_loss)           # RR 1:1
tp2       = entree + (entree - stop_loss) * 2       # RR 1:2

# Bearish (Pin Bar, Étoile Filante, Engulf baissier)
entree    = close_bougie_reversal
stop_loss = high_bougie_reversal + (atr * 0.3)
tp1       = entree - (stop_loss - entree)
tp2       = entree - (stop_loss - entree) * 2
```

---

## 🖥️ CE QUE LE BOT DESSINE SUR LE GRAPHIQUE

Pour chaque signal valide, le bot génère automatiquement le code Pine Script (TradingView) et MQL4 (MT4) qui trace :

```
Sur le graphique tu verras :

  ┌── Nom de la figure (label) ──────────────────────┐
  │                                                   │
  │  [La figure dessinée : lignes, neckline, etc.]   │
  │                                                   │
  │  ⬆️ ou ⬇️  ← FLÈCHE AU POINT D'ENTRÉE EXACT     │
  │  ─────────── ← Ligne rouge = STOP LOSS           │
  │  ─────────── ← Ligne orange = TP1                │
  │  ─────────── ← Ligne verte = TP2                 │
  └───────────────────────────────────────────────────┘

Chaque ligne affiche son PRIX en étiquette sur la droite.
```

### Pine Script généré (TradingView)
```pinescript
// Flèche d'entrée au prix exact
label.new(bar_index, entry_price,
    text  = "⬇️ SHORT\n" + str.tostring(entry_price),
    style = label.style_label_up,
    color = color.red, textcolor = color.white, size = size.large)

// Ligne Stop Loss
line.new(bar_index - 10, stop_loss, bar_index + 20, stop_loss,
    color = color.red, width = 2, style = line.style_dashed)
label.new(bar_index + 20, stop_loss, "SL " + str.tostring(stop_loss),
    style = label.style_label_left, color = color.red)

// Ligne TP1
line.new(bar_index - 10, tp1, bar_index + 20, tp1,
    color = color.orange, width = 1, style = line.style_dotted)
label.new(bar_index + 20, tp1, "TP1 " + str.tostring(tp1),
    style = label.style_label_left, color = color.orange)

// Ligne TP2
line.new(bar_index - 10, tp2, bar_index + 20, tp2,
    color = color.green, width = 2)
label.new(bar_index + 20, tp2, "TP2 " + str.tostring(tp2),
    style = label.style_label_left, color = color.green)
```

### MQL4 généré (MT4)
```mql4
// Flèche d'entrée
ObjectCreate("Entry", OBJ_ARROW,  0, Time[0], entry_price);
ObjectSet("Entry", OBJPROP_ARROWCODE, direction == "SHORT" ? 234 : 233);
ObjectSet("Entry", OBJPROP_COLOR, direction == "SHORT" ? clrRed : clrGreen);
ObjectSet("Entry", OBJPROP_WIDTH, 3);

// Lignes horizontales avec labels
ObjectCreate("SL_Line", OBJ_HLINE, 0, 0, stop_loss);
ObjectSet("SL_Line", OBJPROP_COLOR, clrRed);
ObjectCreate("SL_Label", OBJ_TEXT, 0, Time[0], stop_loss);
ObjectSetText("SL_Label", "SL : " + DoubleToStr(stop_loss, Digits), 9, "Arial", clrRed);

ObjectCreate("TP1_Line", OBJ_HLINE, 0, 0, tp1);
ObjectSet("TP1_Line", OBJPROP_COLOR, clrOrange);
ObjectCreate("TP1_Label", OBJ_TEXT, 0, Time[0], tp1);
ObjectSetText("TP1_Label", "TP1 : " + DoubleToStr(tp1, Digits), 9, "Arial", clrOrange);

ObjectCreate("TP2_Line", OBJ_HLINE, 0, 0, tp2);
ObjectSet("TP2_Line", OBJPROP_COLOR, clrGreen);
ObjectCreate("TP2_Label", OBJ_TEXT, 0, Time[0], tp2);
ObjectSetText("TP2_Label", "TP2 : " + DoubleToStr(tp2, Digits), 9, "Arial", clrGreen);
```

---

## 📹 SOURCES DE FORMATION INTÉGRÉES

| # | Type    | Source                            | Thème                    | Module         | Date   |
|---|---------|-----------------------------------|--------------------------|----------------|--------|
| 1 | Vidéo   | YouTube (lien à ajouter)          | Figures chartistes       | M-02, M-03     | [DATE] |
| 2 | Ebook   | Psychologie du trader             | Mindset & discipline     | M-06           | [DATE] |
| 3 | [?]     | [à compléter]                     | Harmoniques Butterfly    | M-07           | [DATE] |
| 4 | [?]     | [à compléter]                     | Compression + ADX + QQE  | M-08,M-09,M-10 | [DATE] |
| 5 |         |                                   |                          |                |        |
# ↑ Duplique la ligne 5 pour chaque nouvelle source

---

## 🏗️ ARCHITECTURE DU PROJET

```
trading-bot/
│
├── CLAUDE.md                    ← Résumé des règles maîtres (auto-généré)
│
├── knowledge/
│   ├── MODULE-01-sr.md          ← Support & Résistance
│   ├── MODULE-02-chart.md       ← Figures chartistes + calcul des points
│   ├── MODULE-03-candles.md     ← Chandeliers reversal + calcul des points
│   ├── MODULE-04-indicators.md  ← QQE, RSI, Ichimoku
│   ├── MODULE-05-entries.md     ← Logique de calcul des entrées
│   ├── MODULE-06-psychology.md  ← Psychologie du trader
│   ├── MODULE-07-harmonics.md   ← Butterfly, Shark (ratios Fibonacci)
│   ├── MODULE-08-compression.md ← Zones de compression
│   ├── MODULE-09-adx.md         ← ADX momentum
│   ├── MODULE-10-qqe.md         ← QQE croisement
│   └── [MODULE-XX-xxx.md]       ← Nouveaux modules futurs
│
├── bot/
│   ├── sr_detector.py           ← Détecte les zones S/R
│   ├── pattern_detector.py      ← Détecte les 11 figures chartistes
│   ├── candle_detector.py       ← Détecte les reversal candles
│   ├── harmonic_detector.py     ← Détecte Butterfly + Shark (B, C, D)
│   ├── compression_detector.py  ← Détecte les zones de compression
│   ├── adx_validator.py         ← Valide momentum ADX + DI+/DI-
│   ├── qqe_validator.py         ← Valide croisement QQE
│   ├── gate_checker.py          ← Vérifie toutes les conditions (ordre séquentiel)
│   ├── entry_calculator.py      ← Calcule ENTRÉE / SL / TP1 / TP2
│   ├── visualizer.py            ← Génère Pine Script + MQL4
│   └── scanner.py               ← Scanner principal toutes les 15 min
│
└── outputs/
    ├── tradingview/             ← Scripts .pine prêts à coller
    └── mt4/                     ← Scripts .mql4 prêts à coller
```

---

# ═══════════════════════════════════════════════════════
# MODULE-01 — SUPPORT & RÉSISTANCE
# ═══════════════════════════════════════════════════════

## Définition d'une zone S/R valide
- Touchée minimum 2 fois dans le passé
- Un ancien support cassé devient résistance (et vice-versa)
- Les zones rondes (10 000$, 1.2000€...) sont plus fortes

## Méthode de détection
- Pivots hauts/bas significatifs (argrelextrema, order=7)
- Clusters de bougies (consolidations horizontales)
- Niveaux psychologiques (round numbers)
- Anciens ATH / ATL

## Règle d'entrée
- On n'entre JAMAIS en milieu de range
- Attendre que le prix ARRIVE sur la zone avant de chercher un signal

# ─── TES AJOUTS MODULE-01 ───────────────────────────────
# ────────────────────────────────────────────────────────


# ═══════════════════════════════════════════════════════
# MODULE-02 — FIGURES CHARTISTES
# ═══════════════════════════════════════════════════════

## Règle absolue
- La figure doit être CLAIREMENT VISIBLE et TRAÇABLE
- Si tu hésites à la tracer → elle n'est PAS formée → PAS DE TRADE

## Figures de retournement
- Épaule-Tête-Épaule (Bearish)
- Épaule-Tête-Épaule Inversé (Bullish)
- Double Top / Double Bottom

## Figures de continuation
- Drapeau Haussier / Baissier
- Fanion

## Figures de convergence
- Biseau Ascendant (Bearish)
- Biseau Descendant (Bullish)
- Triangle Ascendant (Bullish)
- Triangle Descendant (Bearish)
- Triangle Symétrique (attendre cassure)

## Points d'entrée → voir section OBJECTIF PRINCIPAL ci-dessus

# ─── TES AJOUTS MODULE-02 ───────────────────────────────
# ────────────────────────────────────────────────────────


# ═══════════════════════════════════════════════════════
# MODULE-03 — CHANDELIERS DE REVERSAL
# ═══════════════════════════════════════════════════════

## Chandeliers Bullish (sur support)
- Pin Bar haussier : mèche basse ≥ 2x le corps
- Marteau : petit corps, longue mèche basse
- Bullish Engulfing : bougie verte englobe la rouge
- Morning Star : Rouge + Doji + Verte
- Harami haussier

## Chandeliers Bearish (sur résistance)
- Pin Bar baissier : mèche haute ≥ 2x le corps
- Étoile Filante : petit corps en bas, longue mèche haute
- Bearish Engulfing : bougie rouge englobe la verte
- Evening Star : Verte + Doji + Rouge
- Harami baissier

## Règle critique
- La bougie doit être CLÔTURÉE (pas en cours)
- Elle doit être SUR la zone S/R, pas à côté
- Points d'entrée → voir section OBJECTIF PRINCIPAL ci-dessus

# ─── TES AJOUTS MODULE-03 ───────────────────────────────
# ────────────────────────────────────────────────────────


# ═══════════════════════════════════════════════════════
# MODULE-04 — INDICATEURS TECHNIQUES
# ═══════════════════════════════════════════════════════

## QQE
- Signal LONG : ligne rapide croise au-dessus de la lente, sous le niveau 50
- Signal SHORT : ligne rapide croise sous la lente, au-dessus du niveau 50

## RSI
- Divergence haussière : prix fait un plus bas, RSI fait un plus haut
- Divergence baissière : prix fait un plus haut, RSI fait un plus bas
- Zones extrêmes : <30 survente / >70 surachat

## Ichimoku
- Prix au-dessus du nuage = tendance haussière
- Prix en-dessous du nuage = tendance baissière
- Croisement Tenkan/Kijun = signal d'entrée potentiel

# ─── TES AJOUTS MODULE-04 ───────────────────────────────
# ────────────────────────────────────────────────────────


# ═══════════════════════════════════════════════════════
# MODULE-06 — PSYCHOLOGIE DU TRADER
# ═══════════════════════════════════════════════════════

## Situations où le bot doit mettre en garde (⚠️ warning affiché)
- Signal apparu après 3 trades perdants dans la journée
- Signal sur une paire où une perte a déjà été prise aujourd'hui
- Signal en dehors des sessions de marché actives

## ─── TES AJOUTS MODULE-06 ───────────────────────────────
# Colle ici le contenu de ton ebook psychologie
# ────────────────────────────────────────────────────────


# ═══════════════════════════════════════════════════════
# MODULE-07 — FIGURES HARMONIQUES (Butterfly & Shark)
# ═══════════════════════════════════════════════════════
# 📌 Sources : [ajoute tes sources]
# 📅 Dernière mise à jour : [DATE]

## Principe fondamental
Une figure harmonique est une suite de mouvements de prix liés par des
ratios de Fibonacci. Elle est valide UNIQUEMENT quand les points B, C ET D
sont confirmés (clôturés). Le point D = zone d'entrée (PRZ).

```
  X
   \
    A       C
     \     / \
      B   /   D  ← POINT D = PRZ = ENTRÉE
       \ /
        (ratios Fibonacci entre chaque segment)
```

## ✅ RÈGLE DE VALIDATION — LES 3 POINTS DOIVENT ÊTRE CONFIRMÉS

```python
# Le bot ne génère un signal QUE si B, C et D sont tous validés
if not (point_B_confirmed and point_C_confirmed and point_D_confirmed):
    return "❌ Figure harmonique incomplète — attendre validation de D"
```

---

## 🦋 BUTTERFLY (Papillon) — Retournement fort

### Structure des ratios Fibonacci
```
Segment XA : référence de base
Segment AB : retracement de XA à 0.786 (±2%)
Segment BC : retracement de AB entre 0.382 et 0.886
Segment CD : extension de BC entre 1.618 et 2.618
Point D    : extension de XA à 1.272 ou 1.618 ← PRZ (zone d'entrée)
```

### Validation B
```python
ratio_AB_XA = abs(B - A) / abs(X - A)
point_B_confirmed = (0.766 <= ratio_AB_XA <= 0.806)  # 0.786 ± 2%
```

### Validation C
```python
ratio_BC_AB = abs(C - B) / abs(A - B)
point_C_confirmed = (0.362 <= ratio_BC_AB <= 0.906)  # entre 0.382 et 0.886
```

### Validation D (PRZ — Point d'entrée)
```python
ratio_CD_BC   = abs(D - C) / abs(B - C)
ratio_XD_XA   = abs(D - X) / abs(A - X)

point_D_confirmed = (
    (1.578 <= ratio_CD_BC <= 2.678) and   # CD = 1.618 à 2.618
    (1.242 <= ratio_XD_XA <= 1.638)        # XD = 1.272 à 1.618
)
```

### Point d'entrée Butterfly
```python
# Bullish Butterfly (D en bas)
entree    = point_D
stop_loss = point_D - (abs(point_X - point_A) * 0.15)  # 15% sous X→A
tp1       = point_D + abs(point_D - point_C)            # Retour vers C
tp2       = point_D + abs(point_D - point_A)            # Retour vers A

# Bearish Butterfly (D en haut)
entree    = point_D
stop_loss = point_D + (abs(point_X - point_A) * 0.15)
tp1       = point_D - abs(point_D - point_C)
tp2       = point_D - abs(point_D - point_A)
```

### Ce que le bot dessine sur le graphique
```
  X ────────────────────────────── ligne X→A
   \
    A ──────────────────────────── ligne A→B
     \
      B ─────────────────────────── ligne B→C
       \     /
        C   / ──────────────────── ligne C→D
         \ /
          D  ← 🔴 PRZ (zone rouge) + flèche entrée + SL + TP1 + TP2
```

---

## 🦈 SHARK — Retournement agressif

### Structure des ratios
```
Segment XA : référence de base
Segment AB : extension de XA entre 1.130 et 1.618
Segment BC : extension de AB entre 1.618 et 2.240
Point C    : = point d'entrée (pas de point D comme Butterfly)
Ratio OC   : 0.886 ou 1.130 de X→A
```

### Validation des points
```python
# Point B
ratio_AB_XA = abs(B - A) / abs(X - A)
point_B_confirmed = (1.110 <= ratio_AB_XA <= 1.638)

# Point C (= point d'entrée du Shark)
ratio_BC_AB  = abs(C - B) / abs(A - B)
ratio_OC_OX  = abs(C - O) / abs(X - O)  # O = origine du pattern

point_C_confirmed = (
    (1.578 <= ratio_BC_AB <= 2.260) and
    (0.866 <= ratio_OC_OX <= 1.150)
)
```

### Point d'entrée Shark
```python
# Bullish Shark (C en bas)
entree    = point_C
stop_loss = point_C - (abs(point_X - point_A) * 0.10)
tp1       = point_C + abs(point_C - point_B)   # Retour vers B
tp2       = point_C + abs(point_C - point_A)   # Retour vers A

# Bearish Shark (C en haut)
entree    = point_C
stop_loss = point_C + (abs(point_X - point_A) * 0.10)
tp1       = point_C - abs(point_C - point_B)
tp2       = point_C - abs(point_C - point_A)
```

## ⛔ Rappel validation harmonique
- B non validé → pas de surveillance de C et D
- C non validé → pas de surveillance de D
- D non validé → pas de signal
- PRZ = zone de prix où convergent plusieurs ratios Fibonacci
- Si la bougie ne rejette pas la PRZ → attendre

# ─── TES AJOUTS MODULE-07 ───────────────────────────────
# Ajoute ici d'autres patterns harmoniques : Gartley, Bat, Crab
# ────────────────────────────────────────────────────────


# ═══════════════════════════════════════════════════════
# MODULE-08 — ZONE DE COMPRESSION
# ═══════════════════════════════════════════════════════
# 📌 Sources : [ajoute tes sources]
# 📅 Dernière mise à jour : [DATE]

## Définition
Une zone de compression est une zone où le prix consolide dans un range
très serré avant une explosion directionnelle. C'est une accumulation
d'énergie. Plus la compression est longue et serrée → plus l'explosion
qui suit est violente.

## Critères de détection
```python
# Une zone de compression est validée si :
nb_bougies_compression = 5   # minimum 5 bougies dans la zone
range_compression = (high_max - low_min) / close_moyen

# Range très serré
compression_validee = (
    range_compression < 0.015 and     # amplitude < 1.5% du prix
    nb_bougies_compression >= 5
)

# Encore mieux : ATR en forte baisse dans la zone
atr_compression  = atr(14, sur la zone)
atr_precedent    = atr(14, avant la zone)
compression_forte = atr_compression < atr_precedent * 0.5   # ATR divisé par 2
```

## Types de compressions

### Compression sur S/R (la plus puissante ⚡)
```
Résistance : ─────────────────────────
              | | | | | | | | | | |   ← bougies serrées = compression
Support    : ─────────────────────────
```
Signification : le marché hésite sur une zone clé → décision imminente

### Compression après figure chartiste
- Après un drapeau trop long → compression = signal de cassure proche
- Après un biseau terminal → compression = fin de la figure

### Compression + harmonique
- Si la PRZ d'un Butterfly ou Shark coïncide avec une zone de compression
→ Signal de retournement très fort

## Point d'entrée sur compression
```python
# La compression elle-même ne donne pas de point d'entrée
# Elle AMPLIFIE le signal d'une figure ou d'un reversal

# Attendre la cassure d'un côté :
if close > high_compression:
    entree    = high_compression                  # Cassure haussière
    stop_loss = low_compression - atr * 0.3       # Sous la compression
    amplitude = high_compression - low_compression
    tp1       = entree + amplitude                # Amplitude reportée
    tp2       = entree + amplitude * 2

elif close < low_compression:
    entree    = low_compression                   # Cassure baissière
    stop_loss = high_compression + atr * 0.3
    tp1       = entree - amplitude
    tp2       = entree - amplitude * 2
```

## Ce que le bot dessine
```
  ┌──────────────────────────────────────┐
  │  ZONE DE COMPRESSION (rectangle jaune│
  │  sur toute la durée de la consolidat.)│
  └──────────────────────────────────────┘
  ⬆️ ou ⬇️ Flèche d'entrée à la cassure
  ─── TP1 (amplitude x1)
  ─── TP2 (amplitude x2)
  ─── SL  (sous/au-dessus de la zone)
```

# ─── TES AJOUTS MODULE-08 ───────────────────────────────
# ────────────────────────────────────────────────────────


# ═══════════════════════════════════════════════════════
# MODULE-09 — ADX (Average Directional Index)
# VALIDATION DU MOMENTUM
# ═══════════════════════════════════════════════════════
# 📌 Sources : [ajoute tes sources]
# 📅 Dernière mise à jour : [DATE]

## Rôle de l'ADX dans le bot
L'ADX ne donne pas de direction. Il valide que le momentum est suffisant
pour qu'un trade soit pris. Sans ADX favorable → trade ignoré même si
la figure et le S/R sont parfaits.

## Lecture de l'ADX

```
ADX < 20        → Marché sans tendance, range / compression → attendre
ADX 20 à 25     → Début de tendance → signal acceptable avec prudence
ADX 25 à 40     → Tendance confirmée ✅ → condition momentum validée
ADX > 40        → Tendance forte ✅✅ → meilleur contexte pour trader
ADX > 60        → Tendance extrême, attention aux retournements violents
```

## +DI et -DI (lignes directionnelles)
```
+DI > -DI  → Momentum haussier dominant
-DI > +DI  → Momentum baissier dominant
Croisement +DI/-DI  → Changement de momentum (signal)
```

## Règle d'intégration dans le bot

```python
# VALIDATION ADX — obligatoire pour confirmer tout signal
def validate_adx(adx_value, di_plus, di_minus, signal_direction):

    # ADX trop faible = pas de trade
    if adx_value < 20:
        return False, "❌ ADX trop faible — pas de momentum"

    # Direction cohérente avec le signal
    if signal_direction == "LONG" and di_plus < di_minus:
        return False, "❌ ADX : momentum baissier dominant — pas de LONG"

    if signal_direction == "SHORT" and di_minus < di_plus:
        return False, "❌ ADX : momentum haussier dominant — pas de SHORT"

    # Signal fort si ADX en hausse
    adx_rising = adx_value > adx_value_previous
    if adx_value >= 25 and adx_rising:
        return True, "✅ ADX validé — momentum confirmé"

    return True, "⚠️ ADX acceptable — surveiller"
```

## Ce que le bot affiche
- Dans le label sur le graphique : "ADX: 32 ✅" ou "ADX: 15 ❌"
- Si ADX invalide → figure détectée mais signal bloqué + message affiché

# ─── TES AJOUTS MODULE-09 ───────────────────────────────
# ────────────────────────────────────────────────────────


# ═══════════════════════════════════════════════════════
# MODULE-10 — QQE (Quantitative Qualitative Estimation)
# CONFIRMATION DU CROISEMENT
# ═══════════════════════════════════════════════════════
# 📌 Sources : [ajoute tes sources]
# 📅 Dernière mise à jour : [DATE]

## Rôle du QQE dans le bot
Le QQE confirme que le momentum de court terme est dans le sens du trade.
Un croisement QQE dans le bon sens APRÈS la validation ADX = confluence
maximale → signal le plus fort possible.

## Lecture du QQE
```
Ligne rapide (QQE Line)  = RSI lissé de façon agressive
Ligne lente (Signal Line) = lissage additionnel de la ligne rapide

Croisement HAUSSIER : rapide passe AU-DESSUS de la lente
Croisement BAISSIER : rapide passe EN-DESSOUS de la lente
```

## Règle de validation QQE

```python
def validate_qqe(qqe_fast, qqe_slow, qqe_fast_prev, qqe_slow_prev, signal_direction):

    # Croisement haussier = rapide vient de passer au-dessus de la lente
    crossover_bullish  = (qqe_fast > qqe_slow) and (qqe_fast_prev <= qqe_slow_prev)

    # Croisement baissier = rapide vient de passer en-dessous de la lente
    crossover_bearish  = (qqe_fast < qqe_slow) and (qqe_fast_prev >= qqe_slow_prev)

    if signal_direction == "LONG":
        if crossover_bullish:
            return True, "✅ QQE croisement haussier confirmé"
        elif qqe_fast > qqe_slow:
            return True, "⚠️ QQE haussier mais croisement déjà passé"
        else:
            return False, "❌ QQE baissier — momentum court terme contre le trade"

    if signal_direction == "SHORT":
        if crossover_bearish:
            return True, "✅ QQE croisement baissier confirmé"
        elif qqe_fast < qqe_slow:
            return True, "⚠️ QQE baissier mais croisement déjà passé"
        else:
            return False, "❌ QQE haussier — momentum court terme contre le trade"
```

## Hiérarchie de qualité du croisement QQE

```
✅✅ OPTIMAL   : croisement QQE vient de se produire (bougie précédente)
✅   BON       : QQE dans le bon sens depuis 1 à 3 bougies
⚠️   ACCEPTABLE : QQE dans le bon sens depuis 4 à 6 bougies
❌   TROP TARD  : QQE dans le bon sens depuis 7+ bougies → attendre reset
```

# ─── TES AJOUTS MODULE-10 ───────────────────────────────
# ────────────────────────────────────────────────────────


# ═══════════════════════════════════════════════════════
# LOGIQUE DE CONFLUENCE FINALE — TOUT ASSEMBLER
# ═══════════════════════════════════════════════════════

## Ordre de vérification du bot (séquentiel, chaque étape peut bloquer)

```
ÉTAPE 1 — Zone S/R identifiée ?
          NON → ❌ STOP

ÉTAPE 2 — Figure chartiste OU reversal candle OU harmonique validée ?
          NON → ❌ STOP

ÉTAPE 3 — ADX ≥ 20 ET direction cohérente ?
          NON → ⚠️ signal affiché mais marqué "MOMENTUM INSUFFISANT"

ÉTAPE 4 — QQE croisé dans le bon sens ?
          NON → ⚠️ signal affiché mais marqué "QQE NON ALIGNÉ"

ÉTAPE 5 — Zone de compression détectée en plus ?
          OUI → 🔥 signal marqué "COMPRESSION EXPLOSIVE"

ÉTAPE 6 → Calculer ENTRÉE / SL / TP1 / TP2 et dessiner sur le graphique
```

## Label affiché sur le graphique pour chaque signal

```
┌─────────────────────────────────────────────┐
│  🦋 BUTTERFLY BULLISH | 30m | BTC/USDT      │
│  S/R : Support 42 000$   ✅                 │
│  Figure : PRZ validée (B+C+D)  ✅           │
│  Compression : ✅ Zone de 8 bougies         │
│  ADX : 31 ↑  ✅                             │
│  QQE : Croisement haussier ✅               │
│                                             │
│  ⬆️ ENTRÉE  : 42 150                        │
│  🔴 SL      : 41 800                        │
│  🟠 TP1     : 43 200                        │
│  🟢 TP2     : 44 500                        │
└─────────────────────────────────────────────┘
```

# ─── ZONE D'EXTENSION ────────────────────────────────────
# MODULE-11 — Wyckoff
# MODULE-12 — Smart Money Concepts (SMC, Order Blocks, FVG)
# MODULE-13 — Price Action avancée
# MODULE-14 — Money Management
# ─────────────────────────────────────────────────────────


# ═══════════════════════════════════════════════════════
# INSTRUCTIONS DE DÉMARRAGE POUR CLAUDE CODE
# ═══════════════════════════════════════════════════════

## ✅ ÉTAPES — EXÉCUTE DANS CET ORDRE

1. Génère le fichier `CLAUDE.md` résumant toutes les règles
2. Code `sr_detector.py` — détecte les zones S/R
3. Code `pattern_detector.py` — détecte les 11 figures chartistes
4. Code `candle_detector.py` — détecte les reversal candles
5. Code `harmonic_detector.py` — détecte Butterfly et Shark (validation B, C, D)
6. Code `compression_detector.py` — détecte les zones de compression (ATR + range)
7. Code `adx_validator.py` — valide le momentum ADX + direction DI+/DI-
8. Code `qqe_validator.py` — valide le croisement QQE
9. Code `gate_checker.py` — vérifie toutes les conditions dans l'ordre séquentiel
10. Code `entry_calculator.py` — calcule ENTRÉE / SL / TP1 / TP2 selon la figure
11. Code `visualizer.py` — génère Pine Script + MQL4 avec label complet + tous les points
12. Code `scanner.py` — boucle toutes les 15 minutes

## 📌 RÈGLES DE DÉVELOPPEMENT
- Python 3.10+ | ccxt | pandas | numpy | scipy
- Commentaires en français
- `gate_checker.py` bloque tout si une condition manque — non contournable
- `entry_calculator.py` retourne un objet avec : entry, stop_loss, tp1, tp2 (prix exacts)
- `visualizer.py` génère des fichiers .pine et .mql4 PRÊTS à copier dans TradingView / MT4
- Le fichier Pine Script généré doit être exécutable tel quel dans TradingView sans modification
