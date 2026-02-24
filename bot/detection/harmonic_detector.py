"""
Détection des figures harmoniques (Butterfly, Shark, Gartley, Bat, Crab).
Utilise les ratios de Fibonacci stricts : B+C+D doivent tous être validés.
"""

import logging
import itertools
import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
from typing import Optional

logger = logging.getLogger(__name__)


class HarmonicDetector:
    """
    Détecte les figures harmoniques XABCD sur les 100 dernières bougies.

    Règle absolue : JAMAIS de signal sans B+C+D validés (ratios Fibonacci stricts).

    Figures supportées :
      - Butterfly Bullish / Bearish
      - Shark Bullish / Bearish
      - Gartley Bullish / Bearish
      - Bat Bullish / Bearish
      - Crab Bullish / Bearish
    """

    # Tolérance par défaut sur les ratios Fibonacci (±5%)
    _DEFAULT_TOLERANCE = 0.05

    # ------------------------------------------------------------------ #
    #  Méthode publique principale                                         #
    # ------------------------------------------------------------------ #

    def detect(self, df: pd.DataFrame, sr_zones: list) -> list[dict]:
        """
        Lance la détection de toutes les figures harmoniques.

        Args:
            df        : DataFrame OHLCV (colonnes : open, high, low, close, volume)
            sr_zones  : Liste des zones S/R issues du sr_detector
                        (ex : [{"price": 42000, "type": "resistance"}, ...])

        Returns:
            Liste de dicts de signaux harmoniques (clarity >= 2 uniquement).
        """
        if len(df) < 30:
            logger.warning(
                "Pas assez de bougies pour la détection harmonique (%d < 30)", len(df)
            )
            return []

        # Travailler sur les 100 dernières bougies
        df_slice = df.tail(100).copy().reset_index(drop=True)

        # Calcul de l'ATR
        atr_value = self._compute_atr(df_slice, period=14)

        # Extraction du zigzag (20 derniers points)
        zigzag = self._build_zigzag(df_slice, order=3)
        if len(zigzag) < 5:
            logger.debug("Zigzag insuffisant (%d points < 5)", len(zigzag))
            return []

        signals: list[dict] = []

        # Tester toutes les combinaisons de 5 points consécutifs du zigzag
        for start in range(len(zigzag) - 4):
            xabcd = zigzag[start : start + 5]

            for detector_fn in [
                self._check_butterfly,
                self._check_shark,
                self._check_gartley,
                self._check_bat,
                self._check_crab,
            ]:
                try:
                    result = detector_fn(xabcd, atr_value)
                    if result:
                        result.setdefault("reversal_candle", False)
                        result.setdefault("price", float(df_slice["close"].iloc[-1]))
                        result.setdefault("atr", round(atr_value, 4))

                        # Bonus de clarté si S/R proche du point D
                        result["pattern_clarity"] = self._compute_clarity(
                            result, sr_zones, atr_value
                        )

                        if result["pattern_clarity"] >= 2:
                            signals.append(result)
                            logger.info(
                                "Harmonique détectée : %s | direction=%s | clarity=%d",
                                result["pattern"],
                                result["direction"],
                                result["pattern_clarity"],
                            )
                except Exception as exc:
                    logger.debug(
                        "Erreur dans %s : %s", detector_fn.__name__, exc, exc_info=True
                    )

        return signals

    # ------------------------------------------------------------------ #
    #  Helpers internes                                                    #
    # ------------------------------------------------------------------ #

    def _compute_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calcule l'ATR avec la méthode EMA de Wilder (identique au PatternDetector).

        TR = max(H-L, |H-prev_close|, |L-prev_close|)
        ATR = Wilder EMA(TR, 14)
        """
        highs  = df["high"].values
        lows   = df["low"].values
        closes = df["close"].values

        tr_values = []
        for i in range(1, len(df)):
            hl  = highs[i] - lows[i]
            hpc = abs(highs[i] - closes[i - 1])
            lpc = abs(lows[i]  - closes[i - 1])
            tr_values.append(max(hl, hpc, lpc))

        if len(tr_values) < period:
            return float(np.mean(tr_values)) if tr_values else 0.0

        atr = float(np.mean(tr_values[:period]))
        for tr in tr_values[period:]:
            atr = (atr * (period - 1) + tr) / period

        return atr

    def _build_zigzag(self, df: pd.DataFrame, order: int = 3) -> list[dict]:
        """
        Construit une séquence zigzag alternée haut/bas.

        Étapes :
          1. Trouver les pivots hauts et bas avec argrelextrema (order=3).
          2. Fusionner dans une séquence chronologique.
          3. S'assurer de l'alternance haut/bas (garder le plus extrême en cas de doublon).
          4. Retourner les 20 derniers points.

        Chaque point du zigzag est un dict :
          {"idx": int, "price": float, "type": "high" | "low"}
        """
        highs_prices = df["high"].values
        lows_prices  = df["low"].values

        highs_idx = argrelextrema(highs_prices, np.greater, order=order)[0]
        lows_idx  = argrelextrema(lows_prices,  np.less,    order=order)[0]

        # Construire la liste brute de pivots triée par indice
        raw_pivots = []
        for idx in highs_idx:
            raw_pivots.append({"idx": int(idx), "price": float(highs_prices[idx]), "type": "high"})
        for idx in lows_idx:
            raw_pivots.append({"idx": int(idx), "price": float(lows_prices[idx]), "type": "low"})

        raw_pivots.sort(key=lambda p: p["idx"])

        if not raw_pivots:
            return []

        # Garantir l'alternance haut/bas
        zigzag: list[dict] = [raw_pivots[0]]
        for pivot in raw_pivots[1:]:
            last = zigzag[-1]
            if pivot["type"] == last["type"]:
                # Même type consécutif : garder le plus extrême
                if pivot["type"] == "high" and pivot["price"] > last["price"]:
                    zigzag[-1] = pivot
                elif pivot["type"] == "low" and pivot["price"] < last["price"]:
                    zigzag[-1] = pivot
            else:
                zigzag.append(pivot)

        # Retourner les 20 derniers points
        return zigzag[-20:]

    def _check_ratio(
        self, actual: float, expected: float, tolerance: float = _DEFAULT_TOLERANCE
    ) -> bool:
        """
        Vérifie si un ratio réel est proche d'un ratio Fibonacci attendu.

        Args:
            actual    : ratio calculé
            expected  : ratio Fibonacci cible
            tolerance : tolérance relative (défaut 5%)

        Returns:
            True si |actual - expected| / expected <= tolerance
        """
        if expected == 0:
            return False
        return abs(actual - expected) / expected <= tolerance

    def _check_ratio_range(
        self, actual: float, low: float, high: float
    ) -> bool:
        """
        Vérifie si un ratio est dans une plage [low, high].

        Args:
            actual : ratio calculé
            low    : borne inférieure
            high   : borne supérieure

        Returns:
            True si low <= actual <= high
        """
        return low <= actual <= high

    def _compute_ratios(self, x: float, a: float, b: float, c: float, d: float) -> dict:
        """
        Calcule les ratios XABCD classiques.

        Returns:
            dict avec clés : AB_XA, BC_AB, CD_BC, XD_XA
            (None si division par zéro)
        """
        xa = abs(a - x)
        ab = abs(b - a)
        bc = abs(c - b)
        cd = abs(d - c)
        xd = abs(d - x)

        return {
            "AB_XA": ab / xa if xa != 0 else None,
            "BC_AB": bc / ab if ab != 0 else None,
            "CD_BC": cd / bc if bc != 0 else None,
            "XD_XA": xd / xa if xa != 0 else None,
            "xa": xa,
            "ab": ab,
            "bc": bc,
            "cd": cd,
            "xd": xd,
        }

    def _compute_clarity(
        self, signal: dict, sr_zones: list, atr: float
    ) -> int:
        """
        Attribue un score de clarté final.

        Règles :
          - Commence à 2 (harmonique validée = moyen par défaut).
          - +1 si une zone S/R est dans un rayon de 1 ATR autour du point D.
          - Maximum = 3.
        """
        clarity = signal.get("pattern_clarity", 2)

        d_price = signal.get("D", signal.get("price", 0.0))
        for zone in sr_zones:
            zone_price = zone.get("price", zone) if isinstance(zone, dict) else float(zone)
            if abs(zone_price - d_price) <= atr:
                clarity = min(clarity + 1, 3)
                break

        return clarity

    def _build_signal(
        self,
        pattern: str,
        direction: str,
        xabcd: list[dict],
        atr: float,
        extra: dict = None,
    ) -> dict:
        """
        Construit le dict de signal standardisé.

        Args:
            pattern   : nom de la figure (ex : "BUTTERFLY_BULLISH")
            direction : "LONG" ou "SHORT"
            xabcd     : liste de 5 points [{idx, price, type}, ...]
            atr       : valeur ATR
            extra     : clés supplémentaires optionnelles

        Returns:
            dict de signal complet
        """
        x, a, b, c, d = [p["price"] for p in xabcd]
        x_idx, a_idx, b_idx, c_idx, d_idx = [p.get("idx", 0) for p in xabcd]
        signal = {
            "pattern":         pattern,
            "direction":       direction,
            "pattern_clarity": 2,
            "reversal_candle": False,
            "price":           d,
            "atr":             round(atr, 4),
            # Clés pour entry_calculator (format _price)
            "X_price": round(x, 4),
            "A_price": round(a, 4),
            "B_price": round(b, 4),
            "C_price": round(c, 4),
            "D_price": round(d, 4),
            # Clés pour harmonic_drawers (format _bar = indice de bougie)
            "X_bar": int(x_idx),
            "A_bar": int(a_idx),
            "B_bar": int(b_idx),
            "C_bar": int(c_idx),
            "D_bar": int(d_idx),
            # Alias courts (compatibilité)
            "X": round(x, 4),
            "A": round(a, 4),
            "B": round(b, 4),
            "C": round(c, 4),
            "D": round(d, 4),
            "description":     f"{pattern} validé — D={d:.2f} (PRZ)",
        }
        if extra:
            signal.update(extra)
        return signal

    # ------------------------------------------------------------------ #
    #  Vérificateurs harmoniques                                           #
    # ------------------------------------------------------------------ #

    def _check_butterfly(
        self, xabcd: list[dict], atr: float
    ) -> Optional[dict]:
        """
        Butterfly Bullish / Bearish.

        Ratios :
          AB/XA = 0.786 (±5%)
          BC/AB = 0.382 à 0.886
          CD/BC = 1.618 à 2.618
          XD/XA = 1.272 à 1.618

        Bullish : D < X (D plus bas que X)
        Bearish : D > X
        """
        x, a, b, c, d = [p["price"] for p in xabcd]
        ratios = self._compute_ratios(x, a, b, c, d)

        if any(v is None for v in ratios.values()):
            return None

        ab_xa = ratios["AB_XA"]
        bc_ab = ratios["BC_AB"]
        cd_bc = ratios["CD_BC"]
        xd_xa = ratios["XD_XA"]

        # Validation des 3 ratios obligatoires (B, C, D)
        b_ok = self._check_ratio(ab_xa, 0.786)
        c_ok = self._check_ratio_range(bc_ab, 0.382, 0.886)
        d_cd_ok = self._check_ratio_range(cd_bc, 1.618, 2.618)
        d_xd_ok = self._check_ratio_range(xd_xa, 1.272, 1.618)

        if not (b_ok and c_ok and d_cd_ok and d_xd_ok):
            return None

        # Déterminer la direction
        if d < x:
            pattern   = "BUTTERFLY_BULLISH"
            direction = "LONG"
        elif d > x:
            pattern   = "BUTTERFLY_BEARISH"
            direction = "SHORT"
        else:
            return None

        logger.debug(
            "Butterfly — AB/XA=%.3f BC/AB=%.3f CD/BC=%.3f XD/XA=%.3f",
            ab_xa, bc_ab, cd_bc, xd_xa,
        )

        return self._build_signal(pattern, direction, xabcd, atr, {
            "AB_XA": round(ab_xa, 4),
            "BC_AB": round(bc_ab, 4),
            "CD_BC": round(cd_bc, 4),
            "XD_XA": round(xd_xa, 4),
        })

    def _check_shark(
        self, xabcd: list[dict], atr: float
    ) -> Optional[dict]:
        """
        Shark Bullish / Bearish.

        Le Shark utilise un pattern O-X-A-B-C (5 points), l'entrée est au point C.
        On mappe : O=X, X=A, A=B, B=C, C=D dans notre séquence XABCD.

        Ratios (relatifs aux points O-X-A-B-C renommés) :
          XA/OX = 1.130 à 1.618   (= AB/XA dans notre mapping)
          AB/XA = 1.618 à 2.240   (= BC/AB dans notre mapping)
          BC/OX = 0.886 à 1.130   (harmonie avec O = XD/XA dans notre mapping)

        Bullish : C (notre D) est plus bas que la zone O-X (notre X-A).
        """
        o, x, a, b, c = [p["price"] for p in xabcd]  # renommage pour la clarté

        ox = abs(x - o)
        xa = abs(a - x)
        ab = abs(b - a)
        bc = abs(c - b)
        oc = abs(c - o)

        if ox == 0 or xa == 0 or ab == 0 or bc == 0:
            return None

        xa_ox = xa / ox   # XA/OX
        ab_xa = ab / xa   # AB/XA
        bc_ox = bc / ox   # BC/OX (harmonie avec O)

        # Validation des 3 ratios obligatoires (B, C = points b et c)
        b_ok  = self._check_ratio_range(xa_ox, 1.130, 1.618)
        c_ok  = self._check_ratio_range(ab_xa, 1.618, 2.240)
        d_ok  = self._check_ratio_range(bc_ox, 0.886, 1.130)

        if not (b_ok and c_ok and d_ok):
            return None

        # Déterminer la direction selon la position de C par rapport à la zone O-X
        ox_min = min(o, x)
        ox_max = max(o, x)

        if c < ox_min:
            pattern   = "SHARK_BULLISH"
            direction = "LONG"
        elif c > ox_max:
            pattern   = "SHARK_BEARISH"
            direction = "SHORT"
        else:
            return None

        logger.debug(
            "Shark — XA/OX=%.3f AB/XA=%.3f BC/OX=%.3f",
            xa_ox, ab_xa, bc_ox,
        )

        # Construire le signal avec les 5 points originaux (O=X, X=A, A=B, B=C, C=D)
        o_idx = xabcd[0].get("idx", 0)
        x_idx = xabcd[1].get("idx", 0)
        a_idx = xabcd[2].get("idx", 0)
        b_idx = xabcd[3].get("idx", 0)
        c_idx = xabcd[4].get("idx", 0)
        return {
            "pattern":         pattern,
            "direction":       direction,
            "pattern_clarity": 2,
            "reversal_candle": False,
            "price":           round(c, 4),
            "atr":             round(atr, 4),
            # Clés pour entry_calculator
            "X_price": round(o, 4),
            "A_price": round(x, 4),
            "B_price": round(a, 4),
            "C_price": round(b, 4),
            "D_price": round(c, 4),
            # Clés pour drawers
            "X_bar": int(o_idx),
            "A_bar": int(x_idx),
            "B_bar": int(a_idx),
            "C_bar": int(b_idx),
            "D_bar": int(c_idx),
            # Alias point O pour SharkDrawer (5 points : O→X→A→B→C)
            "O_bar":   int(o_idx),
            "O_price": round(o, 4),
            # Alias courts
            "X": round(o, 4),
            "A": round(x, 4),
            "B": round(a, 4),
            "C": round(b, 4),
            "D": round(c, 4),
            "XA_OX": round(xa_ox, 4),
            "AB_XA": round(ab_xa, 4),
            "BC_OX": round(bc_ox, 4),
            "description": f"{pattern} validé — C={c:.2f} (PRZ)",
        }

    def _check_gartley(
        self, xabcd: list[dict], atr: float
    ) -> Optional[dict]:
        """
        Gartley Bullish / Bearish.

        Ratios :
          AB/XA = 0.618 (±5%)
          BC/AB = 0.382 à 0.886
          CD/BC = 1.272 à 1.618
          XD/XA = 0.786 (±5%)

        Bullish : D < X
        Bearish : D > X
        """
        x, a, b, c, d = [p["price"] for p in xabcd]
        ratios = self._compute_ratios(x, a, b, c, d)

        if any(v is None for v in ratios.values()):
            return None

        ab_xa = ratios["AB_XA"]
        bc_ab = ratios["BC_AB"]
        cd_bc = ratios["CD_BC"]
        xd_xa = ratios["XD_XA"]

        b_ok    = self._check_ratio(ab_xa, 0.618)
        c_ok    = self._check_ratio_range(bc_ab, 0.382, 0.886)
        d_cd_ok = self._check_ratio_range(cd_bc, 1.272, 1.618)
        d_xd_ok = self._check_ratio(xd_xa, 0.786)

        if not (b_ok and c_ok and d_cd_ok and d_xd_ok):
            return None

        if d < x:
            pattern, direction = "GARTLEY_BULLISH", "LONG"
        elif d > x:
            pattern, direction = "GARTLEY_BEARISH", "SHORT"
        else:
            return None

        logger.debug(
            "Gartley — AB/XA=%.3f BC/AB=%.3f CD/BC=%.3f XD/XA=%.3f",
            ab_xa, bc_ab, cd_bc, xd_xa,
        )

        return self._build_signal(pattern, direction, xabcd, atr, {
            "AB_XA": round(ab_xa, 4),
            "BC_AB": round(bc_ab, 4),
            "CD_BC": round(cd_bc, 4),
            "XD_XA": round(xd_xa, 4),
        })

    def _check_bat(
        self, xabcd: list[dict], atr: float
    ) -> Optional[dict]:
        """
        Bat Bullish / Bearish.

        Ratios :
          AB/XA = 0.382 à 0.500 (±5%)
          BC/AB = 0.382 à 0.886
          CD/BC = 1.618 à 2.618
          XD/XA = 0.886 (±5%)

        Bullish : D < X
        Bearish : D > X
        """
        x, a, b, c, d = [p["price"] for p in xabcd]
        ratios = self._compute_ratios(x, a, b, c, d)

        if any(v is None for v in ratios.values()):
            return None

        ab_xa = ratios["AB_XA"]
        bc_ab = ratios["BC_AB"]
        cd_bc = ratios["CD_BC"]
        xd_xa = ratios["XD_XA"]

        # AB/XA doit être entre 0.382 et 0.500 (avec tolérance de ±5%)
        b_ok = self._check_ratio_range(
            ab_xa,
            0.382 * (1 - self._DEFAULT_TOLERANCE),
            0.500 * (1 + self._DEFAULT_TOLERANCE),
        )
        c_ok    = self._check_ratio_range(bc_ab, 0.382, 0.886)
        d_cd_ok = self._check_ratio_range(cd_bc, 1.618, 2.618)
        d_xd_ok = self._check_ratio(xd_xa, 0.886)

        if not (b_ok and c_ok and d_cd_ok and d_xd_ok):
            return None

        if d < x:
            pattern, direction = "BAT_BULLISH", "LONG"
        elif d > x:
            pattern, direction = "BAT_BEARISH", "SHORT"
        else:
            return None

        logger.debug(
            "Bat — AB/XA=%.3f BC/AB=%.3f CD/BC=%.3f XD/XA=%.3f",
            ab_xa, bc_ab, cd_bc, xd_xa,
        )

        return self._build_signal(pattern, direction, xabcd, atr, {
            "AB_XA": round(ab_xa, 4),
            "BC_AB": round(bc_ab, 4),
            "CD_BC": round(cd_bc, 4),
            "XD_XA": round(xd_xa, 4),
        })

    def _check_crab(
        self, xabcd: list[dict], atr: float
    ) -> Optional[dict]:
        """
        Crab Bullish / Bearish.

        Ratios :
          AB/XA = 0.382 à 0.618
          BC/AB = 0.382 à 0.886
          CD/BC = 2.618 à 3.618
          XD/XA = 1.618 (±5%)

        Bullish : D < X
        Bearish : D > X
        """
        x, a, b, c, d = [p["price"] for p in xabcd]
        ratios = self._compute_ratios(x, a, b, c, d)

        if any(v is None for v in ratios.values()):
            return None

        ab_xa = ratios["AB_XA"]
        bc_ab = ratios["BC_AB"]
        cd_bc = ratios["CD_BC"]
        xd_xa = ratios["XD_XA"]

        b_ok    = self._check_ratio_range(ab_xa, 0.382, 0.618)
        c_ok    = self._check_ratio_range(bc_ab, 0.382, 0.886)
        d_cd_ok = self._check_ratio_range(cd_bc, 2.618, 3.618)
        d_xd_ok = self._check_ratio(xd_xa, 1.618)

        if not (b_ok and c_ok and d_cd_ok and d_xd_ok):
            return None

        if d < x:
            pattern, direction = "CRAB_BULLISH", "LONG"
        elif d > x:
            pattern, direction = "CRAB_BEARISH", "SHORT"
        else:
            return None

        logger.debug(
            "Crab — AB/XA=%.3f BC/AB=%.3f CD/BC=%.3f XD/XA=%.3f",
            ab_xa, bc_ab, cd_bc, xd_xa,
        )

        return self._build_signal(pattern, direction, xabcd, atr, {
            "AB_XA": round(ab_xa, 4),
            "BC_AB": round(bc_ab, 4),
            "CD_BC": round(cd_bc, 4),
            "XD_XA": round(xd_xa, 4),
        })
