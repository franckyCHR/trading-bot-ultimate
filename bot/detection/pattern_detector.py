"""
Détection des figures chartistes classiques.
Utilise scipy.signal.argrelextrema pour identifier les pivots.
"""

import logging
import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
from typing import Optional

logger = logging.getLogger(__name__)


class PatternDetector:
    """
    Détecte les figures chartistes sur les 100 dernières bougies.

    Figures supportées :
      - Double Top / Double Bottom
      - Head & Shoulders / Inverse Head & Shoulders
      - Bull Flag / Bear Flag
      - Ascending Triangle / Descending Triangle / Symmetric Triangle
      - Rising Wedge / Falling Wedge
    """

    # ------------------------------------------------------------------ #
    #  Méthode publique principale                                         #
    # ------------------------------------------------------------------ #

    def detect(self, df: pd.DataFrame, sr_zones: list) -> list[dict]:
        """
        Lance la détection de toutes les figures sur les 100 dernières bougies.

        Args:
            df        : DataFrame OHLCV avec colonnes open, high, low, close, volume
            sr_zones  : Liste des zones S/R issues du sr_detector
                        (ex : [{"price": 42000, "type": "resistance"}, ...])

        Returns:
            Liste de dicts de signaux (clarity >= 2 uniquement).
        """
        if len(df) < 30:
            logger.warning("Pas assez de bougies pour la détection de figures (%d < 30)", len(df))
            return []

        # Travailler sur les 100 dernières bougies
        df_slice = df.tail(100).copy().reset_index(drop=True)

        # Calcul de l'ATR une seule fois
        atr_value = self._compute_atr(df_slice, period=14)

        # Pivots hauts et bas
        highs_idx, lows_idx = self._find_pivots(df_slice, order=5)

        signals: list[dict] = []

        # --- Appel de chaque détecteur ---
        detectors = [
            self._detect_double_top,
            self._detect_double_bottom,
            self._detect_head_shoulders,
            self._detect_inverse_head_shoulders,
            self._detect_bull_flag,
            self._detect_bear_flag,
            self._detect_ascending_triangle,
            self._detect_descending_triangle,
            self._detect_symmetric_triangle,
            self._detect_rising_wedge,
            self._detect_falling_wedge,
        ]

        for detector_fn in detectors:
            try:
                result = detector_fn(df_slice, highs_idx, lows_idx, atr_value)
                if result:
                    # Ajout du booléen reversal_candle (toujours False ici,
                    # la couche supérieure peut l'enrichir)
                    result.setdefault("reversal_candle", False)
                    result.setdefault("price", float(df_slice["close"].iloc[-1]))
                    result.setdefault("atr", round(atr_value, 4))

                    # Calcul de la clarté finale (bonus si S/R proche)
                    result["pattern_clarity"] = self._compute_clarity(
                        result, sr_zones, atr_value
                    )

                    if result["pattern_clarity"] >= 2:
                        signals.append(result)
                        logger.info(
                            "Figure détectée : %s | direction=%s | clarity=%d",
                            result["pattern"],
                            result["direction"],
                            result["pattern_clarity"],
                        )
            except Exception as exc:
                logger.debug("Erreur dans %s : %s", detector_fn.__name__, exc, exc_info=True)

        return signals

    # ------------------------------------------------------------------ #
    #  Helpers internes                                                    #
    # ------------------------------------------------------------------ #

    def _compute_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calcule l'ATR avec la méthode EMA de Wilder.

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

        # Initialisation : moyenne simple des 'period' premières TR
        atr = float(np.mean(tr_values[:period]))

        # Wilder smoothing
        for tr in tr_values[period:]:
            atr = (atr * (period - 1) + tr) / period

        return atr

    def _find_pivots(
        self, df: pd.DataFrame, order: int = 5
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Retourne les indices des pivots hauts et bas.

        Args:
            df    : DataFrame OHLCV
            order : Nombre de bougies de chaque côté pour définir un pivot

        Returns:
            (highs_idx, lows_idx) : tableaux d'indices
        """
        highs = df["high"].values
        lows  = df["low"].values

        highs_idx = argrelextrema(highs, np.greater, order=order)[0]
        lows_idx  = argrelextrema(lows,  np.less,    order=order)[0]

        return highs_idx, lows_idx

    def _compute_clarity(
        self, signal: dict, sr_zones: list, atr: float
    ) -> int:
        """
        Attribue un score de clarté final.

        Règles :
          - Le signal démarre avec la clarté interne calculée par le détecteur.
          - +1 si une zone S/R est dans un rayon de 1 ATR autour du prix du signal.
          - Maximum = 3.
        """
        clarity = signal.get("pattern_clarity", 1)

        price = signal.get("price", 0.0)
        for zone in sr_zones:
            zone_price = zone.get("price", zone) if isinstance(zone, dict) else float(zone)
            if abs(zone_price - price) <= atr:
                clarity = min(clarity + 1, 3)
                break

        return clarity

    def _slope(self, indices: np.ndarray, values: np.ndarray) -> float:
        """Régression linéaire simple — retourne la pente."""
        if len(indices) < 2:
            return 0.0
        x = indices.astype(float)
        y = values.astype(float)
        n = len(x)
        slope = (n * np.dot(x, y) - x.sum() * y.sum()) / (
            n * np.dot(x, x) - x.sum() ** 2 + 1e-12
        )
        return float(slope)

    # ------------------------------------------------------------------ #
    #  Détecteurs individuels                                              #
    # ------------------------------------------------------------------ #

    # --- 1. DOUBLE TOP ---------------------------------------------------

    def _detect_double_top(
        self,
        df: pd.DataFrame,
        highs_idx: np.ndarray,
        lows_idx: np.ndarray,
        atr: float,
    ) -> Optional[dict]:
        """
        Double Top (Bearish).

        Deux pivots hauts similaires (< 1% d'écart) séparés par un pivot bas.
        La neckline est le bas intermédiaire.
        """
        if len(highs_idx) < 2 or len(lows_idx) < 1:
            return None

        highs_prices = df["high"].values

        # Parcourir les paires de pivots hauts
        for i in range(len(highs_idx) - 1):
            idx1 = highs_idx[i]
            idx2 = highs_idx[i + 1]
            p1   = highs_prices[idx1]
            p2   = highs_prices[idx2]

            # Les deux sommets doivent être similaires (< 1%)
            if abs(p1 - p2) / p1 > 0.01:
                continue

            # Il doit exister un pivot bas entre les deux sommets
            mid_lows = lows_idx[(lows_idx > idx1) & (lows_idx < idx2)]
            if len(mid_lows) == 0:
                continue

            neckline_idx   = mid_lows[np.argmin(df["low"].values[mid_lows])]
            neckline_price = float(df["low"].values[neckline_idx])
            current_close  = float(df["close"].iloc[-1])

            # Validation : le prix est proche de la neckline ou l'a cassée
            near_or_broken = current_close <= neckline_price * 1.02

            if not near_or_broken:
                continue

            clarity = 2 if abs(p1 - p2) / p1 < 0.005 else 1

            return {
                "pattern":    "DOUBLE_TOP",
                "direction":  "SHORT",
                "pattern_clarity": clarity,
                "price":      current_close,
                "atr":        round(atr, 4),
                "description": f"Double Top détecté — neckline {neckline_price:.2f}",
                "neckline":   neckline_price,
                "valley":     neckline_price,  # alias entry_calculator
                "top1_price": float(p1),
                "top2_price": float(p2),
                "top1_idx":   int(idx1),
                "top2_idx":   int(idx2),
                "top1_bar":   int(idx1),  # alias pour chart_drawers
                "top2_bar":   int(idx2),  # alias pour chart_drawers
                "valley_bar": int(neckline_idx),
            }

        return None

    # --- 2. DOUBLE BOTTOM ------------------------------------------------

    def _detect_double_bottom(
        self,
        df: pd.DataFrame,
        highs_idx: np.ndarray,
        lows_idx: np.ndarray,
        atr: float,
    ) -> Optional[dict]:
        """
        Double Bottom (Bullish).

        Deux pivots bas similaires (< 1%) séparés par un pivot haut.
        La neckline est le haut intermédiaire.
        """
        if len(lows_idx) < 2 or len(highs_idx) < 1:
            return None

        lows_prices = df["low"].values

        for i in range(len(lows_idx) - 1):
            idx1 = lows_idx[i]
            idx2 = lows_idx[i + 1]
            p1   = lows_prices[idx1]
            p2   = lows_prices[idx2]

            if abs(p1 - p2) / p1 > 0.01:
                continue

            mid_highs = highs_idx[(highs_idx > idx1) & (highs_idx < idx2)]
            if len(mid_highs) == 0:
                continue

            neckline_idx   = mid_highs[np.argmax(df["high"].values[mid_highs])]
            neckline_price = float(df["high"].values[neckline_idx])
            current_close  = float(df["close"].iloc[-1])

            near_or_broken = current_close >= neckline_price * 0.98

            if not near_or_broken:
                continue

            clarity = 2 if abs(p1 - p2) / p1 < 0.005 else 1

            return {
                "pattern":    "DOUBLE_BOTTOM",
                "direction":  "LONG",
                "pattern_clarity": clarity,
                "price":      current_close,
                "atr":        round(atr, 4),
                "description": f"Double Bottom détecté — neckline {neckline_price:.2f}",
                "neckline":   neckline_price,
                "peak":       neckline_price,  # alias entry_calculator
                "bot1_price": float(p1),
                "bot2_price": float(p2),
                "bot1_bar":   int(idx1),       # alias pour chart_drawers
                "bot2_bar":   int(idx2),       # alias pour chart_drawers
                "peak_bar":   int(neckline_idx),
            }

        return None

    # --- 3. HEAD & SHOULDERS (Bearish) -----------------------------------

    def _detect_head_shoulders(
        self,
        df: pd.DataFrame,
        highs_idx: np.ndarray,
        lows_idx: np.ndarray,
        atr: float,
    ) -> Optional[dict]:
        """
        Épaule-Tête-Épaule (Bearish).

        3 pivots hauts : les épaules sont environ à la même hauteur,
        la tête est le plus haut des trois.
        La neckline relie les deux creux entre épaules.
        """
        if len(highs_idx) < 3:
            return None

        highs_prices = df["high"].values
        lows_prices  = df["low"].values

        for i in range(len(highs_idx) - 2):
            ls_idx  = highs_idx[i]
            h_idx   = highs_idx[i + 1]
            rs_idx  = highs_idx[i + 2]

            ls  = highs_prices[ls_idx]
            hd  = highs_prices[h_idx]
            rs  = highs_prices[rs_idx]

            # La tête doit être le plus haut
            if not (hd > ls and hd > rs):
                continue

            # Les épaules doivent être comparables (< 5% d'écart)
            if abs(ls - rs) / ls > 0.05:
                continue

            # Creux entre épaule gauche et tête
            left_lows  = lows_idx[(lows_idx > ls_idx) & (lows_idx < h_idx)]
            # Creux entre tête et épaule droite
            right_lows = lows_idx[(lows_idx > h_idx)  & (lows_idx < rs_idx)]

            if len(left_lows) == 0 or len(right_lows) == 0:
                continue

            ll_price = float(lows_prices[left_lows[np.argmin(lows_prices[left_lows])]])
            rl_price = float(lows_prices[right_lows[np.argmin(lows_prices[right_lows])]])
            neckline = (ll_price + rl_price) / 2.0

            current_close = float(df["close"].iloc[-1])

            # Validation : le prix est sous ou proche de la neckline
            if current_close > neckline * 1.02:
                continue

            return {
                "pattern":    "HEAD_SHOULDERS",
                "direction":  "SHORT",
                "pattern_clarity": 2,
                "price":      current_close,
                "atr":        round(atr, 4),
                "description": f"Épaule-Tête-Épaule détecté — neckline {neckline:.2f}",
                "neckline":             round(neckline, 4),
                "left_shoulder":        round(float(ls), 4),
                "left_shoulder_price":  round(float(ls), 4),   # alias chart_drawers
                "head":                 round(float(hd), 4),
                "head_price":           round(float(hd), 4),   # alias entry/drawers
                "right_shoulder":       round(float(rs), 4),
                "right_shoulder_price": round(float(rs), 4),   # alias entry/drawers
                "left_shoulder_bar":    int(ls_idx),           # alias chart_drawers
                "head_bar":             int(h_idx),            # alias chart_drawers
                "right_shoulder_bar":   int(rs_idx),           # alias chart_drawers
            }

        return None

    # --- 4. INVERSE HEAD & SHOULDERS (Bullish) ---------------------------

    def _detect_inverse_head_shoulders(
        self,
        df: pd.DataFrame,
        highs_idx: np.ndarray,
        lows_idx: np.ndarray,
        atr: float,
    ) -> Optional[dict]:
        """
        Épaule-Tête-Épaule Inversé (Bullish).

        3 pivots bas : la tête est le plus bas des trois.
        """
        if len(lows_idx) < 3:
            return None

        lows_prices  = df["low"].values
        highs_prices = df["high"].values

        for i in range(len(lows_idx) - 2):
            ls_idx  = lows_idx[i]
            h_idx   = lows_idx[i + 1]
            rs_idx  = lows_idx[i + 2]

            ls  = lows_prices[ls_idx]
            hd  = lows_prices[h_idx]
            rs  = lows_prices[rs_idx]

            # La tête doit être le plus bas
            if not (hd < ls and hd < rs):
                continue

            # Les épaules doivent être comparables (< 5%)
            if abs(ls - rs) / ls > 0.05:
                continue

            # Sommets entre les creux
            left_highs  = highs_idx[(highs_idx > ls_idx) & (highs_idx < h_idx)]
            right_highs = highs_idx[(highs_idx > h_idx)  & (highs_idx < rs_idx)]

            if len(left_highs) == 0 or len(right_highs) == 0:
                continue

            lh_price = float(highs_prices[left_highs[np.argmax(highs_prices[left_highs])]])
            rh_price = float(highs_prices[right_highs[np.argmax(highs_prices[right_highs])]])
            neckline = (lh_price + rh_price) / 2.0

            current_close = float(df["close"].iloc[-1])

            # Validation : le prix est au-dessus ou proche de la neckline
            if current_close < neckline * 0.98:
                continue

            return {
                "pattern":    "INVERSE_HEAD_SHOULDERS",
                "direction":  "LONG",
                "pattern_clarity": 2,
                "price":      current_close,
                "atr":        round(atr, 4),
                "description": f"ETE Inversé détecté — neckline {neckline:.2f}",
                "neckline":             round(neckline, 4),
                "left_shoulder":        round(float(ls), 4),
                "left_shoulder_price":  round(float(ls), 4),   # alias chart_drawers
                "head":                 round(float(hd), 4),
                "head_price":           round(float(hd), 4),   # alias entry/drawers
                "right_shoulder":       round(float(rs), 4),
                "right_shoulder_price": round(float(rs), 4),   # alias entry/drawers
                "left_shoulder_bar":    int(ls_idx),           # alias chart_drawers
                "head_bar":             int(h_idx),            # alias chart_drawers
                "right_shoulder_bar":   int(rs_idx),           # alias chart_drawers
            }

        return None

    # --- 5. BULL FLAG (Bullish) ------------------------------------------

    def _detect_bull_flag(
        self,
        df: pd.DataFrame,
        highs_idx: np.ndarray,
        lows_idx: np.ndarray,
        atr: float,
    ) -> Optional[dict]:
        """
        Drapeau Haussier (Bullish).

        Mât = forte hausse (>= 3%) sur 10-20 bougies.
        Drapeau = consolidation avec légère pente négative,
                  range < 50% du mât.
        """
        n = len(df)
        if n < 25:
            return None

        close = df["close"].values
        high  = df["high"].values
        low   = df["low"].values

        # Recherche du mât dans les 20-40 bougies précédentes
        for mast_len in range(10, 21):
            mast_start = n - mast_len - 10
            if mast_start < 0:
                continue
            mast_end = n - 10

            mast_low_price  = float(np.min(low[mast_start:mast_end]))
            mast_high_price = float(np.max(high[mast_start:mast_end]))
            mast_move       = (mast_high_price - mast_low_price) / mast_low_price

            if mast_move < 0.03:
                continue

            # Vérifier que c'est bien une hausse (close fin > close début)
            if close[mast_end - 1] < close[mast_start] * 1.02:
                continue

            # Zone de drapeau : 10 dernières bougies
            flag_start = n - 10
            flag_close = close[flag_start:]
            flag_high  = float(np.max(high[flag_start:]))
            flag_low   = float(np.min(low[flag_start:]))
            flag_range = flag_high - flag_low

            # Range du drapeau < 50% du mât
            if flag_range > 0.5 * (mast_high_price - mast_low_price):
                continue

            # Légère pente négative du drapeau
            flag_slope = self._slope(
                np.arange(len(flag_close)), flag_close
            )
            if flag_slope >= 0:
                continue

            current_close = float(df["close"].iloc[-1])

            return {
                "pattern":    "BULL_FLAG",
                "direction":  "LONG",
                "pattern_clarity": 2,
                "price":      current_close,
                "atr":        round(atr, 4),
                "description": (
                    f"Drapeau Haussier — mât {mast_move * 100:.1f}% | "
                    f"flag [{flag_low:.2f}-{flag_high:.2f}]"
                ),
                "mast_high":       round(mast_high_price, 4),
                "mast_low":        round(mast_low_price, 4),
                "mat_high":        round(mast_high_price, 4),   # alias entry_calculator
                "mat_low":         round(mast_low_price, 4),    # alias entry_calculator
                "flag_high":       round(flag_high, 4),
                "flag_low":        round(flag_low, 4),
                "flag_canal_high": round(flag_high, 4),         # alias entry_calculator
                "flag_canal_low":  round(flag_low, 4),          # alias entry_calculator
                "pole_height":     round(mast_high_price - mast_low_price, 4),
            }

        return None

    # --- 6. BEAR FLAG (Bearish) ------------------------------------------

    def _detect_bear_flag(
        self,
        df: pd.DataFrame,
        highs_idx: np.ndarray,
        lows_idx: np.ndarray,
        atr: float,
    ) -> Optional[dict]:
        """
        Drapeau Baissier (Bearish).

        Mât = forte baisse (>= 3%) sur 10-20 bougies.
        Drapeau = consolidation avec légère pente positive.
        """
        n = len(df)
        if n < 25:
            return None

        close = df["close"].values
        high  = df["high"].values
        low   = df["low"].values

        for mast_len in range(10, 21):
            mast_start = n - mast_len - 10
            if mast_start < 0:
                continue
            mast_end = n - 10

            mast_high_price = float(np.max(high[mast_start:mast_end]))
            mast_low_price  = float(np.min(low[mast_start:mast_end]))
            mast_move       = (mast_high_price - mast_low_price) / mast_high_price

            if mast_move < 0.03:
                continue

            # Vérifier que c'est bien une baisse (close fin < close début)
            if close[mast_end - 1] > close[mast_start] * 0.98:
                continue

            flag_start = n - 10
            flag_close = close[flag_start:]
            flag_high  = float(np.max(high[flag_start:]))
            flag_low   = float(np.min(low[flag_start:]))
            flag_range = flag_high - flag_low

            if flag_range > 0.5 * (mast_high_price - mast_low_price):
                continue

            # Légère pente positive du drapeau
            flag_slope = self._slope(
                np.arange(len(flag_close)), flag_close
            )
            if flag_slope <= 0:
                continue

            current_close = float(df["close"].iloc[-1])

            return {
                "pattern":    "BEAR_FLAG",
                "direction":  "SHORT",
                "pattern_clarity": 2,
                "price":      current_close,
                "atr":        round(atr, 4),
                "description": (
                    f"Drapeau Baissier — mât {mast_move * 100:.1f}% | "
                    f"flag [{flag_low:.2f}-{flag_high:.2f}]"
                ),
                "mast_high":       round(mast_high_price, 4),
                "mast_low":        round(mast_low_price, 4),
                "mat_high":        round(mast_high_price, 4),   # alias entry_calculator
                "mat_low":         round(mast_low_price, 4),    # alias entry_calculator
                "flag_high":       round(flag_high, 4),
                "flag_low":        round(flag_low, 4),
                "flag_canal_high": round(flag_high, 4),         # alias entry_calculator
                "flag_canal_low":  round(flag_low, 4),          # alias entry_calculator
                "pole_height":     round(mast_high_price - mast_low_price, 4),
            }

        return None

    # --- 7. ASCENDING TRIANGLE (Bullish) ---------------------------------

    def _detect_ascending_triangle(
        self,
        df: pd.DataFrame,
        highs_idx: np.ndarray,
        lows_idx: np.ndarray,
        atr: float,
    ) -> Optional[dict]:
        """
        Triangle Ascendant (Bullish).

        Résistance horizontale (tops dans 0.5% les uns des autres)
        + creux ascendants.
        Minimum 4 oscillations (2 hauts + 2 bas).
        """
        if len(highs_idx) < 2 or len(lows_idx) < 2:
            return None

        highs_prices = df["high"].values
        lows_prices  = df["low"].values

        # Utiliser les 5 derniers pivots hauts et bas
        recent_hi_idx = highs_idx[-5:]
        recent_lo_idx = lows_idx[-5:]
        recent_hi     = highs_prices[recent_hi_idx]
        recent_lo     = lows_prices[recent_lo_idx]

        if len(recent_hi) < 2 or len(recent_lo) < 2:
            return None

        # Résistance horizontale : tous les hauts dans 0.5% de leur moyenne
        resistance = float(np.mean(recent_hi))
        if np.any(np.abs(recent_hi - resistance) / resistance > 0.005):
            return None

        # Creux ascendants : chaque bas doit être supérieur au précédent
        if not np.all(np.diff(recent_lo) > 0):
            return None

        # Nombre total de swings >= 4
        total_swings = len(recent_hi_idx) + len(recent_lo_idx)
        if total_swings < 4:
            return None

        current_close = float(df["close"].iloc[-1])

        return {
            "pattern":    "ASCENDING_TRIANGLE",
            "direction":  "LONG",
            "pattern_clarity": 2,
            "price":      current_close,
            "atr":        round(atr, 4),
            "description":    f"Triangle Ascendant — résistance {resistance:.2f}",
            "resistance":     round(resistance, 4),
            "resistance_level": round(resistance, 4),  # alias entry_calculator
            "low1":           round(float(recent_lo[-2]), 4),
            "low2":           round(float(recent_lo[-1]), 4),
            "support_start":  round(float(recent_lo[-2]), 4),  # alias entry_calculator
            "support_end":    round(float(recent_lo[-1]), 4),  # alias entry_calculator
        }

    # --- 8. DESCENDING TRIANGLE (Bearish) --------------------------------

    def _detect_descending_triangle(
        self,
        df: pd.DataFrame,
        highs_idx: np.ndarray,
        lows_idx: np.ndarray,
        atr: float,
    ) -> Optional[dict]:
        """
        Triangle Descendant (Bearish).

        Support horizontal + sommets descendants.
        """
        if len(highs_idx) < 2 or len(lows_idx) < 2:
            return None

        highs_prices = df["high"].values
        lows_prices  = df["low"].values

        recent_hi_idx = highs_idx[-5:]
        recent_lo_idx = lows_idx[-5:]
        recent_hi     = highs_prices[recent_hi_idx]
        recent_lo     = lows_prices[recent_lo_idx]

        if len(recent_hi) < 2 or len(recent_lo) < 2:
            return None

        # Support horizontal : tous les bas dans 0.5% de leur moyenne
        support = float(np.mean(recent_lo))
        if np.any(np.abs(recent_lo - support) / support > 0.005):
            return None

        # Sommets descendants
        if not np.all(np.diff(recent_hi) < 0):
            return None

        total_swings = len(recent_hi_idx) + len(recent_lo_idx)
        if total_swings < 4:
            return None

        current_close = float(df["close"].iloc[-1])

        return {
            "pattern":    "DESCENDING_TRIANGLE",
            "direction":  "SHORT",
            "pattern_clarity": 2,
            "price":      current_close,
            "atr":        round(atr, 4),
            "description":      f"Triangle Descendant — support {support:.2f}",
            "support":          round(support, 4),
            "support_level":    round(support, 4),               # alias entry_calculator
            "high1":            round(float(recent_hi[-2]), 4),
            "high2":            round(float(recent_hi[-1]), 4),
            "resistance_start": round(float(recent_hi[-2]), 4),  # alias entry_calculator
            "resistance_end":   round(float(recent_hi[-1]), 4),  # alias entry_calculator
        }

    # --- 9. SYMMETRIC TRIANGLE ------------------------------------------

    def _detect_symmetric_triangle(
        self,
        df: pd.DataFrame,
        highs_idx: np.ndarray,
        lows_idx: np.ndarray,
        atr: float,
    ) -> Optional[dict]:
        """
        Triangle Symétrique (Neutre — attente de cassure).

        Sommets descendants ET creux ascendants convergent.
        """
        if len(highs_idx) < 3 or len(lows_idx) < 3:
            return None

        highs_prices = df["high"].values
        lows_prices  = df["low"].values

        recent_hi_idx = highs_idx[-5:]
        recent_lo_idx = lows_idx[-5:]
        recent_hi     = highs_prices[recent_hi_idx]
        recent_lo     = lows_prices[recent_lo_idx]

        if len(recent_hi) < 3 or len(recent_lo) < 3:
            return None

        # Sommets descendants
        if not np.all(np.diff(recent_hi) < 0):
            return None

        # Creux ascendants
        if not np.all(np.diff(recent_lo) > 0):
            return None

        # Calcul des pentes de convergence
        hi_slope = self._slope(recent_hi_idx.astype(float), recent_hi)
        lo_slope = self._slope(recent_lo_idx.astype(float), recent_lo)

        # Les deux pentes doivent converger (hi négatif, lo positif)
        if hi_slope >= 0 or lo_slope <= 0:
            return None

        current_close = float(df["close"].iloc[-1])

        # Déterminer la direction probable selon la position du prix
        mid_price = (float(recent_hi[-1]) + float(recent_lo[-1])) / 2.0
        direction = "LONG" if current_close > mid_price else "SHORT"

        return {
            "pattern":    "SYMMETRIC_TRIANGLE",
            "direction":  direction,
            "pattern_clarity": 2,
            "price":      current_close,
            "atr":        round(atr, 4),
            "description": (
                f"Triangle Symétrique — attente cassure | "
                f"pente haute={hi_slope:.4f} | pente basse={lo_slope:.4f}"
            ),
            "resistance_slope":  round(hi_slope, 6),
            "support_slope":     round(lo_slope, 6),
            # Clés pour entry_calculator (prix réels)
            "resistance_start":  round(float(recent_hi[0]), 4),
            "resistance_end":    round(float(recent_hi[-1]), 4),
            "support_start":     round(float(recent_lo[0]), 4),
            "support_end":       round(float(recent_lo[-1]), 4),
        }

    # --- 10. RISING WEDGE (Bearish) --------------------------------------

    def _detect_rising_wedge(
        self,
        df: pd.DataFrame,
        highs_idx: np.ndarray,
        lows_idx: np.ndarray,
        atr: float,
    ) -> Optional[dict]:
        """
        Biseau Ascendant (Bearish).

        Hauts ET bas montent, mais les hauts montent moins vite que les bas
        (convergence vers le haut).
        Utilise les 5 derniers pivots hauts et bas.
        """
        if len(highs_idx) < 3 or len(lows_idx) < 3:
            return None

        highs_prices = df["high"].values
        lows_prices  = df["low"].values

        recent_hi_idx = highs_idx[-5:]
        recent_lo_idx = lows_idx[-5:]
        recent_hi     = highs_prices[recent_hi_idx]
        recent_lo     = lows_prices[recent_lo_idx]

        if len(recent_hi) < 3 or len(recent_lo) < 3:
            return None

        # Les hauts et bas doivent tous monter
        if not (np.all(np.diff(recent_hi) > 0) and np.all(np.diff(recent_lo) > 0)):
            return None

        hi_slope = self._slope(recent_hi_idx.astype(float), recent_hi)
        lo_slope = self._slope(recent_lo_idx.astype(float), recent_lo)

        # Convergence : pente des bas > pente des hauts (les lignes se rapprochent)
        if lo_slope <= hi_slope:
            return None

        # Les deux pentes doivent être positives
        if hi_slope <= 0 or lo_slope <= 0:
            return None

        current_close = float(df["close"].iloc[-1])

        return {
            "pattern":    "RISING_WEDGE",
            "direction":  "SHORT",
            "pattern_clarity": 2,
            "price":      current_close,
            "atr":        round(atr, 4),
            "description": (
                f"Biseau Ascendant (Rising Wedge) — "
                f"pente haute={hi_slope:.4f} | pente basse={lo_slope:.4f}"
            ),
            "upper_line_start": round(float(recent_hi[0]), 4),
            "lower_line_start": round(float(recent_lo[0]), 4),
            # Clés pour entry_calculator
            "resistance_start": round(float(recent_hi[0]), 4),
            "resistance_end":   round(float(recent_hi[-1]), 4),
            "support_start":    round(float(recent_lo[0]), 4),
            "support_end":      round(float(recent_lo[-1]), 4),
        }

    # --- 11. FALLING WEDGE (Bullish) -------------------------------------

    def _detect_falling_wedge(
        self,
        df: pd.DataFrame,
        highs_idx: np.ndarray,
        lows_idx: np.ndarray,
        atr: float,
    ) -> Optional[dict]:
        """
        Biseau Descendant (Bullish).

        Hauts ET bas descendent, mais les hauts descendent plus vite que les bas
        (convergence vers le bas).
        """
        if len(highs_idx) < 3 or len(lows_idx) < 3:
            return None

        highs_prices = df["high"].values
        lows_prices  = df["low"].values

        recent_hi_idx = highs_idx[-5:]
        recent_lo_idx = lows_idx[-5:]
        recent_hi     = highs_prices[recent_hi_idx]
        recent_lo     = lows_prices[recent_lo_idx]

        if len(recent_hi) < 3 or len(recent_lo) < 3:
            return None

        # Les hauts et bas doivent tous descendre
        if not (np.all(np.diff(recent_hi) < 0) and np.all(np.diff(recent_lo) < 0)):
            return None

        hi_slope = self._slope(recent_hi_idx.astype(float), recent_hi)
        lo_slope = self._slope(recent_lo_idx.astype(float), recent_lo)

        # Convergence : pente des hauts < pente des bas (les deux négatives,
        # hauts descendent plus vite)
        if hi_slope >= lo_slope:
            return None

        # Les deux pentes doivent être négatives
        if hi_slope >= 0 or lo_slope >= 0:
            return None

        current_close = float(df["close"].iloc[-1])

        return {
            "pattern":    "FALLING_WEDGE",
            "direction":  "LONG",
            "pattern_clarity": 2,
            "price":      current_close,
            "atr":        round(atr, 4),
            "description": (
                f"Biseau Descendant (Falling Wedge) — "
                f"pente haute={hi_slope:.4f} | pente basse={lo_slope:.4f}"
            ),
            "upper_line_start": round(float(recent_hi[0]), 4),
            "lower_line_start": round(float(recent_lo[0]), 4),
            # Clés pour entry_calculator
            "resistance_start": round(float(recent_hi[0]), 4),
            "resistance_end":   round(float(recent_hi[-1]), 4),
            "support_start":    round(float(recent_lo[0]), 4),
            "support_end":      round(float(recent_lo[-1]), 4),
        }
