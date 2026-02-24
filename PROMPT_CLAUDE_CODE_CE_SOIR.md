# 🏆 PROMPT CLAUDE CODE — TRADING BOT ULTIMATE
# ══════════════════════════════════════════════════════════════════════
# INSTRUCTIONS : Colle ce prompt ENTIER dans ton terminal Claude Code
# Tous les fichiers de base sont déjà dans le dossier — Claude Code
# doit les compléter, améliorer et assembler en bot fonctionnel.
# ══════════════════════════════════════════════════════════════════════

---

## 🎭 TON RÔLE

Tu es mon développeur expert en trading technique et Python.
Tu dois livrer ce soir un bot de trading 100% fonctionnel.
La structure du projet est déjà créée avec des fichiers de base.
Tu dois :
1. Rechercher les MEILLEURES librairies disponibles
2. Compléter tous les fichiers manquants
3. Assembler le tout en un pipeline qui tourne

---

## 📁 FICHIERS DÉJÀ CRÉÉS — NE PAS RÉÉCRIRE

Ces fichiers sont déjà prêts dans le projet :

```
✅ CLAUDE.md                              ← Cerveau du bot
✅ knowledge/MODULE-01-sr.md             ← Support & Résistance
✅ knowledge/MODULE-02-chart.md          ← Figures chartistes
✅ knowledge/MODULE-03-candles.md        ← Chandeliers reversal
✅ knowledge/MODULE-04-indicators.md     ← QQE, ADX, RSI, Ichimoku
✅ knowledge/MODULE-05-entries.md        ← Formules d'entrée
✅ knowledge/MODULE-06-psychology.md     ← Psychologie
✅ knowledge/MODULE-07-harmonics.md      ← Butterfly, Shark, Gartley, Bat, Crab
✅ knowledge/MODULE-08-compression.md    ← Zones de compression
✅ knowledge/MODULE-09-adx.md            ← ADX momentum
✅ knowledge/MODULE-10-qqe.md            ← QQE croisement
✅ bot/validation/gate_checker.py        ← 2 portes obligatoires
✅ bot/entries/entry_calculator.py       ← Calcul ENTRÉE/SL/TP par figure
✅ bot/output/alert_manager.py           ← Console + Telegram
✅ bot/output/backtester.py             ← Validation historique
✅ bot/output/dashboard_generator.py    ← Dashboard HTML temps réel
✅ bot/detection/multi_timeframe.py     ← Analyse HTF/LTF
✅ bot/drawers/__init__.py              ← Registre drawers + fallback
✅ bot/drawers/base_drawer.py           ← Classe de base
✅ bot/drawers/chart_drawers.py         ← ETE, Double Top, Flag, Biseau, Triangle
✅ bot/drawers/harmonic_drawers.py      ← Butterfly, Shark
✅ bot/drawers/special_drawers.py       ← Reversal Candle, Compression
✅ scanner.py                            ← Scanner principal
✅ requirements.txt                      ← Dépendances
✅ .env.example                          ← Template variables d'environnement
```

---

## 🔍 ÉTAPE 1 — RECHERCHE (OBLIGATOIRE AVANT DE CODER)

Avant d'écrire une seule ligne de code, cherche sur internet :

### A) Meilleure librairie de détection de patterns
```
Cherche : "python chart pattern detection library github 2024"
Cherche : "python harmonic pattern scanner butterfly shark gartley github"
Cherche : "pandas-ta chart patterns candlestick patterns"
Cherche : "python technical analysis pattern recognition pypi"
Compare : pandas-ta vs ta-lib vs finta vs mplfinance patterns
```

### B) Meilleure librairie de données temps réel
```
Cherche : "ccxt python crypto real time data best practices 2024"
Cherche : "python websocket crypto market data binance"
Cherche : "yfinance vs ccxt performance comparison"
```

### C) Meilleure librairie de dessin de figures
```
Cherche : "python tradingview pine script generator github"
Cherche : "python chart pattern visualization mplfinance plotly 2024"
Cherche : "python draw technical patterns chart automatically"
```

### D) QQE indicator Python
```
Cherche : "QQE indicator python implementation github"
Cherche : "pandas-ta QQE quantitative qualitative estimation"
```

Crée `RESEARCH.md` avec tes conclusions AVANT de continuer.

---

## 📦 ÉTAPE 2 — INSTALLATION

```bash
pip install -r requirements.txt
```

Si tu trouves des librairies meilleures que celles dans requirements.txt,
mets à jour le fichier et installe-les.

---

## 🏗️ ÉTAPE 3 — FICHIERS À CRÉER

Voici les fichiers qui manquent. Crée-les dans cet ordre :

### 3.1 — bot/data/market_feed.py
```python
"""
Récupère les données OHLCV depuis l'exchange.
Utilise la meilleure librairie trouvée à l'étape 1.
Doit retourner un DataFrame pandas avec colonnes :
[timestamp, open, high, low, close, volume]
"""

class MarketFeed:
    def __init__(self, exchange_id: str = "binance"): ...
    def get_ohlcv(self, pair: str, timeframe: str, limit: int = 300) -> pd.DataFrame: ...
    def get_current_price(self, pair: str) -> float: ...
```

### 3.2 — bot/detection/sr_detector.py
```python
"""
Détecte les zones Support & Résistance selon MODULE-01.
Méthodes : pivots hauts/bas, clusters, round numbers, ATH/ATL.
Retourne une liste de zones avec prix, force (1-3), nb touches.
"""

class SRDetector:
    def detect(self, df: pd.DataFrame) -> list[dict]: ...
    # Retourne : [{"price": 42000, "strength": 3, "touches": 5, "type": "resistance"}]
```

### 3.3 — bot/detection/pattern_detector.py
```python
"""
Détecte les 12 figures chartistes selon MODULE-02.
Utilise la meilleure librairie trouvée + détection custom si besoin.
Pour chaque figure retourne les points clés pour le drawer.

Figures : ETE, ETE_INVERSE, DOUBLE_TOP, DOUBLE_BOTTOM,
          BULL_FLAG, BEAR_FLAG, PENNANT,
          BISEAU_ASCENDANT, BISEAU_DESCENDANT,
          TRIANGLE_ASCENDANT, TRIANGLE_DESCENDANT, TRIANGLE_SYMETRIQUE
"""

class PatternDetector:
    def detect(self, df: pd.DataFrame, sr_zones: list) -> list[dict]: ...
```

### 3.4 — bot/detection/candle_detector.py
```python
"""
Détecte les chandeliers de reversal selon MODULE-03.
Chandeliers : Pin Bar, Marteau, Engulfing, Morning/Evening Star, Harami, Doji.
Ne retourne un signal que si le chandelier est SUR une zone S/R.
"""

class CandleDetector:
    def detect(self, df: pd.DataFrame, sr_zones: list) -> list[dict]: ...
```

### 3.5 — bot/detection/harmonic_detector.py
```python
"""
Détecte les figures harmoniques selon MODULE-07.
Figures : Butterfly, Shark, Gartley, Bat, Crab.
Validation stricte des ratios Fibonacci B, C, D.
JAMAIS de signal sans B+C+D validés.
"""

class HarmonicDetector:
    def detect(self, df: pd.DataFrame, sr_zones: list) -> list[dict]: ...
    def _validate_butterfly(self, X,A,B,C,D) -> bool: ...
    def _validate_shark(self, O,X,A,B,C) -> bool: ...
    def _validate_gartley(self, X,A,B,C,D) -> bool: ...
    def _validate_bat(self, X,A,B,C,D) -> bool: ...
    def _validate_crab(self, X,A,B,C,D) -> bool: ...
```

### 3.6 — bot/detection/compression_detector.py
```python
"""
Détecte les zones de compression selon MODULE-08.
Critères : range < 1.5% + ATR divisé par 2 + minimum 5 bougies.
"""

class CompressionDetector:
    def detect(self, df: pd.DataFrame) -> list[dict]: ...
```

### 3.7 — bot/detection/indicator_engine.py
```python
"""
Calcule tous les indicateurs nécessaires.
Utilise pandas-ta ou la meilleure librairie trouvée.
Retourne un dict avec : adx, di_plus, di_minus, adx_rising,
                        qqe_fast, qqe_slow, qqe_fast_prev, qqe_slow_prev,
                        qqe_cross_bars_ago, rsi, macd, bbands
"""

class IndicatorEngine:
    def compute(self, df: pd.DataFrame) -> dict: ...
```

### 3.8 — bot/validation/adx_validator.py
```python
"""
Valide le momentum ADX selon MODULE-09.
ADX < 20 → signal bloqué.
DI dans la mauvaise direction → signal bloqué.
"""

class ADXValidator:
    def __init__(self, min_adx: float = 20): ...
    def validate(self, adx: float, di_plus: float, di_minus: float, direction: str) -> tuple[bool, str]: ...
```

### 3.9 — bot/validation/qqe_validator.py
```python
"""
Valide le croisement QQE selon MODULE-10.
Retourne qualité du croisement : OPTIMAL / BON / ACCEPTABLE / TROP_TARD.
"""

class QQEValidator:
    def validate(self, qqe_fast, qqe_slow, qqe_fast_prev, qqe_slow_prev, bars_ago, direction) -> tuple[bool, str]: ...
```

### 3.10 — bot/brain/claude_brain.py
```python
"""
Charge tous les modules MODULE-XX.md comme contexte.
Détecte automatiquement les nouveaux modules ajoutés.
"""

class ClaudeBrain:
    def load_knowledge(self) -> str: ...
    def get_context(self) -> str: ...
```

### 3.11 — bot/output/report_generator.py
```python
"""
Génère des rapports de performance quotidiens.
Analyse les logs de signals pour mesurer le winrate réel.
"""

class ReportGenerator:
    def daily_report(self) -> str: ...
    def weekly_report(self) -> str: ...
```

---

## 🚨 RÈGLES ABSOLUES — VÉRIFIE À CHAQUE FICHIER

```
╔══════════════════════════════════════════════════════════╗
║ RÈGLE 1 — Jamais de signal sans zone S/R                ║
║ RÈGLE 2 — Jamais de signal sans figure ou reversal      ║
║ RÈGLE 3 — Toute figure détectée DOIT être dessinée      ║
║ RÈGLE 4 — Toujours : ENTRÉE + SL + TP1 + TP2           ║
║ RÈGLE 5 — Si drawer manquant → fallback générique       ║
╚══════════════════════════════════════════════════════════╝
```

---

## 🎨 FIGURES À DESSINER — VISUELLEMENT SUR LE GRAPHIQUE

Pour CHAQUE figure, le Pine Script généré doit afficher :
- Les points et lignes de la figure (neckline, segments, etc.)
- Zone colorée transparente sur la figure
- Label avec nom + direction
- Flèche d'entrée au prix exact
- Ligne rouge SL + prix
- Ligne orange TP1 + prix
- Ligne verte TP2 + prix

Couleurs par figure :
- ETE / Double Top / Biseau Asc → 🔴 Rouge
- ETE Inv / Double Bottom / Biseau Desc → 🟢 Vert
- Drapeau / Mât → 🔵 Bleu (mât) + 🟠 Orange (canal)
- Triangle Sym / Compression → 🟡 Jaune
- Butterfly : XA=bleu, AB=orange, BC=vert, CD=violet + PRZ colorée
- Reversal Candle → cercle géant autour de la bougie

---

## 📊 LOGIQUE DE CONFLUENCE FINALE

```
ÉTAPE 1 → S/R identifié ?              NON → ❌ STOP
ÉTAPE 2 → Figure ou reversal ?         NON → ❌ STOP
ÉTAPE 3 → ADX ≥ 20 + DI aligné ?      NON → ⚠️ signal "momentum faible"
ÉTAPE 4 → QQE croisé dans le bon sens? NON → ⚠️ signal "QQE non aligné"
ÉTAPE 5 → Compression aussi ?          OUI → 🔥 "COMPRESSION EXPLOSIVE"
ÉTAPE 6 → HTF aligné ?                 OUI → ✅✅ "SIGNAL HTF CONFIRMÉ"
ÉTAPE 7 → Calculer ENTRÉE/SL/TP + Dessiner + Alerter + Dashboard
```

---

## 📐 CALCUL D'ENTRÉE (résumé des formules)

| Figure              | Entrée                    | SL                       | TP2                      |
|---------------------|---------------------------|--------------------------|--------------------------|
| ETE Bearish         | Neckline                  | Épaule D + ATR×0.5       | Neckline − hauteur       |
| ETE Inversé         | Neckline                  | Épaule D − ATR×0.5       | Neckline + hauteur       |
| Double Top          | Creux intermédiaire       | Max(tops) + ATR×0.5      | Creux − amplitude        |
| Double Bottom       | Pic intermédiaire         | Min(bots) − ATR×0.5      | Pic + amplitude          |
| Bull Flag           | Haut du canal             | Bas canal − ATR×0.3      | Entrée + hauteur mât     |
| Bear Flag           | Bas du canal              | Haut canal + ATR×0.3     | Entrée − hauteur mât     |
| Biseau Asc.         | Support biseau            | Résistance + ATR×0.5     | Base biseau              |
| Biseau Desc.        | Résistance biseau         | Support − ATR×0.5        | Base biseau              |
| Triangle Asc.       | Résistance horizontale    | Dernier creux − ATR×0.3  | Entrée + hauteur         |
| Triangle Desc.      | Support horizontal        | Dernier sommet + ATR×0.3 | Entrée − hauteur         |
| Butterfly           | Point D (PRZ)             | D ± XA×0.15              | Retour vers A            |
| Shark               | Point C                   | C ± XA×0.10              | Retour vers A            |
| Gartley             | Point D                   | X ± ATR                  | Retour vers B            |
| Bat                 | Point D                   | X ± ATR×0.5              | Retour vers A            |
| Crab                | Point D                   | D ± ATR×1.5              | Retour vers B            |
| Compression         | Cassure haut/bas          | Côté opposé − ATR×0.3   | Entrée ± amplitude×2     |
| Reversal Candle     | Close bougie signal       | Mèche ± ATR×0.3          | RR 1:2                   |

---

## 🔔 TELEGRAM — CONFIGURATION

```bash
# Dans ton .env :
TELEGRAM_BOT_TOKEN=ton_token
TELEGRAM_CHAT_ID=ton_chat_id

# Le bot envoie automatiquement :
# 1. L'alerte texte formatée avec prix
# 2. Le fichier Pine Script (.pine) prêt à coller dans TradingView
```

---

## 🕐 MULTI-TIMEFRAME — RÈGLE D'OR

```
Signal 30m → vérifier tendance 1h
Signal 1h  → vérifier tendance 4h
Signal 4h  → vérifier tendance 1d

Signal dans le sens de la tendance HTF → ✅✅ priorité maximale
Signal neutre (HTF neutre)             → ✅  acceptable
Signal contre HTF                      → ⚠️  avertissement (configurable)
```

---

## 📊 BACKTESTING — VALIDATION

Après avoir codé le bot, lance un backtest sur les 3 derniers mois :
```python
from bot.output.backtester import Backtester
bt = Backtester(risk_pct=1.0)
report = bt.run(historical_signals, ohlcv_df)
report.print()
```

Le backtest doit montrer au minimum :
- Winrate > 40% (avec RR 1:2, ça reste profitable)
- RR moyen > 1.5

---

## 🏁 ORDRE D'EXÉCUTION — CE SOIR

### Phase 1 — Recherche & Setup (20 min)
1. Recherche sur internet (ÉTAPE 1)
2. Crée RESEARCH.md
3. Met à jour requirements.txt si nécessaire
4. `pip install -r requirements.txt`

### Phase 2 — Données & Indicateurs (30 min)
5. Code `market_feed.py`
6. Code `indicator_engine.py` (QQE, ADX, RSI obligatoires)
7. Test rapide : récupère BTC/USDT 1h et affiche les indicateurs

### Phase 3 — Détection (60 min)
8. Code `sr_detector.py`
9. Code `pattern_detector.py` (utilise la meilleure librairie trouvée)
10. Code `candle_detector.py`
11. Code `harmonic_detector.py` (Butterfly, Shark, Gartley, Bat, Crab)
12. Code `compression_detector.py`

### Phase 4 — Validation (20 min)
13. Code `adx_validator.py`
14. Code `qqe_validator.py`
15. Vérifie `gate_checker.py` (déjà créé — adapter si besoin)

### Phase 5 — Drawers (30 min)
16. Vérifie que les drawers existants fonctionnent
17. Améliore les drawers si tu as trouvé de meilleures librairies
18. Ajoute les drawers manquants (Gartley, Bat, Crab)

### Phase 6 — Cerveau & Pipeline (20 min)
19. Code `claude_brain.py`
20. Code `report_generator.py`
21. Vérifie `scanner.py` (déjà créé — adapter si besoin)

### Phase 7 — Test final (20 min)
22. Lance `python scanner.py`
23. Vérifie qu'un signal est généré
24. Ouvre `outputs/dashboard.html` dans le navigateur
25. Copie un fichier `.pine` dans TradingView → vérifier le visuel

### Phase 8 — Telegram (10 min)
26. Configure `.env` avec ton token Telegram
27. Teste l'envoi d'une alerte

---

## ✅ CRITÈRES DE SUCCÈS CE SOIR

À la fin de la session, le bot doit :
- [ ] Tourner sans erreur : `python scanner.py`
- [ ] Détecter au moins un signal sur BTC/USDT ou ETH/USDT
- [ ] Générer un fichier Pine Script lisible dans TradingView
- [ ] Afficher le dashboard HTML avec les signaux
- [ ] Envoyer une alerte Telegram (si configuré)
- [ ] Toutes les figures dessinées visuellement (pas juste les prix)

---

## 📌 STANDARDS DE CODE

- Python 3.10+
- Type hints sur toutes les fonctions
- Commentaires en français
- Chaque détecteur retourne une liste de dicts standardisée
- Chaque drawer retourne DrawingOutput avec pine_script + mql4_script
- Aucune erreur possible dans le pipeline de dessin (fallback toujours actif)
- Logs propres avec logging (pas de print brut)

---

## 🔮 MODULES FUTURS DÉJÀ PRÉVUS

Le bot est conçu pour s'étendre. À ajouter dans les prochaines sessions :
- MODULE-11 — Wyckoff (accumulation, distribution, springs)
- MODULE-12 — Smart Money Concepts (order blocks, FVG, liquidity)
- MODULE-13 — Price Action (inside bar, outside bar)
- MODULE-14 — Money Management (position sizing, Kelly criterion)
- MODULE-15 — Corrélations inter-marchés (DXY, Gold, Oil, BTC Dominance)
- MODULE-16 — Sessions de marché (London, NY, Asia timing)
- MODULE-17 — Volume Profile (POC, VAH, VAL)
