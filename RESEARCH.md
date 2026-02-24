# RESEARCH.md — Bibliothèques Sélectionnées

## Conclusions de Recherche

### A) Détection de Patterns Chartistes

**Sélectionné : Implémentation custom + scipy**
- pandas-ta v0.4.71b0 **incompatible Python 3.14** (dépendance numba)
- Implémentation manuelle avec scipy.signal.argrelextrema pour les pivots
- Avantage : contrôle total sur les seuils et la logique métier
- Reference : https://github.com/twopirllc/pandas-ta

**Chandeliers japonais** : Implémentation manuelle basée sur les ratios OHLC
- pandas-ta inclut TA-Lib CDL functions mais inaccessible sous Python 3.14
- Formules directes : wick_ratio, body_ratio, engulf detection

### B) Données de Marché Temps Réel

**Sélectionné : ccxt 4.5.40** ✅ (installé, compatible Python 3.14)
- Supporte 100+ exchanges (Binance, Bybit, Coinbase, Kraken...)
- Méthode fetch_ohlcv() standardisée
- Rate limiting automatique
- yfinance : backup pour indices/actions (incompatible Python 3.14 sans adjustments)

### C) Visualisation des Figures

**Sélectionné : Pine Script v5 généré dynamiquement**
- plotly 6.5.2 ✅ pour dashboard HTML interactif
- mplfinance 0.12.10b0 ✅ pour graphiques matplotlib
- Pine Script généré en texte = compatible TradingView directement
- MQL4 généré en texte = compatible MetaTrader 4

### D) Indicateur QQE

**Sélectionné : Implémentation manuelle Python/Pandas**
- QQE = Qualitative Quantitative Estimation (basé sur RSI lissé)
- Algorithme :
  1. RSI(14) standard
  2. Lissage RSI → SMRSI (EMA sur RSI)
  3. Calcul ATR du RSI (True Range sur RSI)
  4. Ligne rapide = SMRSI
  5. Ligne lente = SMRSI ± (ATR_RSI × facteur 4.236)
  6. Signal = croisement rapide/lente

### E) Indicateurs ADX et ATR

**Sélectionné : Implémentation manuelle Wilder's EMA**
- ADX = Average Directional Index (Wilder 1978)
- +DI, -DI calculés via True Range et Directional Movement
- Wilder's EMA = EMA avec alpha = 1/période (lissage spécifique)
- ATR = Average True Range via Wilder's EMA

---

## Résumé des Packages Installés

| Package | Version | Usage | Compatible Python 3.14 |
|---------|---------|-------|------------------------|
| ccxt | 4.5.40 | Données OHLCV | ✅ |
| numpy | latest | Calculs vectoriels | ✅ |
| scipy | 1.17.1 | Détection pivots | ✅ |
| pandas | latest | DataFrames | ✅ |
| plotly | 6.5.2 | Dashboard HTML | ✅ |
| mplfinance | 0.12.10b0 | Graphiques | ✅ |
| matplotlib | 3.10.8 | Graphiques | ✅ |
| requests | latest | Telegram API | ✅ |
| python-dotenv | 1.2.1 | Config .env | ✅ |
| schedule | 1.2.2 | Boucle 15min | ✅ |
| colorama | 0.4.6 | Terminal colors | ✅ |
| pandas-ta | 0.4.71b0 | ❌ Numba requis | ❌ (Python 3.14) |

**Stratégie** : Tous les indicateurs (QQE, ADX, RSI, ATR) sont implémentés manuellement
en Python/NumPy pour une compatibilité totale avec Python 3.14+.
