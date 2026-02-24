"""
entry_calculator.py
───────────────────
Calcule ENTRÉE / SL / TP1 / TP2 pour chaque figure.
Chaque figure a sa propre formule mathématique précise.
Retourne toujours 4 prix exacts prêts à afficher sur le graphique.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class EntryResult:
    pattern     : str
    direction   : str       # LONG / SHORT
    entry       : float     # Prix d'entrée exact
    stop_loss   : float     # Prix invalidation
    tp1         : float     # 50% objectif
    tp2         : float     # Objectif complet
    rr_ratio    : float     # Risk/Reward ratio (tp2)
    description : str       # Explication du calcul


class EntryCalculator:

    def calculate(self, signal: dict) -> EntryResult:
        pattern = signal.get("pattern", "").upper()
        atr     = signal.get("atr", 0)

        calculators = {
            "ETE"                  : self._ete_bearish,
            "HEAD_SHOULDERS"       : self._ete_bearish,
            "ETE_INVERSE"          : self._ete_bullish,
            "INVERSE_HEAD_SHOULDERS": self._ete_bullish,
            "DOUBLE_TOP"           : self._double_top,
            "DOUBLE_BOTTOM"        : self._double_bottom,
            "BULL_FLAG"            : self._bull_flag,
            "DRAPEAU_HAUSSIER"     : self._bull_flag,
            "BEAR_FLAG"            : self._bear_flag,
            "DRAPEAU_BAISSIER"     : self._bear_flag,
            "PENNANT"              : self._pennant,
            "FANION"               : self._pennant,
            "BISEAU_ASCENDANT"     : self._rising_wedge,
            "RISING_WEDGE"         : self._rising_wedge,
            "BISEAU_DESCENDANT"    : self._falling_wedge,
            "FALLING_WEDGE"        : self._falling_wedge,
            "TRIANGLE_ASCENDANT"   : self._ascending_triangle,
            "ASCENDING_TRIANGLE"   : self._ascending_triangle,
            "TRIANGLE_DESCENDANT"  : self._descending_triangle,
            "DESCENDING_TRIANGLE"  : self._descending_triangle,
            "TRIANGLE_SYMETRIQUE"  : self._symmetric_triangle,
            "SYMMETRIC_TRIANGLE"   : self._symmetric_triangle,
            "BUTTERFLY"            : self._butterfly,
            "BUTTERFLY_BULLISH"    : self._butterfly,
            "BUTTERFLY_BEARISH"    : self._butterfly,
            "SHARK"                : self._shark,
            "SHARK_BULLISH"        : self._shark,
            "SHARK_BEARISH"        : self._shark,
            "GARTLEY"              : self._gartley,
            "BAT"                  : self._bat,
            "CRAB"                 : self._crab,
            "COMPRESSION"          : self._compression,
            "ZONE_COMPRESSION"     : self._compression,
        }

        # Chandeliers reversal — tous traitables par la même méthode
        reversal_candles = {
            "PIN_BAR_BULLISH", "PIN_BAR_BEARISH", "MARTEAU", "HAMMER",
            "ETOILE_FILANTE", "SHOOTING_STAR", "BULLISH_ENGULFING",
            "BEARISH_ENGULFING", "MORNING_STAR", "EVENING_STAR",
            "HARAMI_BULLISH", "HARAMI_BEARISH", "DOJI"
        }

        if pattern in reversal_candles:
            return self._reversal_candle(signal)

        if pattern in calculators:
            return calculators[pattern](signal)

        # Fallback générique
        return self._generic_fallback(signal)

    # ──────────────────────────────────────────────────────────────
    # FIGURES CHARTISTES
    # ──────────────────────────────────────────────────────────────

    def _ete_bearish(self, s: dict) -> EntryResult:
        neckline = s["neckline"]
        tete     = s["head_price"]
        epaule_d = s["right_shoulder_price"]
        atr      = s.get("atr", abs(tete - neckline) * 0.1)
        hauteur  = tete - neckline
        entry    = neckline
        sl       = epaule_d + atr * 0.5
        tp1      = neckline - hauteur * 0.5
        tp2      = neckline - hauteur
        return EntryResult("ETE", "SHORT", entry, sl, tp1, tp2,
                           self._rr(entry, sl, tp2),
                           f"ETE Bearish | Neckline={round(neckline,2)} | Hauteur={round(hauteur,2)}")

    def _ete_bullish(self, s: dict) -> EntryResult:
        neckline = s["neckline"]
        tete     = s["head_price"]
        epaule_d = s["right_shoulder_price"]
        atr      = s.get("atr", abs(neckline - tete) * 0.1)
        hauteur  = neckline - tete
        entry    = neckline
        sl       = epaule_d - atr * 0.5
        tp1      = neckline + hauteur * 0.5
        tp2      = neckline + hauteur
        return EntryResult("ETE_INVERSE", "LONG", entry, sl, tp1, tp2,
                           self._rr(entry, sl, tp2),
                           f"ETE Inversé Bullish | Neckline={round(neckline,2)}")

    def _double_top(self, s: dict) -> EntryResult:
        top1    = s["top1_price"]
        top2    = s["top2_price"]
        valley  = s["valley"]
        atr     = s.get("atr", 0)
        hauteur = max(top1, top2) - valley
        entry   = valley
        sl      = max(top1, top2) + atr * 0.5
        tp1     = valley - hauteur * 0.5
        tp2     = valley - hauteur
        return EntryResult("DOUBLE_TOP", "SHORT", entry, sl, tp1, tp2,
                           self._rr(entry, sl, tp2),
                           f"Double Top M | Tops={round(max(top1,top2),2)} | Valley={round(valley,2)}")

    def _double_bottom(self, s: dict) -> EntryResult:
        bot1    = s["bot1_price"]
        bot2    = s["bot2_price"]
        peak    = s["peak"]
        atr     = s.get("atr", 0)
        hauteur = peak - min(bot1, bot2)
        entry   = peak
        sl      = min(bot1, bot2) - atr * 0.5
        tp1     = peak + hauteur * 0.5
        tp2     = peak + hauteur
        return EntryResult("DOUBLE_BOTTOM", "LONG", entry, sl, tp1, tp2,
                           self._rr(entry, sl, tp2),
                           f"Double Bottom W | Bots={round(min(bot1,bot2),2)} | Peak={round(peak,2)}")

    def _bull_flag(self, s: dict) -> EntryResult:
        mat_high   = s["mat_high"]
        mat_low    = s["mat_low"]
        flag_high  = s["flag_canal_high"]
        flag_low   = s["flag_canal_low"]
        atr        = s.get("atr", 0)
        hauteur    = mat_high - mat_low
        entry      = flag_high
        sl         = flag_low - atr * 0.3
        tp1        = entry + hauteur * 0.5
        tp2        = entry + hauteur
        return EntryResult("BULL_FLAG", "LONG", entry, sl, tp1, tp2,
                           self._rr(entry, sl, tp2),
                           f"Bull Flag | Mât={round(hauteur,2)} | Canal {round(flag_low,2)}→{round(flag_high,2)}")

    def _bear_flag(self, s: dict) -> EntryResult:
        mat_high  = s["mat_high"]
        mat_low   = s["mat_low"]
        flag_high = s["flag_canal_high"]
        flag_low  = s["flag_canal_low"]
        atr       = s.get("atr", 0)
        hauteur   = mat_high - mat_low
        entry     = flag_low
        sl        = flag_high + atr * 0.3
        tp1       = entry - hauteur * 0.5
        tp2       = entry - hauteur
        return EntryResult("BEAR_FLAG", "SHORT", entry, sl, tp1, tp2,
                           self._rr(entry, sl, tp2), "Bear Flag")

    def _pennant(self, s: dict) -> EntryResult:
        direction   = s.get("direction", "LONG")
        mat_height  = s.get("mat_height", 0)
        breakout    = s.get("breakout_price", s.get("entry", 0))
        atr         = s.get("atr", 0)
        entry = breakout
        if direction == "LONG":
            sl  = breakout - atr * 1.0
            tp1 = entry + mat_height * 0.5
            tp2 = entry + mat_height
        else:
            sl  = breakout + atr * 1.0
            tp1 = entry - mat_height * 0.5
            tp2 = entry - mat_height
        return EntryResult("PENNANT", direction, entry, sl, tp1, tp2,
                           self._rr(entry, sl, tp2), f"Fanion {direction}")

    def _rising_wedge(self, s: dict) -> EntryResult:
        res_end    = s["resistance_end"]
        sup_end    = s["support_end"]
        res_start  = s["resistance_start"]
        sup_start  = s["support_start"]
        atr        = s.get("atr", 0)
        largeur    = res_start - sup_start
        entry      = sup_end
        sl         = res_end + atr * 0.5
        tp1        = entry - largeur * 0.5
        tp2        = entry - largeur
        return EntryResult("BISEAU_ASCENDANT", "SHORT", entry, sl, tp1, tp2,
                           self._rr(entry, sl, tp2), "Biseau Ascendant Bearish")

    def _falling_wedge(self, s: dict) -> EntryResult:
        res_end   = s["resistance_end"]
        sup_end   = s["support_end"]
        res_start = s["resistance_start"]
        sup_start = s["support_start"]
        atr       = s.get("atr", 0)
        largeur   = res_start - sup_start
        entry     = res_end
        sl        = sup_end - atr * 0.5
        tp1       = entry + largeur * 0.5
        tp2       = entry + largeur
        return EntryResult("BISEAU_DESCENDANT", "LONG", entry, sl, tp1, tp2,
                           self._rr(entry, sl, tp2), "Biseau Descendant Bullish")

    def _ascending_triangle(self, s: dict) -> EntryResult:
        res     = s["resistance_level"]
        sup_s   = s["support_start"]
        sup_e   = s.get("support_end", sup_s)
        atr     = s.get("atr", 0)
        hauteur = res - sup_s
        entry   = res
        sl      = sup_e - atr * 0.3
        tp1     = entry + hauteur * 0.5
        tp2     = entry + hauteur
        return EntryResult("TRIANGLE_ASCENDANT", "LONG", entry, sl, tp1, tp2,
                           self._rr(entry, sl, tp2), f"Triangle Ascendant | Résistance={round(res,2)}")

    def _descending_triangle(self, s: dict) -> EntryResult:
        sup     = s["support_level"]
        res_s   = s["resistance_start"]
        res_e   = s.get("resistance_end", res_s)
        atr     = s.get("atr", 0)
        hauteur = res_s - sup
        entry   = sup
        sl      = res_e + atr * 0.3
        tp1     = entry - hauteur * 0.5
        tp2     = entry - hauteur
        return EntryResult("TRIANGLE_DESCENDANT", "SHORT", entry, sl, tp1, tp2,
                           self._rr(entry, sl, tp2), f"Triangle Descendant | Support={round(sup,2)}")

    def _symmetric_triangle(self, s: dict) -> EntryResult:
        direction = s.get("direction", "LONG")
        res_e     = s["resistance_end"]
        sup_e     = s["support_end"]
        res_s     = s["resistance_start"]
        sup_s     = s["support_start"]
        atr       = s.get("atr", 0)
        base      = res_s - sup_s
        if direction == "LONG":
            entry = res_e
            sl    = sup_e - atr * 0.3
            tp1   = entry + base * 0.5
            tp2   = entry + base
        else:
            entry = sup_e
            sl    = res_e + atr * 0.3
            tp1   = entry - base * 0.5
            tp2   = entry - base
        return EntryResult("TRIANGLE_SYMETRIQUE", direction, entry, sl, tp1, tp2,
                           self._rr(entry, sl, tp2), "Triangle Symétrique — cassure confirmée")

    # ──────────────────────────────────────────────────────────────
    # HARMONIQUES
    # ──────────────────────────────────────────────────────────────

    def _butterfly(self, s: dict) -> EntryResult:
        direction = s["direction"]
        d_p       = s["D_price"]
        c_p       = s["C_price"]
        a_p       = s["A_price"]
        x_p       = s["X_price"]
        xa        = abs(x_p - a_p)
        atr       = s.get("atr", xa * 0.05)
        entry     = d_p
        if direction == "LONG":
            sl  = d_p - atr * 2
            tp1 = d_p + abs(d_p - c_p)
            tp2 = d_p + abs(d_p - a_p)
        else:
            sl  = d_p + atr * 2
            tp1 = d_p - abs(d_p - c_p)
            tp2 = d_p - abs(d_p - a_p)
        return EntryResult("BUTTERFLY", direction, entry, sl, tp1, tp2,
                           self._rr(entry, sl, tp2), f"🦋 Butterfly {direction} | PRZ={round(d_p,2)}")

    def _shark(self, s: dict) -> EntryResult:
        direction = s["direction"]
        c_p       = s["C_price"]
        b_p       = s["B_price"]
        a_p       = s["A_price"]
        x_p       = s["X_price"]
        xa        = abs(x_p - a_p)
        atr       = s.get("atr", xa * 0.05)
        entry     = c_p
        if direction == "LONG":
            sl  = c_p - atr * 2
            tp1 = c_p + abs(c_p - b_p)
            tp2 = c_p + abs(c_p - a_p)
        else:
            sl  = c_p + atr * 2
            tp1 = c_p - abs(c_p - b_p)
            tp2 = c_p - abs(c_p - a_p)
        return EntryResult("SHARK", direction, entry, sl, tp1, tp2,
                           self._rr(entry, sl, tp2), f"🦈 Shark {direction} | Entrée C={round(c_p,2)}")

    def _gartley(self, s: dict) -> EntryResult:
        direction = s["direction"]
        d_p = s["D_price"]
        c_p = s["C_price"]
        b_p = s["B_price"]
        x_p = s["X_price"]
        atr = s.get("atr", abs(x_p - d_p) * 0.05)
        entry = d_p
        if direction == "LONG":
            sl  = x_p - atr
            tp1 = d_p + abs(d_p - c_p)
            tp2 = d_p + abs(d_p - b_p)
        else:
            sl  = x_p + atr
            tp1 = d_p - abs(d_p - c_p)
            tp2 = d_p - abs(d_p - b_p)
        return EntryResult("GARTLEY", direction, entry, sl, tp1, tp2,
                           self._rr(entry, sl, tp2), f"Gartley {direction}")

    def _bat(self, s: dict) -> EntryResult:
        direction = s["direction"]
        d_p = s["D_price"]
        c_p = s["C_price"]
        a_p = s["A_price"]
        x_p = s["X_price"]
        atr = s.get("atr", abs(x_p - d_p) * 0.03)
        entry = d_p
        if direction == "LONG":
            sl  = x_p - atr
            tp1 = d_p + abs(d_p - c_p)
            tp2 = d_p + abs(d_p - a_p)
        else:
            sl  = x_p + atr
            tp1 = d_p - abs(d_p - c_p)
            tp2 = d_p - abs(d_p - a_p)
        return EntryResult("BAT", direction, entry, sl, tp1, tp2,
                           self._rr(entry, sl, tp2), f"🦇 Bat {direction}")

    def _crab(self, s: dict) -> EntryResult:
        direction = s["direction"]
        d_p = s["D_price"]
        c_p = s["C_price"]
        b_p = s["B_price"]
        x_p = s["X_price"]
        atr = s.get("atr", abs(x_p - d_p) * 0.03)
        entry = d_p
        if direction == "LONG":
            sl  = d_p - atr * 1.5
            tp1 = d_p + abs(d_p - c_p)
            tp2 = d_p + abs(d_p - b_p)
        else:
            sl  = d_p + atr * 1.5
            tp1 = d_p - abs(d_p - c_p)
            tp2 = d_p - abs(d_p - b_p)
        return EntryResult("CRAB", direction, entry, sl, tp1, tp2,
                           self._rr(entry, sl, tp2), f"🦞 Crab {direction}")

    # ──────────────────────────────────────────────────────────────
    # COMPRESSION & REVERSAL
    # ──────────────────────────────────────────────────────────────

    def _compression(self, s: dict) -> EntryResult:
        direction   = s.get("direction", "LONG")
        high_zone   = s["compression_high"]
        low_zone    = s["compression_low"]
        amplitude   = high_zone - low_zone
        atr         = s.get("atr", amplitude * 0.2)
        if direction == "LONG":
            entry = high_zone
            sl    = low_zone - atr * 0.3
            tp1   = entry + amplitude
            tp2   = entry + amplitude * 2
        else:
            entry = low_zone
            sl    = high_zone + atr * 0.3
            tp1   = entry - amplitude
            tp2   = entry - amplitude * 2
        return EntryResult("COMPRESSION", direction, entry, sl, tp1, tp2,
                           self._rr(entry, sl, tp2),
                           f"⚡ Compression {direction} | Amplitude={round(amplitude,2)}")

    def _reversal_candle(self, s: dict) -> EntryResult:
        direction = s.get("direction", "LONG")
        close     = s["close"]
        high      = s["high"]
        low       = s["low"]
        atr       = s.get("atr", abs(high - low))
        pattern   = s.get("pattern", "REVERSAL")
        if direction == "LONG":
            entry = close
            sl    = low - atr * 0.3
            tp1   = entry + (entry - sl)
            tp2   = entry + (entry - sl) * 2
        else:
            entry = close
            sl    = high + atr * 0.3
            tp1   = entry - (sl - entry)
            tp2   = entry - (sl - entry) * 2
        return EntryResult(pattern, direction, entry, sl, tp1, tp2,
                           self._rr(entry, sl, tp2),
                           f"Reversal Candle {pattern} {direction} | RR 1:{round(self._rr(entry,sl,tp2),1)}")

    def _generic_fallback(self, s: dict) -> EntryResult:
        direction = s.get("direction", "LONG")
        entry     = s.get("entry", s.get("close", 0))
        atr       = s.get("atr", entry * 0.005)
        pattern   = s.get("pattern", "UNKNOWN")
        if direction == "LONG":
            sl  = entry - atr * 2
            tp1 = entry + atr * 2
            tp2 = entry + atr * 4
        else:
            sl  = entry + atr * 2
            tp1 = entry - atr * 2
            tp2 = entry - atr * 4
        return EntryResult(pattern, direction, entry, sl, tp1, tp2,
                           self._rr(entry, sl, tp2),
                           f"[FALLBACK] {pattern} — calcul générique")

    def _rr(self, entry: float, sl: float, tp: float) -> float:
        risk   = abs(entry - sl)
        reward = abs(tp - entry)
        if risk == 0:
            return 0
        return round(reward / risk, 2)
