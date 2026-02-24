"""
multi_timeframe.py
──────────────────
Analyse multi-timeframe automatique.
Vérifie que le 4H confirme le 1H qui confirme le 30m.
C'est ce que font les traders professionnels.
"""

from dataclasses import dataclass
from typing import Optional


# Hiérarchie des timeframes
TF_HIERARCHY = {
    "1d"  : 6,
    "4h"  : 5,
    "1h"  : 4,
    "30m" : 3,
    "15m" : 2,
    "5m"  : 1,
}

TF_PARENT = {
    "5m"  : "15m",
    "15m" : "30m",
    "30m" : "1h",
    "1h"  : "4h",
    "4h"  : "1d",
}


@dataclass
class MTFResult:
    entry_tf        : str
    trend_htf       : str          # BULLISH / BEARISH / NEUTRE sur le TF parent
    trend_htf_tf    : str          # Quel TF est le parent
    aligned         : bool         # Tendance HTF dans le même sens que le signal
    sr_confluence   : bool         # Même zone S/R présente sur HTF
    strength        : int          # 1 = signal seul | 2 = + HTF aligné | 3 = + HTF S/R
    label           : str
    blocked         : bool = False # True si HTF contre le signal (sniper mode)


class MultiTimeframeAnalyzer:
    """
    Analyse la confluence entre timeframes.
    Le signal LTF est plus fort si HTF est dans le même sens.

    Règle d'or :
    - Trade dans le sens de la tendance HTF uniquement
    - S/R présent sur 2+ TF = zone très forte
    - Signal contre HTF → ⚠️ avertissement ou blocage selon config
    """

    def __init__(self, block_counter_trend: bool = False):
        """
        block_counter_trend : si True, bloque tout signal contre la tendance HTF
        """
        self.block_counter_trend = block_counter_trend

    def analyze(self,
                signal_tf   : str,
                signal_dir  : str,
                htf_data    : dict) -> MTFResult:
        """
        signal_tf  : le timeframe du signal détecté (ex: "1h")
        signal_dir : direction du signal (LONG / SHORT)
        htf_data   : données du timeframe supérieur {
            "trend"     : "BULLISH" / "BEARISH" / "NEUTRE",
            "sr_levels" : [42000, 43500, ...],
            "price"     : 42150,
            "above_ema" : True/False,
            "qqe_dir"   : "LONG"/"SHORT"
        }
        """
        parent_tf   = TF_PARENT.get(signal_tf, "4h")
        htf_trend   = htf_data.get("trend", "NEUTRE")
        htf_sr      = htf_data.get("sr_levels", [])
        signal_price= htf_data.get("price", 0)

        # Alignement tendance
        aligned = (
            (signal_dir == "LONG"  and htf_trend == "BULLISH") or
            (signal_dir == "SHORT" and htf_trend == "BEARISH")
        )

        counter = (
            (signal_dir == "LONG"  and htf_trend == "BEARISH") or
            (signal_dir == "SHORT" and htf_trend == "BULLISH")
        )

        # Confluence S/R HTF
        sr_confluence = False
        if htf_sr and signal_price:
            for level in htf_sr:
                if abs(signal_price - level) / signal_price < 0.005:  # ±0.5%
                    sr_confluence = True
                    break

        # Score de force
        strength = 1
        if aligned:
            strength += 1
        if sr_confluence:
            strength += 1

        # Label
        if aligned and sr_confluence:
            label = f"✅✅ HTF {parent_tf} aligné + S/R confluent → SIGNAL FORT"
        elif aligned:
            label = f"✅ HTF {parent_tf} aligné ({htf_trend})"
        elif counter:
            label = f"⚠️ HTF {parent_tf} OPPOSÉ ({htf_trend}) — risque accru"
        else:
            label = f"ℹ️ HTF {parent_tf} neutre"

        return MTFResult(
            entry_tf     = signal_tf,
            trend_htf    = htf_trend,
            trend_htf_tf = parent_tf,
            aligned      = aligned,
            sr_confluence= sr_confluence,
            strength     = strength,
            label        = label,
        )

    def analyze_sniper(self,
                       signal_tf  : str,
                       signal_dir : str,
                       htf1_data  : dict,
                       htf2_data  : Optional[dict] = None) -> MTFResult:
        """
        Analyse sniper pour M15/M30 :
        - HTF1 = contexte direct (H1 pour M15/M30)
        - HTF2 = tendance de fond (H4 pour M15/M30)

        Règle :
        - HTF1 CONTRE le signal → bloqué (signal contre tendance immédiate)
        - HTF1 aligné + HTF2 aligné → signal fort ✅✅
        - HTF1 aligné + HTF2 neutre → signal valide ✅
        - HTF1 neutre → signal faible ⚠️
        """
        htf1_tf    = htf1_data.get("tf", "1h")
        htf1_trend = htf1_data.get("trend", "NEUTRE")
        htf1_sr    = htf1_data.get("sr_levels", [])
        price      = htf1_data.get("price", 0)

        htf2_tf    = htf2_data.get("tf", "4h")    if htf2_data else None
        htf2_trend = htf2_data.get("trend", "NEUTRE") if htf2_data else "NEUTRE"

        def is_aligned(direction, trend):
            return (direction == "LONG" and trend == "BULLISH") or \
                   (direction == "SHORT" and trend == "BEARISH")

        def is_counter(direction, trend):
            return (direction == "LONG" and trend == "BEARISH") or \
                   (direction == "SHORT" and trend == "BULLISH")

        h1_aligned  = is_aligned(signal_dir, htf1_trend)
        h1_counter  = is_counter(signal_dir, htf1_trend)
        h4_aligned  = is_aligned(signal_dir, htf2_trend) if htf2_tf else False
        h4_counter  = is_counter(signal_dir, htf2_trend) if htf2_tf else False

        # Confluence S/R HTF1
        sr_confluence = False
        if htf1_sr and price:
            for level in htf1_sr:
                if level and abs(price - level) / price < 0.005:
                    sr_confluence = True
                    break

        # Blocage : HTF1 CONTRE le signal
        blocked = h1_counter

        # Score
        strength = 1
        if h1_aligned:
            strength += 1
        if h4_aligned:
            strength += 1
        if sr_confluence:
            strength += 1

        # Label contextuel
        h1_icon = "✅" if h1_aligned else ("❌" if h1_counter else "➖")
        h4_icon = ("✅✅" if h4_aligned else ("❌" if h4_counter else "➖")) if htf2_tf else ""

        if blocked:
            label = f"🚫 {htf1_tf} CONTRE le signal ({htf1_trend}) — entrée bloquée"
        elif h1_aligned and h4_aligned:
            label = f"🎯 SNIPER {htf1_tf} {h1_icon} + {htf2_tf} {h4_icon} — CONTEXTE PARFAIT"
        elif h1_aligned:
            h4_str = f"| {htf2_tf}: {htf2_trend} {h4_icon}" if htf2_tf else ""
            label = f"✅ {htf1_tf} aligné ({htf1_trend}) {h4_str}"
        else:
            label = f"⚠️ {htf1_tf} neutre ({htf1_trend}) — attendre confirmation"

        return MTFResult(
            entry_tf     = signal_tf,
            trend_htf    = htf1_trend,
            trend_htf_tf = htf1_tf,
            aligned      = h1_aligned,
            sr_confluence= sr_confluence,
            strength     = strength,
            label        = label,
            blocked      = blocked,
        )

    def get_trend_from_data(self, df) -> str:
        """
        Détermine la tendance d'un dataframe OHLCV.
        Méthode simple : position par rapport à EMA 50 + EMA 200
        """
        try:
            close = df["close"]
            ema50 = close.ewm(span=50).mean().iloc[-1]
            ema200= close.ewm(span=200).mean().iloc[-1]
            price = close.iloc[-1]

            if price > ema50 > ema200:
                return "BULLISH"
            elif price < ema50 < ema200:
                return "BEARISH"
            elif price > ema200:
                return "BULLISH"
            elif price < ema200:
                return "BEARISH"
            else:
                return "NEUTRE"
        except Exception:
            return "NEUTRE"
