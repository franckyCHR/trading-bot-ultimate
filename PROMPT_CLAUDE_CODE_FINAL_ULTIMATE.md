# 🏆 PROMPT CLAUDE CODE — RECHERCHE & INTÉGRATION DES MEILLEURES LIBRAIRIES
# Colle ce prompt entier dans ton terminal Claude Code
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

---

## 🎯 MISSION

Tu vas construire le meilleur bot de trading technique qui existe en Python.
Pour ça, commence par faire une RECHERCHE APPROFONDIE sur internet pour trouver
les meilleures librairies disponibles dans chaque catégorie.

Ne te contente pas de la première résultat. Compare, évalue, choisis le TOP.

---

## 🔍 ÉTAPE 1 — RECHERCHE (fais-la AVANT d'installer quoi que ce soit)

### Recherche dans cet ordre et prends des notes :

**A) Librairies de détection de patterns techniques**
Cherche sur PyPI, GitHub, et Google :
- `pandas-ta` vs `ta-lib` vs `finta` vs `technical` — lequel a le plus de patterns ?
- Y a-t-il des librairies spécialisées en figures chartistes (ETE, Double Top...) ?
- Cherche : "python chart pattern detection library github stars"
- Cherche : "python harmonic pattern detection butterfly shark gartley"
- Cherche : "python candlestick pattern detection library"

**B) Librairies de dessin / visualisation de figures**
- `mplfinance` — rendu des chandeliers et figures
- `plotly` vs `bokeh` — graphiques interactifs
- Y a-t-il des librairies qui génèrent du Pine Script automatiquement ?
- Cherche : "python tradingview pine script generator library"
- Cherche : "python chart pattern drawing visualization github"

**C) Librairies de calcul d'indicateurs**
- `pandas-ta` vs `ta-lib` vs `tulipy` — lequel supporte QQE et ADX complets ?
- Cherche : "python QQE indicator implementation github"
- Cherche : "python ADX DI+ DI- indicator library"

**D) Librairies de données de marché**
- `ccxt` vs `yfinance` vs `alpaca` — lequel a les meilleures données temps réel ?
- Y a-t-il mieux pour des données tick by tick ?
- Cherche : "best python library real time market data crypto forex 2024"

**E) Repos GitHub spécialisés trading technique**
- Cherche : "github python trading bot chart patterns stars:>500"
- Cherche : "github harmonic pattern scanner python"
- Cherche : "github candlestick pattern recognition python"

---

## 📊 ÉTAPE 2 — TABLEAU COMPARATIF

Après ta recherche, crée un fichier `RESEARCH.md` avec :

```markdown
# Résultats de recherche — Meilleures librairies

## Détection de patterns
| Librairie | Stars GitHub | Patterns supportés | QQE | ADX | Harmoniques | Choix |
|-----------|-------------|-------------------|-----|-----|-------------|-------|
| ...       | ...         | ...               | ... | ... | ...         | ...   |

## Visualisation
| Librairie | Type output | Pine Script | MQL4 | Qualité visuelle | Choix |
...

## Données marché
...

## 🏆 SÉLECTION FINALE — ce qu'on installe
```

---

## 📦 ÉTAPE 3 — INSTALLATION

Installe uniquement les librairies sélectionnées.
Pour chaque librairie, vérifie qu'elle fonctionne avec un test simple.

```bash
pip install [les meilleures librairies sélectionnées]
```

---

## 🏗️ ÉTAPE 4 — ARCHITECTURE DU BOT

Une fois les librairies choisies, crée cette structure :

```
trading-bot/
│
├── CLAUDE.md                        ← Règles maîtres du trader
│
├── knowledge/
│   ├── MODULE-01-sr.md              ← Support & Résistance
│   ├── MODULE-02-chart.md           ← Figures chartistes (ETE, Drapeau, Biseau...)
│   ├── MODULE-03-candles.md         ← Chandeliers reversal
│   ├── MODULE-04-indicators.md      ← QQE, ADX, RSI, Ichimoku
│   ├── MODULE-05-entries.md         ← Calcul ENTRÉE / SL / TP1 / TP2
│   ├── MODULE-06-psychology.md      ← Psychologie du trader
│   ├── MODULE-07-harmonics.md       ← Butterfly, Shark (ratios Fibonacci)
│   ├── MODULE-08-compression.md     ← Zones de compression
│   ├── MODULE-09-adx.md             ← ADX momentum
│   ├── MODULE-10-qqe.md             ← QQE croisement
│   └── [MODULE-XX-xxx.md]           ← Extensible à l'infini
│
├── bot/
│   ├── data/
│   │   └── market_feed.py           ← Récupération données (meilleure librairie)
│   │
│   ├── detection/
│   │   ├── sr_detector.py           ← Support & Résistance
│   │   ├── pattern_detector.py      ← Figures chartistes (via meilleure librairie)
│   │   ├── candle_detector.py       ← Chandeliers reversal
│   │   ├── harmonic_detector.py     ← Butterfly, Shark (validation B, C, D)
│   │   ├── compression_detector.py  ← Zones de compression (ATR + range)
│   │   └── indicator_engine.py      ← QQE, ADX, RSI, Ichimoku
│   │
│   ├── validation/
│   │   ├── gate_checker.py          ← Vérifie les 2 conditions obligatoires
│   │   ├── adx_validator.py         ← Valide momentum ADX
│   │   └── qqe_validator.py         ← Valide croisement QQE
│   │
│   ├── entries/
│   │   └── entry_calculator.py      ← ENTRÉE / SL / TP1 / TP2 par figure
│   │
│   ├── drawers/                     ← Librairie de drawers (déjà créée)
│   │   ├── __init__.py              ← Registre + fallback automatique
│   │   ├── base_drawer.py           ← Classe de base + fallback générique
│   │   ├── chart_drawers.py         ← ETE, Double Top, Flag, Biseau, Triangle
│   │   ├── harmonic_drawers.py      ← Butterfly, Shark
│   │   ├── special_drawers.py       ← Reversal Candle, Compression
│   │   └── [nouveau_drawer.py]      ← Ajoute tes nouveaux drawers ici
│   │
│   ├── output/
│   │   ├── visualizer.py            ← Génère Pine Script + MQL4
│   │   ├── alert_manager.py         ← Alertes (Telegram / console)
│   │   └── report_generator.py      ← Rapport des signaux détectés
│   │
│   └── brain/
│       └── claude_brain.py          ← Charge tous les modules + valide le setup
│
├── outputs/
│   ├── tradingview/                 ← Scripts .pine générés
│   └── mt4/                         ← Scripts .mql4 générés
│
├── scanner.py                       ← Scanner principal (toutes les 15 min)
└── requirements.txt                 ← Toutes les dépendances
```

---

## 🚨 RÈGLES ABSOLUES DU BOT (non négociables)

```
╔══════════════════════════════════════════════════════════════════╗
║  RÈGLE N°1 — JAMAIS de signal sans zone S/R identifiée         ║
║  RÈGLE N°2 — JAMAIS de signal sans figure chartiste             ║
║              CLAIREMENT FORMÉE                                   ║
║              OU reversal pattern chandelier CONFIRMÉ             ║
║                                                                  ║
║  RÈGLE N°3 — TOUTES les figures détectées doivent être          ║
║              DESSINÉES VISUELLEMENT sur le graphique             ║
║              (Pine Script + MQL4 générés automatiquement)        ║
║                                                                  ║
║  RÈGLE N°4 — Le bot affiche TOUJOURS :                          ║
║              ⬆️/⬇️ Point d'entrée exact                          ║
║              🔴 Stop Loss                                        ║
║              🟠 TP1 (50% objectif)                               ║
║              🟢 TP2 (objectif complet)                           ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 🎨 FIGURES À DÉTECTER ET DESSINER

### Figures chartistes classiques
- Épaule-Tête-Épaule (Bearish) + ETE Inversé (Bullish)
- Double Top (M) + Double Bottom (W)
- Drapeau Haussier + Drapeau Baissier
- Biseau Ascendant (Bearish) + Biseau Descendant (Bullish)
- Triangle Ascendant (Bullish) + Triangle Descendant (Bearish) + Triangle Symétrique
- Fanion (Pennant)

### Figures harmoniques
- Butterfly (Bullish + Bearish) — validation B, C, D avec ratios Fibonacci
- Shark (Bullish + Bearish) — validation B, C avec ratios Fibonacci

### Figures spéciales
- Zone de Compression (rectangle jaune + explosion à la cassure)
- Chandeliers reversal : Pin Bar, Marteau, Engulfing, Morning/Evening Star, Harami, Doji

---

## 📐 LOGIQUE D'ENTRÉE (pour chaque figure)

Chaque figure a son propre calcul de point d'entrée :

| Figure                | Entrée                          | SL                        | TP2                        |
|-----------------------|---------------------------------|---------------------------|---------------------------|
| ETE                   | Cassure neckline                | Au-dessus épaule droite   | Neckline − hauteur tête   |
| Double Top            | Cassure creux intermédiaire     | Au-dessus des tops        | Creux − amplitude         |
| Drapeau               | Cassure canal                   | Bord opposé du canal      | Entrée + hauteur mât      |
| Biseau Asc.           | Cassure support biseau          | Au-dessus résistance      | Base du biseau            |
| Triangle Asc.         | Cassure résistance horizontale  | Dernier creux support     | Entrée + hauteur triangle |
| Butterfly             | Point D (PRZ)                   | 15% sous XA               | Retour vers A             |
| Shark                 | Point C                         | 10% sous XA               | Retour vers A             |
| Compression           | Cassure haute/basse de la zone  | Côté opposé de la zone    | Entrée ± amplitude × 2   |
| Reversal Candle       | Clôture de la bougie signal     | Mèche opposée + ATR×0.3   | RR 1:2                    |

---

## 🔔 CONFLUENCE FINALE — ORDRE DE VÉRIFICATION

```
1. Zone S/R identifiée ?          NON → ❌ STOP
2. Figure ou reversal confirmé ?  NON → ❌ STOP
3. ADX ≥ 20 et direction OK ?     NON → ⚠️ signal marqué "momentum faible"
4. QQE croisé dans le bon sens ?  NON → ⚠️ signal marqué "QQE non aligné"
5. Zone de compression aussi ?    OUI → 🔥 "COMPRESSION EXPLOSIVE"
6. → Calculer ENTRÉE/SL/TP + Dessiner sur le graphique
```

---

## 🖥️ CE QUE LE TRADER VOIT SUR SON GRAPHIQUE

Pour chaque signal, afficher ce label :

```
┌────────────────────────────────────────────────────┐
│  🔴 ETE BEARISH | BTC/USDT | 1H                   │
│  S/R ✅  |  Figure nette ✅  |  Compression ✅     │
│  ADX: 34↑ ✅  |  QQE croisement ✅                │
│                                                    │
│  ⬇️  ENTRÉE  : 43 250                             │
│  🔴  SL      : 44 100                             │
│  🟠  TP1     : 42 400                             │
│  🟢  TP2     : 41 550                             │
└────────────────────────────────────────────────────┘
```

---

## 🏁 ORDRE D'EXÉCUTION — FAIS DANS CET ORDRE

### Phase 1 — Recherche & Setup
1. **Recherche** sur internet (ÉTAPE 1 ci-dessus)
2. **Crée RESEARCH.md** avec tableau comparatif
3. **Installe** les meilleures librairies sélectionnées
4. **Vérifie** que chaque librairie fonctionne

### Phase 2 — Génère CLAUDE.md
5. Crée `CLAUDE.md` qui synthétise toutes les règles de ce prompt
6. Ce fichier sera chargé à chaque analyse pour contextualiser Claude

### Phase 3 — Couche de données
7. Code `market_feed.py` avec la meilleure librairie trouvée

### Phase 4 — Couche de détection
8. Code `sr_detector.py`
9. Code `pattern_detector.py` en utilisant la meilleure librairie de patterns
10. Code `candle_detector.py`
11. Code `harmonic_detector.py` (Butterfly + Shark, validation B/C/D)
12. Code `compression_detector.py`
13. Code `indicator_engine.py` (QQE, ADX+DI, RSI, Ichimoku)

### Phase 5 — Couche de validation
14. Code `gate_checker.py` (2 conditions obligatoires bloquantes)
15. Code `adx_validator.py`
16. Code `qqe_validator.py`

### Phase 6 — Couche d'entrée
17. Code `entry_calculator.py` (ENTRÉE/SL/TP1/TP2 par figure)

### Phase 7 — Couche de dessin
18. Intègre les drawers existants (dossier `drawers/` déjà créé)
19. Si tu as trouvé de meilleures librairies de dessin → améliore les drawers
20. Code `visualizer.py` (génère Pine Script + MQL4 prêts à coller)

### Phase 8 — Cerveau Claude
21. Code `claude_brain.py` qui charge tous les MODULE-XX.md comme contexte

### Phase 9 — Scanner final
22. Code `scanner.py` avec boucle toutes les 15 minutes
23. Code `alert_manager.py` (console d'abord, Telegram ensuite)
24. Génère `requirements.txt` complet

### Phase 10 — Test
25. Lance un scan sur BTC/USDT en 1h et montre-moi le premier signal détecté
26. Génère le Pine Script correspondant
27. Vérifie que le Pine Script est copiable directement dans TradingView

---

## 📌 STANDARDS DE CODE

- Python 3.10+
- Commentaires en français
- Type hints sur toutes les fonctions
- Chaque détecteur retourne un dataclass structuré
- Chaque drawer retourne Pine Script + MQL4 prêts à coller sans modification
- Le drawer registry utilise le fallback générique si un pattern inconnu arrive
- Aucune erreur possible dans le pipeline de dessin

---

## 🔮 ÉVOLUTIVITÉ

Ce bot est conçu pour grandir. À chaque nouvelle formation/vidéo/ebook :
- Ajouter les règles dans le MODULE correspondant
- Le bot les intègre automatiquement au prochain chargement
- Pour une nouvelle figure : créer un drawer + l'enregistrer dans le registre

Modules futurs prévus :
- MODULE-11 — Wyckoff (accumulation, distribution, springs)
- MODULE-12 — Smart Money Concepts (order blocks, FVG, liquidity)
- MODULE-13 — Price Action avancée (inside bar, outside bar)
- MODULE-14 — Money Management (risk per trade, position sizing)
- MODULE-15 — Corrélations inter-marchés (DXY, Gold, Oil)
