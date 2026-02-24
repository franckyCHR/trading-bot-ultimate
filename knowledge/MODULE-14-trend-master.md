# MODULE-14 — TREND MASTER (Alignement Multi-Timeframes)
# Source : CHARLES_TrendMaster.mq4

---

## 🎯 CONCEPT

Dashboard de tendance multi-timeframes qui :
- Analyse la tendance sur 4 timeframes simultanément
- Génère un signal fort si 3+ TF sont alignés
- Colorie les bougies selon la tendance

---

## 📊 DÉTECTION DE TENDANCE PAR TIMEFRAME

**Fonction GetTrend() — Appliquée à chaque TF :**
```
Pour chaque timeframe tf dans [TF_Actuel, H1, H4, D1] :

   SI EMA8[tf] > EMA21[tf] ET Close[tf] > EMA50[tf] ALORS
      Trend[tf] = "HAUSSIER"

   SINON SI EMA8[tf] < EMA21[tf] ET Close[tf] < EMA50[tf] ALORS
      Trend[tf] = "BAISSIER"

   SINON
      Trend[tf] = "NEUTRE"
```

---

## 🚦 SIGNAL FINAL

```
bullCount = 0, bearCount = 0

Pour chaque TF :
   SI Trend = "HAUSSIER" → bullCount++
   SI Trend = "BAISSIER" → bearCount++

SI bullCount >= 3 ALORS Signal = ">>> BUY FORT <<<"
SI bearCount >= 3 ALORS Signal = ">>> SELL FORT <<<"
SINON               Signal = "ATTENDRE"
```

**Règle** : Signal valide UNIQUEMENT si **≥ 3 timeframes alignés dans le même sens**

---

## 🖥️ DASHBOARD (4 lignes + Signal)

```
┌────────────────────────────────┐
│ TF ACTUEL : HAUSSIER / BAISSIER / NEUTRE │
│ H1       : HAUSSIER / BAISSIER / NEUTRE │
│ H4       : HAUSSIER / BAISSIER / NEUTRE │
│ D1       : HAUSSIER / BAISSIER / NEUTRE │
│ SIGNAL   : >>> BUY FORT <<<   │
└────────────────────────────────┘
```

---

## 🎨 COLORATION DES BOUGIES

| Couleur | Tendance |
|---------|----------|
| 🟢 Vert | Haussière (EMA8 > EMA21 ET Close > EMA50) |
| 🔴 Rouge | Baissière (EMA8 < EMA21 ET Close < EMA50) |
| ⚫ Gris | Neutre (aucune condition claire) |

---

## 🧠 INTÉGRATION DANS LE BOT

### Correspondance avec `MultiTimeframeAnalyzer`

Le bot analyse déjà les HTF. La logique TrendMaster **renforce** cette analyse :

**Signal qualité PREMIUM si** :
```
TF courant (30m/1h/4h) = HAUSSIER/BAISSIER
+ H4 aligné dans le même sens
+ D1 aligné dans le même sens
→ 3/3 TF alignés = signal maximum confiance
```

**Intégration possible dans `gate_checker.py`** :
- Ajouter bonus si 3 TF alignés
- `htf_aligned = True` déjà calculé — étendre à D1

### Timeframes recommandées par signal
| Signal TF | HTF à vérifier | HTF2 |
|-----------|----------------|------|
| 30m | 1h | 4h |
| 1h | 4h | D1 |
| 4h | D1 | W1 |

**Règle or** : Ne jamais aller contre la tendance H4 + D1 combinées.
