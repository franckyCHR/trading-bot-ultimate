# MODULE-16 — STRATÉGIE DAILY SNIPER
# Source : Trading_Sniper_MT4.pptx (Charles, inspiré de Matt)

---

## 🎯 CONCEPT SNIPER

**RÈGLE D'OR** : Ne JAMAIS utiliser le RSI seul.
Toujours confirmer avec :
1. Un niveau S/R
2. La tendance générale
3. Un indicateur de momentum (QQE ou EMA)

---

## 📊 RSI — UTILISATION AVANCÉE

### Surachat / Survente
```
RSI > 70 = ZONE SURACHAT → chercher reversal BEARISH
RSI < 30 = ZONE SURVENTE → chercher reversal BULLISH
RSI = 50 = ligne médiane (sépare bull/bear)
```

### Divergences RSI (Signal premium ⭐⭐⭐)

**Divergence BEARISH :**
```
Prix : Higher High (HH) — nouveau sommet
RSI  : Lower High (LH)  — sommet déclinant
→ VENTE avec confirmation S/R
→ C'est un signe de FAIBLESSE du mouvement haussier
```

**Divergence BULLISH :**
```
Prix : Lower Low (LL) — nouveau creux
RSI  : Higher Low (HL) — creux remontant
→ ACHAT avec confirmation S/R
→ C'est un signe de FORCE du mouvement baissier qui s'essoufle
```

**⚠️ RSI seul = 0 signal. RSI + S/R = signal valide.**

---

## 📈 EMA — RÈGLES DE TENDANCE

### EMA 20, 50, 200

| Situation | Signal |
|-----------|--------|
| EMA20 > EMA50 | Tendance HAUSSIÈRE (Golden Cross) → chercher BUY |
| EMA20 < EMA50 | Tendance BAISSIÈRE (Death Cross) → chercher SELL |
| Prix > EMA200 | Tendance long terme HAUSSIÈRE |
| Prix < EMA200 | Tendance long terme BAISSIÈRE |

**RÈGLE ABSOLUE** : Ne trader QUE dans le sens de l'EMA200.
- Prix > EMA200 = LONG uniquement
- Prix < EMA200 = SHORT uniquement

### Golden Cross et Death Cross

**Golden Cross (BULLISH) :**
```
EMA20 croise au-dessus EMA50
+ Prix > EMA200
→ Signal fort LONG
→ Attendre pullback sur EMA20 ou EMA50
```

**Death Cross (BEARISH) :**
```
EMA20 croise en-dessous EMA50
+ Prix < EMA200
→ Signal fort SHORT
→ Attendre pullback sur EMA20 ou EMA50
```

---

## 🏗️ NIVEAUX S/R — RÈGLES DU SNIPER

```
1. Minimum 2 touches sur D1 pour valider un niveau
2. Les zones ne sont PAS des prix exacts mais des ZONES
3. Un niveau n'est confirmé qu'en clôture Daily au-dessus/dessous
4. Plus le nombre de touches est élevé, plus le niveau est fort
5. Breakout confirmé = clôture Daily HORS de la zone
```

---

## 📐 STRATÉGIE DAILY SNIPER — PROCESSUS COMPLET

### Analyse Top-Down (D1 → H4 → H1/30m)

```
ÉTAPE 1 (D1) :
   - Identifier tendance principale (EMA 20/50/200)
   - Repérer zones S/R majeures
   - Repérer divergences RSI D1

ÉTAPE 2 (H4) :
   - Confirmer direction de la tendance D1
   - Identifier la zone S/R sur laquelle on va trader
   - Vérifier EMA alignment H4

ÉTAPE 3 (H1/30m) :
   - Chercher le pattern d'entrée (reversal candle, figure chartiste)
   - Vérifier QQE croisement dans le bon sens
   - Placer l'entrée, SL, TP
```

---

## 🚫 CONDITIONS "NO TRADE"

```
❌ RSI utilisé seul sans S/R
❌ Contre la tendance EMA200
❌ Pendant les actualités majeures (NFP, FOMC, BCE)
❌ Si pas de zone S/R identifiable
❌ Si pas de pattern de reversal clair
❌ FOMO (peur de rater)
❌ Revenge trading (récupérer une perte)
❌ Plus de 3 pertes dans la journée
```

---

## 🧮 GESTION DU RISQUE (SNIPER)

```
- Risque par trade : 1-2% du capital maximum
- RR minimum : 1:2 (TP = 2× SL)
- SL : derrière la zone S/R (jamais dans la zone)
- TP1 : prochain niveau S/R majeur
- TP2 : extension Fibonacci 161.8% ou niveau suivant
- Ne jamais déplacer le SL contre soi
- Partial close à TP1 puis trailing stop
```

---

## 🎯 RÉSUMÉ — CHECKLIST SNIPER

```
□ 1. Tendance D1 identifiée (EMA 20/50/200)
□ 2. Zone S/R identifiée (min. 2 touches D1)
□ 3. H4 confirme la direction
□ 4. Divergence RSI présente (bonus ⭐⭐)
□ 5. EMA alignées dans le sens du trade
□ 6. Pattern reversal sur la zone (Pin Bar, Engulfing, ETE...)
□ 7. QQE croisé dans le bon sens
□ 8. SL/TP calculés (RR ≥ 1:2)
□ 9. Pas de news majeure dans les 2h
□ 10. Pas de revenge trading / FOMO
```
