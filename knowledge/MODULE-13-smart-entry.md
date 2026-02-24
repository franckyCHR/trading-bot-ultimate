# MODULE-13 — SMART ENTRY (Entrées Multi-Confluences)
# Source : CHARLES_SmartEntry.mq4

---

## 🎯 CONCEPT

Générateur de signaux par **score de confluence** combinant :
- EMA 8/21/50 (alignement de tendance)
- RSI 14 (momentum)
- Stochastique 5/3/3 (momentum court terme)
- MACD 12/26/9 (momentum moyen terme)
- Filtre HTF H4 obligatoire

**Règle : Signal généré SEULEMENT si score ≥ 3/4 conditions remplies**

---

## 📈 CONDITIONS BUY (Score-based)

```
buyScore = 0

Condition 1 — Alignement EMA :
   SI EMA8 > EMA21 ET Close > EMA50 ALORS buyScore += 1

Condition 2 — Momentum RSI :
   SI RSI(14) > 50 ALORS buyScore += 1

Condition 3 — Momentum Stochastique :
   SI Stoch_Main > Stoch_Signal ET Stoch_Main < 80 ALORS buyScore += 1

Condition 4 — MACD Haussier :
   SI MACD_Main > MACD_Signal ALORS buyScore += 1

DÉCLENCHEUR (Trigger) :
   SI EMA8 croise au-dessus EMA21 (croisement haussier)
   ET buyScore >= 3
   ET H4_Bullish (EMA8_H4 > EMA21_H4 ET Close_H4 > EMA50_H4)
   ALORS → Générer signal BUY
```

---

## 📉 CONDITIONS SELL (Score-based)

```
sellScore = 0

Condition 1 — Alignement EMA :
   SI EMA8 < EMA21 ET Close < EMA50 ALORS sellScore += 1

Condition 2 — Momentum RSI :
   SI RSI(14) < 50 ALORS sellScore += 1

Condition 3 — Momentum Stochastique :
   SI Stoch_Main < Stoch_Signal ET Stoch_Main > 20 ALORS sellScore += 1

Condition 4 — MACD Baissier :
   SI MACD_Main < MACD_Signal ALORS sellScore += 1

DÉCLENCHEUR :
   SI EMA8 croise en-dessous EMA21 (croisement baissier)
   ET sellScore >= 3
   ET H4_Bearish (EMA8_H4 < EMA21_H4 ET Close_H4 < EMA50_H4)
   ALORS → Générer signal SELL
```

---

## 🔍 FILTRE HTF H4 (Obligatoire)

```
H4_Bullish = (EMA8_H4 > EMA21_H4) ET (Close_H4 > EMA50_H4)
H4_Bearish = (EMA8_H4 < EMA21_H4) ET (Close_H4 < EMA50_H4)

→ BUY seulement si H4_Bullish
→ SELL seulement si H4_Bearish
```

---

## 📊 PARAMÈTRES OPTIMAUX

| Indicateur | Paramètre | Valeur |
|-----------|-----------|--------|
| EMA rapide | EMA_Fast | 8 |
| EMA lente | EMA_Slow | 21 |
| EMA tendance | EMA_Trend | 50 |
| RSI | Période | 14 |
| RSI seuil BUY | | > 50 |
| RSI seuil SELL | | < 50 |
| Stochastique | K/D/Slowing | 5/3/3 |
| Stoch. surachat | | 80 |
| Stoch. survente | | 20 |
| MACD | Fast/Slow/Signal | 12/26/9 |
| Score minimum | MinConfluence | 3/4 |

---

## 🧠 INTÉGRATION DANS LE BOT

Ce module inspire l'ajout dans `IndicatorEngine` :
- EMA 8/21 à calculer en plus des EMA50/200 existants
- Score de confluence à intégrer dans `GateChecker`

**Règle d'entrée SmartEntry** :
- EMA 8 > 21 > 50 = tendance haussière forte
- EMA 8 < 21 < 50 = tendance baissière forte
- RSI > 50 = momentum bullish confirmé
- Stoch pas en surachat = pas de surachat

**Cette logique RENFORCE les 2 Portes** :
- Porte 1 (S/R) + Porte 2 (Pattern) + SmartEntry (3/4) = Signal PREMIUM ⭐⭐⭐
