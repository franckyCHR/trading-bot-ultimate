"""
Détecteur de chandeliers de retournement (reversal candles).
Chaque signal n'est retourné que si le chandelier se trouve
à proximité d'une zone S/R valide (tolérance 0.5%).
"""

import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class CandleDetector:
    """
    Détecte les figures de retournement en chandelier sur les 3 dernières barres.

    Règle absolue : un signal n'est émis que si le chandelier est sur ou proche
    d'une zone S/R (dans un rayon de 0.5% du prix de la zone).

    Chandeliers détectés
    --------------------
    Bullish  : Pin Bar, Hammer, Engulfing, Morning Star, Harami, Doji support
    Bearish  : Shooting Star, Engulfing, Evening Star, Harami, Doji résistance
    """

    # Tolérance de proximité avec une zone S/R (0.5%)
    TOLERANCE_SR = 0.005

    # Période ATR pour l'indication de volatilité
    ATR_PERIODE = 14

    def detect(self, df: pd.DataFrame, sr_zones: list) -> list[dict]:
        """
        Détecte les chandeliers de retournement sur les 3 dernières barres.

        Paramètres
        ----------
        df : pd.DataFrame
            DataFrame OHLCV (colonnes insensibles à la casse).
        sr_zones : list[dict]
            Liste de zones S/R retournées par SRDetector.detect().

        Retourne
        --------
        list[dict]
            Signaux de retournement détectés.
        """
        # --- Normalisation des colonnes ---
        df = df.copy()
        df.columns = [c.lower() for c in df.columns]

        if len(df) < 3:
            logger.warning("DataFrame trop court (%d barres) pour analyser les chandeliers.", len(df))
            return []

        # --- ATR pour la valeur atr dans le signal ---
        atr_value = self._calculer_atr_dernier(df)

        # --- Extraction des 3 dernières bougies ---
        c0 = df.iloc[-1]   # Bougie actuelle (signal)
        c1 = df.iloc[-2]   # Bougie précédente
        c2 = df.iloc[-3]   # Bougie ante-précédente

        signaux: list[dict] = []

        # --- Lancement des détecteurs individuels ---
        detecteurs = [
            self._pin_bar_bullish,
            self._pin_bar_bearish,
            self._hammer,
            self._engulfing_bullish,
            self._engulfing_bearish,
            self._morning_star,
            self._evening_star,
            self._harami_bullish,
            self._harami_bearish,
            self._doji,
        ]

        for detecteur in detecteurs:
            try:
                signal = detecteur(c0, c1, c2, sr_zones, atr_value)
                if signal is not None:
                    signaux.append(signal)
                    logger.info("Signal détecté : %s à %.4f", signal["pattern"], signal["price"])
            except Exception as exc:
                logger.error("Erreur dans %s : %s", detecteur.__name__, exc)

        logger.debug("%d signal(s) chandelier trouvé(s).", len(signaux))
        return signaux

    # ------------------------------------------------------------------
    # Helper : proximité S/R
    # ------------------------------------------------------------------

    def _is_near_sr(self, price: float, sr_zones: list, tolerance: float = 0.005) -> tuple[bool, dict | None]:
        """
        Vérifie si `price` est à moins de `tolerance` (fraction) d'une zone S/R.

        Retourne
        --------
        (bool, dict | None)
            True + la zone la plus proche si une zone est à portée, sinon (False, None).
        """
        if not sr_zones:
            return False, None

        meilleure_zone = None
        meilleure_distance = float("inf")

        for zone in sr_zones:
            zone_price = zone.get("price", 0)
            if zone_price <= 0:
                continue
            distance = abs(price - zone_price) / zone_price
            if distance <= tolerance and distance < meilleure_distance:
                meilleure_distance = distance
                meilleure_zone = zone

        return (meilleure_zone is not None), meilleure_zone

    # ------------------------------------------------------------------
    # Helper : calcul ATR
    # ------------------------------------------------------------------

    def _calculer_atr_dernier(self, df: pd.DataFrame) -> float:
        """
        Calcule la dernière valeur d'ATR(14) avec le lissage Wilder.
        Retourne 0.0 si le DataFrame est trop court.
        """
        if len(df) < self.ATR_PERIODE + 1:
            return 0.0

        high = df["high"].values
        low = df["low"].values
        close = df["close"].values

        # True Range
        tr = np.maximum(
            high[1:] - low[1:],
            np.maximum(
                np.abs(high[1:] - close[:-1]),
                np.abs(low[1:] - close[:-1]),
            )
        )

        # Première valeur ATR : moyenne simple
        atr = float(tr[:self.ATR_PERIODE].mean())

        # Lissage Wilder
        for i in range(self.ATR_PERIODE, len(tr)):
            atr = (atr * (self.ATR_PERIODE - 1) + tr[i]) / self.ATR_PERIODE

        return round(atr, 8)

    # ------------------------------------------------------------------
    # Helpers : mesures d'une bougie
    # ------------------------------------------------------------------

    @staticmethod
    def _mesures(c) -> tuple[float, float, float, float, float, float]:
        """
        Retourne (open, high, low, close, body, range_total) pour une bougie.
        body = |close - open|, range_total = high - low (vaut au moins 1e-12).
        """
        o, h, l, cl = float(c["open"]), float(c["high"]), float(c["low"]), float(c["close"])
        body = abs(cl - o)
        range_total = max(h - l, 1e-12)
        return o, h, l, cl, body, range_total

    @staticmethod
    def _ombre_basse(o: float, l: float, cl: float) -> float:
        """Longueur de l'ombre basse."""
        return min(o, cl) - l

    @staticmethod
    def _ombre_haute(o: float, h: float, cl: float) -> float:
        """Longueur de l'ombre haute."""
        return h - max(o, cl)

    @staticmethod
    def _base_signal(pattern: str, direction: str, c, atr: float) -> dict:
        """Construit le squelette commun d'un signal chandelier."""
        return {
            "pattern": pattern,
            "direction": direction,
            "pattern_clarity": 3,
            "reversal_candle": True,
            "price": round(float(c["close"]), 8),
            "atr": round(atr, 8),
            "candle_high": round(float(c["high"]), 8),
            "candle_low": round(float(c["low"]), 8),
            "candle_open": round(float(c["open"]), 8),
            "candle_close": round(float(c["close"]), 8),
            # Aliases pour entry_calculator._reversal_candle
            "close": round(float(c["close"]), 8),
            "high":  round(float(c["high"]), 8),
            "low":   round(float(c["low"]), 8),
            "open":  round(float(c["open"]), 8),
            "description": "",  # Complété par chaque détecteur
        }

    # ------------------------------------------------------------------
    # Détecteurs individuels
    # ------------------------------------------------------------------

    def _pin_bar_bullish(self, c0, c1, c2, sr_zones, atr) -> dict | None:
        """
        Pin Bar Bullish :
            - Ombre basse >= 2.5x le corps
            - Clôture dans les 40% supérieurs du range
            - Sur zone support
        """
        o, h, l, cl, body, rng = self._mesures(c0)
        ombre_b = self._ombre_basse(o, l, cl)

        if body < 1e-12:
            return None

        # Condition 1 : ombre basse >= 2.5x corps
        if ombre_b < 2.5 * body:
            return None

        # Condition 2 : clôture dans les 40% supérieurs du range
        position_close = (cl - l) / rng
        if position_close < 0.60:
            return None

        # Condition 3 : sur zone support
        proche, zone = self._is_near_sr(cl, sr_zones, self.TOLERANCE_SR)
        if not proche or zone is None or zone.get("type") != "support":
            return None

        signal = self._base_signal("PIN_BAR_BULLISH", "LONG", c0, atr)
        signal["description"] = f"Pin Bar Bullish sur zone support {zone['price']:.4f}"
        return signal

    def _pin_bar_bearish(self, c0, c1, c2, sr_zones, atr) -> dict | None:
        """
        Pin Bar Bearish (Shooting Star) :
            - Ombre haute >= 2.5x le corps
            - Clôture dans les 40% inférieurs du range
            - Sur zone résistance
        """
        o, h, l, cl, body, rng = self._mesures(c0)
        ombre_h = self._ombre_haute(o, h, cl)

        if body < 1e-12:
            return None

        # Condition 1 : ombre haute >= 2.5x corps
        if ombre_h < 2.5 * body:
            return None

        # Condition 2 : clôture dans les 40% inférieurs du range
        position_close = (cl - l) / rng
        if position_close > 0.40:
            return None

        # Condition 3 : sur zone résistance
        proche, zone = self._is_near_sr(cl, sr_zones, self.TOLERANCE_SR)
        if not proche or zone is None or zone.get("type") != "resistance":
            return None

        signal = self._base_signal("PIN_BAR_BEARISH", "SHORT", c0, atr)
        signal["description"] = f"Pin Bar Bearish (Shooting Star) sur zone résistance {zone['price']:.4f}"
        return signal

    def _hammer(self, c0, c1, c2, sr_zones, atr) -> dict | None:
        """
        Hammer Bullish :
            - Petit corps (< 30% du range total)
            - Ombre basse >= 2x le corps
            - Ombre haute < 10% du range total
            - Clôture > Ouverture
            - Sur zone support
        """
        o, h, l, cl, body, rng = self._mesures(c0)
        ombre_b = self._ombre_basse(o, l, cl)
        ombre_h = self._ombre_haute(o, h, cl)

        # Clôture haussière
        if cl <= o:
            return None

        # Petit corps
        if body >= 0.30 * rng:
            return None

        # Ombre basse >= 2x corps
        if body < 1e-12 or ombre_b < 2.0 * body:
            return None

        # Ombre haute < 10% du range
        if ombre_h >= 0.10 * rng:
            return None

        # Sur zone support
        proche, zone = self._is_near_sr(cl, sr_zones, self.TOLERANCE_SR)
        if not proche or zone is None or zone.get("type") != "support":
            return None

        signal = self._base_signal("HAMMER_BULLISH", "LONG", c0, atr)
        signal["description"] = f"Hammer Bullish sur zone support {zone['price']:.4f}"
        return signal

    def _engulfing_bullish(self, c0, c1, c2, sr_zones, atr) -> dict | None:
        """
        Engulfing Bullish :
            - c0 haussier (close > open)
            - c1 baissier (close < open)
            - Corps de c0 englobe entièrement le corps de c1
            - Sur zone support
        """
        o0, h0, l0, cl0, _, _ = self._mesures(c0)
        o1, h1, l1, cl1, _, _ = self._mesures(c1)

        # c0 haussier, c1 baissier
        if cl0 <= o0 or cl1 >= o1:
            return None

        # Englobement des corps
        if o0 > cl1 or cl0 < o1:
            return None

        # Sur zone support
        proche, zone = self._is_near_sr(cl0, sr_zones, self.TOLERANCE_SR)
        if not proche or zone is None or zone.get("type") != "support":
            return None

        signal = self._base_signal("ENGULFING_BULLISH", "LONG", c0, atr)
        signal["description"] = f"Engulfing Bullish sur zone support {zone['price']:.4f}"
        return signal

    def _engulfing_bearish(self, c0, c1, c2, sr_zones, atr) -> dict | None:
        """
        Engulfing Bearish :
            - c0 baissier (close < open)
            - c1 haussier (close > open)
            - Corps de c0 englobe entièrement le corps de c1
            - Sur zone résistance
        """
        o0, h0, l0, cl0, _, _ = self._mesures(c0)
        o1, h1, l1, cl1, _, _ = self._mesures(c1)

        # c0 baissier, c1 haussier
        if cl0 >= o0 or cl1 <= o1:
            return None

        # Englobement des corps
        if o0 < cl1 or cl0 > o1:
            return None

        # Sur zone résistance
        proche, zone = self._is_near_sr(cl0, sr_zones, self.TOLERANCE_SR)
        if not proche or zone is None or zone.get("type") != "resistance":
            return None

        signal = self._base_signal("ENGULFING_BEARISH", "SHORT", c0, atr)
        signal["description"] = f"Engulfing Bearish sur zone résistance {zone['price']:.4f}"
        return signal

    def _morning_star(self, c0, c1, c2, sr_zones, atr) -> dict | None:
        """
        Morning Star (3 bougies, Bullish) :
            - c2 : baissier avec grand corps
            - c1 : petit corps (doji-like), gap ou chevauchement
            - c0 : haussier, clôture au-dessus du milieu du corps de c2
            - Sur zone support
        """
        o0, h0, l0, cl0, body0, rng0 = self._mesures(c0)
        o1, h1, l1, cl1, body1, rng1 = self._mesures(c1)
        o2, h2, l2, cl2, body2, rng2 = self._mesures(c2)

        # c2 baissier avec grand corps
        if cl2 >= o2:
            return None
        if body2 < 0.5 * rng2:   # Grand corps = > 50% du range
            return None

        # c1 petit corps (< 30% de son range)
        if rng1 > 1e-12 and body1 >= 0.30 * rng1:
            return None

        # c0 haussier
        if cl0 <= o0:
            return None

        # c0 clôture au-dessus du milieu du corps de c2
        milieu_c2 = (o2 + cl2) / 2
        if cl0 <= milieu_c2:
            return None

        # Sur zone support
        proche, zone = self._is_near_sr(cl0, sr_zones, self.TOLERANCE_SR)
        if not proche or zone is None or zone.get("type") != "support":
            return None

        signal = self._base_signal("MORNING_STAR_BULLISH", "LONG", c0, atr)
        signal["description"] = f"Morning Star Bullish sur zone support {zone['price']:.4f}"
        return signal

    def _evening_star(self, c0, c1, c2, sr_zones, atr) -> dict | None:
        """
        Evening Star (3 bougies, Bearish) :
            - c2 : haussier avec grand corps
            - c1 : petit corps
            - c0 : baissier, clôture en-dessous du milieu du corps de c2
            - Sur zone résistance
        """
        o0, h0, l0, cl0, body0, rng0 = self._mesures(c0)
        o1, h1, l1, cl1, body1, rng1 = self._mesures(c1)
        o2, h2, l2, cl2, body2, rng2 = self._mesures(c2)

        # c2 haussier avec grand corps
        if cl2 <= o2:
            return None
        if body2 < 0.5 * rng2:
            return None

        # c1 petit corps
        if rng1 > 1e-12 and body1 >= 0.30 * rng1:
            return None

        # c0 baissier
        if cl0 >= o0:
            return None

        # c0 clôture en-dessous du milieu du corps de c2
        milieu_c2 = (o2 + cl2) / 2
        if cl0 >= milieu_c2:
            return None

        # Sur zone résistance
        proche, zone = self._is_near_sr(cl0, sr_zones, self.TOLERANCE_SR)
        if not proche or zone is None or zone.get("type") != "resistance":
            return None

        signal = self._base_signal("EVENING_STAR_BEARISH", "SHORT", c0, atr)
        signal["description"] = f"Evening Star Bearish sur zone résistance {zone['price']:.4f}"
        return signal

    def _harami_bullish(self, c0, c1, c2, sr_zones, atr) -> dict | None:
        """
        Harami Bullish :
            - c1 : grand bougie baissière
            - c0 : petite bougie haussière entièrement à l'intérieur du corps de c1
            - Sur zone support
        """
        o0, h0, l0, cl0, body0, rng0 = self._mesures(c0)
        o1, h1, l1, cl1, body1, rng1 = self._mesures(c1)

        # c1 baissier avec grand corps
        if cl1 >= o1:
            return None
        if body1 < 0.5 * rng1:
            return None

        # c0 haussier
        if cl0 <= o0:
            return None

        # Corps de c0 entièrement à l'intérieur du corps de c1
        # Corps de c1 va de cl1 (bas) à o1 (haut) car c1 est baissier
        if o0 < cl1 or cl0 > o1:
            return None

        # Sur zone support
        proche, zone = self._is_near_sr(cl0, sr_zones, self.TOLERANCE_SR)
        if not proche or zone is None or zone.get("type") != "support":
            return None

        signal = self._base_signal("HARAMI_BULLISH", "LONG", c0, atr)
        signal["description"] = f"Harami Bullish sur zone support {zone['price']:.4f}"
        return signal

    def _harami_bearish(self, c0, c1, c2, sr_zones, atr) -> dict | None:
        """
        Harami Bearish :
            - c1 : grand bougie haussière
            - c0 : petite bougie baissière entièrement à l'intérieur du corps de c1
            - Sur zone résistance
        """
        o0, h0, l0, cl0, body0, rng0 = self._mesures(c0)
        o1, h1, l1, cl1, body1, rng1 = self._mesures(c1)

        # c1 haussier avec grand corps
        if cl1 <= o1:
            return None
        if body1 < 0.5 * rng1:
            return None

        # c0 baissier
        if cl0 >= o0:
            return None

        # Corps de c0 entièrement à l'intérieur du corps de c1
        # Corps de c1 va de o1 (bas) à cl1 (haut) car c1 est haussier
        if o0 > cl1 or cl0 < o1:
            return None

        # Sur zone résistance
        proche, zone = self._is_near_sr(cl0, sr_zones, self.TOLERANCE_SR)
        if not proche or zone is None or zone.get("type") != "resistance":
            return None

        signal = self._base_signal("HARAMI_BEARISH", "SHORT", c0, atr)
        signal["description"] = f"Harami Bearish sur zone résistance {zone['price']:.4f}"
        return signal

    def _doji(self, c0, c1, c2, sr_zones, atr) -> dict | None:
        """
        Doji :
            - Corps < 10% du range total
            - Les deux ombres sont présentes
            - Direction déduite du contexte S/R :
                LONG si sur support, SHORT si sur résistance
        """
        o, h, l, cl, body, rng = self._mesures(c0)
        ombre_b = self._ombre_basse(o, l, cl)
        ombre_h = self._ombre_haute(o, h, cl)

        # Corps inférieur à 10% du range
        if body >= 0.10 * rng:
            return None

        # Les deux ombres doivent être présentes (> 0)
        if ombre_b <= 0 or ombre_h <= 0:
            return None

        # Contexte S/R pour déterminer la direction
        proche, zone = self._is_near_sr(cl, sr_zones, self.TOLERANCE_SR)
        if not proche or zone is None:
            return None

        type_zone = zone.get("type", "")
        if type_zone == "support":
            direction = "LONG"
            label = "support"
        elif type_zone == "resistance":
            direction = "SHORT"
            label = "résistance"
        else:
            return None

        signal = self._base_signal("DOJI", direction, c0, atr)
        signal["description"] = f"Doji sur zone {label} {zone['price']:.4f}"
        return signal
