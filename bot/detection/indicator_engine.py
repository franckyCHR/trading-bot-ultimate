"""
indicator_engine.py
===================
Moteur de calcul des indicateurs techniques pour le bot de trading.

Tous les indicateurs sont implémentés manuellement avec pandas/numpy.
pandas-ta et ta-lib sont intentionnellement exclus (incompatibles Python 3.14).

Indicateurs calculés :
    - ATR  (Average True Range, méthode Wilder)
    - ADX  + DI+/DI- (Average Directional Index, méthode Wilder)
    - RSI  (Relative Strength Index, période 14)
    - QQE  (Quantitative Qualitative Estimation, Fast + Slow lines)
    - MACD (Moving Average Convergence Divergence)
    - Bollinger Bands (période 20, 2 écarts-types)
    - EMA 50 / EMA 200

Auteur  : Trading Bot Ultimate
Version : 1.0
"""

import logging
import numpy as np
import pandas as pd

# Logger dédié à ce module
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Constantes des indicateurs
# ------------------------------------------------------------------

# ATR / ADX
ATR_PERIOD = 14
ADX_PERIOD = 14

# RSI
RSI_PERIOD = 14

# QQE
QQE_RSI_PERIOD = 14
QQE_SF = 5           # Facteur de lissage (EMA du RSI)
QQE_FACTOR = 4.236   # Multiplicateur de l'ATR RSI pour la slow line

# MACD
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Bollinger Bands
BB_PERIOD = 20
BB_STD = 2

# EMA longues
EMA_FAST = 50
EMA_SLOW = 200

# Nombre minimum de bougies requis pour que tous les calculs soient fiables
MIN_BARS = EMA_SLOW + 50  # 250 bougies minimum

# Horizon de recherche du dernier croisement QQE (en barres)
QQE_CROSS_LOOKBACK = 20


def _wilder_ema(series: pd.Series, period: int) -> pd.Series:
    """
    Calcule l'EMA lissée de Wilder (Wilder Smoothing Method).

    Formule :
        - Première valeur valide = SMA(period)
        - Valeurs suivantes : result[i] = (result[i-1] * (period - 1) + series[i]) / period

    Args:
        series (pd.Series): Série numérique d'entrée.
        period (int)       : Période de lissage.

    Returns:
        pd.Series: Série lissée selon Wilder, même index que l'entrée.
    """
    result = np.full(len(series), np.nan)
    values = series.values

    # Recherche du premier index où on peut calculer la SMA initiale
    start = period - 1
    while start < len(values) and np.isnan(values[start]):
        start += 1

    if start + period - 1 >= len(values):
        # Pas assez de données
        return pd.Series(result, index=series.index)

    # Valeur initiale = SMA sur les 'period' premières valeurs valides
    # On cherche 'period' valeurs non-NaN consécutives
    valid_start = None
    count = 0
    for i in range(len(values)):
        if not np.isnan(values[i]):
            count += 1
            if count == period:
                valid_start = i
                break
        else:
            count = 0

    if valid_start is None:
        return pd.Series(result, index=series.index)

    # Première valeur = SMA des 'period' premières données valides
    result[valid_start] = np.nanmean(values[valid_start - period + 1 : valid_start + 1])

    # Lissage de Wilder pour les valeurs suivantes
    for i in range(valid_start + 1, len(values)):
        if not np.isnan(values[i]):
            result[i] = (result[i - 1] * (period - 1) + values[i]) / period
        else:
            result[i] = result[i - 1]

    return pd.Series(result, index=series.index)


class IndicatorEngine:
    """
    Calcule tous les indicateurs techniques nécessaires au bot de trading.

    Utilisation :
        engine = IndicatorEngine()
        indicators = engine.compute(df)  # df = DataFrame OHLCV
    """

    # ------------------------------------------------------------------
    # Dictionnaire de résultat vide — retourné en cas d'erreur
    # ------------------------------------------------------------------

    @staticmethod
    def _empty_result() -> dict:
        """
        Retourne un dictionnaire avec toutes les valeurs à zéro / False / 99.
        Utilisé en cas de données insuffisantes ou d'erreur de calcul.
        """
        return {
            "adx": 0.0,
            "di_plus": 0.0,
            "di_minus": 0.0,
            "adx_rising": False,
            "qqe_fast": 0.0,
            "qqe_slow": 0.0,
            "qqe_fast_prev": 0.0,
            "qqe_slow_prev": 0.0,
            "qqe_cross_bars_ago": 99,
            "rsi": 0.0,
            "atr": 0.0,
            "macd": 0.0,
            "macd_signal": 0.0,
            "bb_upper": 0.0,
            "bb_lower": 0.0,
            "ema50": 0.0,
            "ema200": 0.0,
        }

    # ------------------------------------------------------------------
    # Méthode publique principale
    # ------------------------------------------------------------------

    def compute(self, df: pd.DataFrame) -> dict:
        """
        Calcule l'ensemble des indicateurs techniques à partir d'un DataFrame OHLCV.

        Args:
            df (pd.DataFrame): DataFrame avec colonnes [open, high, low, close, volume].
                               Doit contenir au minimum MIN_BARS lignes pour des
                               résultats fiables.

        Returns:
            dict: Dictionnaire avec toutes les valeurs d'indicateurs.
                  Retourne _empty_result() si données insuffisantes ou erreur.
        """
        # Vérification du nombre minimal de bougies
        if df is None or len(df) < MIN_BARS:
            logger.warning(
                "Données insuffisantes pour le calcul des indicateurs : "
                "%d bougies reçues, %d requises minimum.",
                0 if df is None else len(df),
                MIN_BARS,
            )
            return self._empty_result()

        try:
            # Extraction des séries de prix depuis le DataFrame
            close = df["close"].astype(float)
            high  = df["high"].astype(float)
            low   = df["low"].astype(float)

            # --- Calcul des indicateurs dans l'ordre de dépendance ---

            atr_series              = self._compute_atr(high, low, close)
            adx_vals                = self._compute_adx(high, low, close, atr_series)
            rsi_series              = self._compute_rsi(close)
            qqe_vals                = self._compute_qqe(rsi_series)
            macd_vals               = self._compute_macd(close)
            bb_vals                 = self._compute_bollinger(close)
            ema50_series            = close.ewm(span=EMA_FAST,  adjust=False).mean()
            ema200_series           = close.ewm(span=EMA_SLOW, adjust=False).mean()

            # ----------------------------------------------------------
            # Extraction des dernières valeurs (bougie la plus récente)
            # ----------------------------------------------------------

            result = {
                # ADX
                "adx"       : float(adx_vals["adx"].iloc[-1]),
                "di_plus"   : float(adx_vals["di_plus"].iloc[-1]),
                "di_minus"  : float(adx_vals["di_minus"].iloc[-1]),
                "adx_rising": bool(
                    adx_vals["adx"].iloc[-1] > adx_vals["adx"].iloc[-2]
                ),

                # QQE
                "qqe_fast"       : float(qqe_vals["fast"].iloc[-1]),
                "qqe_slow"       : float(qqe_vals["slow"].iloc[-1]),
                "qqe_fast_prev"  : float(qqe_vals["fast"].iloc[-2]),
                "qqe_slow_prev"  : float(qqe_vals["slow"].iloc[-2]),
                "qqe_cross_bars_ago": self._qqe_cross_bars_ago(
                    qqe_vals["fast"], qqe_vals["slow"]
                ),

                # RSI
                "rsi": float(rsi_series.iloc[-1]),

                # ATR
                "atr": float(atr_series.iloc[-1]),

                # MACD
                "macd"       : float(macd_vals["macd"].iloc[-1]),
                "macd_signal": float(macd_vals["signal"].iloc[-1]),

                # Bollinger Bands
                "bb_upper": float(bb_vals["upper"].iloc[-1]),
                "bb_lower": float(bb_vals["lower"].iloc[-1]),

                # EMA longues
                "ema50" : float(ema50_series.iloc[-1]),
                "ema200": float(ema200_series.iloc[-1]),
            }

            logger.debug(
                "Indicateurs calculés — ADX: %.2f | RSI: %.2f | ATR: %.6f | "
                "QQE fast/slow: %.2f/%.2f",
                result["adx"],
                result["rsi"],
                result["atr"],
                result["qqe_fast"],
                result["qqe_slow"],
            )

            return result

        except Exception as exc:
            # En cas d'erreur inattendue, on log et on retourne des zéros
            logger.exception("Erreur lors du calcul des indicateurs : %s", exc)
            return self._empty_result()

    # ------------------------------------------------------------------
    # Calcul de l'ATR (méthode Wilder)
    # ------------------------------------------------------------------

    def _compute_atr(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
    ) -> pd.Series:
        """
        Calcule l'Average True Range (ATR) selon la méthode de Wilder.

        True Range = max(
            high - low,
            |high - close_précédente|,
            |low  - close_précédente|
        )

        ATR = EMA de Wilder du True Range sur ATR_PERIOD barres.

        Args:
            high  (pd.Series): Prix hauts.
            low   (pd.Series): Prix bas.
            close (pd.Series): Prix de clôture.

        Returns:
            pd.Series: Série ATR (même index que l'entrée).
        """
        prev_close = close.shift(1)

        # True Range : composante 1 = amplitude de la bougie
        tr1 = high - low
        # True Range : composante 2 = distance high → clôture précédente
        tr2 = (high - prev_close).abs()
        # True Range : composante 3 = distance low → clôture précédente
        tr3 = (low  - prev_close).abs()

        # TR = max des 3 composantes
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Lissage de Wilder
        atr = _wilder_ema(true_range, ATR_PERIOD)
        return atr

    # ------------------------------------------------------------------
    # Calcul de l'ADX + DI+ / DI- (méthode Wilder)
    # ------------------------------------------------------------------

    def _compute_adx(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        atr: pd.Series,
    ) -> dict:
        """
        Calcule l'ADX (Average Directional Index) et les lignes directionnelles
        +DI / -DI selon la méthode de Wilder.

        Formules :
            +DM  = high - prev_high  si > 0 ET > (prev_low - low),  sinon 0
            -DM  = prev_low - low    si > 0 ET > (high - prev_high), sinon 0
            +DI  = 100 * Wilder_EMA(+DM, 14) / ATR
            -DI  = 100 * Wilder_EMA(-DM, 14) / ATR
            DX   = 100 * |+DI - -DI| / (+DI + -DI)
            ADX  = Wilder_EMA(DX, 14)

        Args:
            high  (pd.Series): Prix hauts.
            low   (pd.Series): Prix bas.
            close (pd.Series): Prix de clôture (non utilisé directement, fourni par cohérence).
            atr   (pd.Series): ATR déjà calculé.

        Returns:
            dict: {"adx": pd.Series, "di_plus": pd.Series, "di_minus": pd.Series}
        """
        prev_high = high.shift(1)
        prev_low  = low.shift(1)

        # Mouvements directionnels bruts
        up_move   = high - prev_high     # Mouvement haussier
        down_move = prev_low - low       # Mouvement baissier

        # +DM : uniquement si le mouvement haussier est positif ET supérieur au baissier
        plus_dm  = pd.Series(np.where((up_move > 0) & (up_move > down_move),  up_move,  0.0), index=high.index)
        # -DM : uniquement si le mouvement baissier est positif ET supérieur au haussier
        minus_dm = pd.Series(np.where((down_move > 0) & (down_move > up_move), down_move, 0.0), index=high.index)

        # Lissage de Wilder des DM
        smooth_plus_dm  = _wilder_ema(plus_dm,  ADX_PERIOD)
        smooth_minus_dm = _wilder_ema(minus_dm, ADX_PERIOD)

        # Protection division par zéro pour l'ATR
        atr_safe = atr.replace(0, np.nan)

        # +DI et -DI en pourcentage
        di_plus  = 100 * smooth_plus_dm  / atr_safe
        di_minus = 100 * smooth_minus_dm / atr_safe

        # DX = indice directionnel brut
        di_sum  = di_plus + di_minus
        di_diff = (di_plus - di_minus).abs()
        # Protection division par zéro
        di_sum_safe = di_sum.replace(0, np.nan)
        dx = 100 * di_diff / di_sum_safe

        # ADX = lissage de Wilder du DX
        adx = _wilder_ema(dx, ADX_PERIOD)

        # Remplacement des NaN résiduels par 0
        return {
            "adx"     : adx.fillna(0.0),
            "di_plus" : di_plus.fillna(0.0),
            "di_minus": di_minus.fillna(0.0),
        }

    # ------------------------------------------------------------------
    # Calcul du RSI (méthode EWM standard)
    # ------------------------------------------------------------------

    def _compute_rsi(self, close: pd.Series) -> pd.Series:
        """
        Calcule le RSI (Relative Strength Index) sur RSI_PERIOD barres.

        Utilise la méthode des moyennes exponentielles (EWM) :
            delta = close.diff()
            gain  = EWM(max(delta, 0), com=RSI_PERIOD-1)
            loss  = EWM(max(-delta, 0), com=RSI_PERIOD-1)
            RSI   = 100 - 100 / (1 + gain / loss)

        Args:
            close (pd.Series): Prix de clôture.

        Returns:
            pd.Series: Série RSI (0–100), même index que l'entrée.
        """
        delta = close.diff()

        # Séparation des gains et des pertes
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)

        # Lissage exponentiel (com = période - 1 pour reproduire le RSI de Wilder)
        avg_gain = gain.ewm(com=RSI_PERIOD - 1, adjust=False).mean()
        avg_loss = loss.ewm(com=RSI_PERIOD - 1, adjust=False).mean()

        # Protection division par zéro
        avg_loss_safe = avg_loss.replace(0, np.nan)
        rs  = avg_gain / avg_loss_safe
        rsi = 100.0 - (100.0 / (1.0 + rs))

        return rsi.fillna(50.0)

    # ------------------------------------------------------------------
    # Calcul du QQE (Quantitative Qualitative Estimation)
    # ------------------------------------------------------------------

    def _compute_qqe(self, rsi: pd.Series) -> dict:
        """
        Calcule les deux lignes du QQE (fast line et slow line).

        Algorithme :
            1. SMRSI    = EMA(RSI, QQE_SF)            → ligne rapide (fast)
            2. TR_RSI   = |SMRSI - SMRSI.shift(1)|    → variation du RSI lissé
            3. WILLMA   = EMA(TR_RSI, QQE_SF)         → ATR du RSI lissé
            4. QQE_delta = WILLMA * QQE_FACTOR
            5. Slow line = trailing stop adaptatif :
                - Si SMRSI > prev_slow : slow = max(prev_slow, SMRSI - QQE_delta)
                - Si SMRSI < prev_slow : slow = min(prev_slow, SMRSI + QQE_delta)

        Args:
            rsi (pd.Series): Série RSI déjà calculée.

        Returns:
            dict: {"fast": pd.Series, "slow": pd.Series}
        """
        # --- Étape 1 : Lissage du RSI (ligne rapide) ---
        smrsi = rsi.ewm(span=QQE_SF, adjust=False).mean()

        # --- Étape 2 : ATR du RSI lissé ---
        tr_rsi = smrsi.diff().abs()
        willma = tr_rsi.ewm(span=QQE_SF, adjust=False).mean()

        # --- Étape 3 : Bande de fluctuation ---
        qqe_delta = willma * QQE_FACTOR

        # --- Étape 4 : Calcul de la slow line (trailing stop) ---
        smrsi_arr   = smrsi.values
        delta_arr   = qqe_delta.values
        slow_arr    = np.full(len(smrsi_arr), np.nan)

        # Initialisation : première valeur valide
        first_valid = 0
        while first_valid < len(smrsi_arr) and np.isnan(smrsi_arr[first_valid]):
            first_valid += 1

        if first_valid < len(smrsi_arr):
            slow_arr[first_valid] = smrsi_arr[first_valid]

        # Propagation de la slow line barre par barre
        for i in range(first_valid + 1, len(smrsi_arr)):
            if np.isnan(smrsi_arr[i]) or np.isnan(delta_arr[i]):
                # Propagation de la dernière valeur valide si données manquantes
                slow_arr[i] = slow_arr[i - 1]
                continue

            prev_slow = slow_arr[i - 1]
            curr_smrsi = smrsi_arr[i]
            curr_delta = delta_arr[i]

            if np.isnan(prev_slow):
                # Cas rare : initialisation tardive
                slow_arr[i] = curr_smrsi
            elif curr_smrsi > prev_slow:
                # Tendance haussière : le stop remonte (jamais en dessous du précédent)
                slow_arr[i] = max(prev_slow, curr_smrsi - curr_delta)
            else:
                # Tendance baissière : le stop descend (jamais au dessus du précédent)
                slow_arr[i] = min(prev_slow, curr_smrsi + curr_delta)

        slow_series = pd.Series(slow_arr, index=smrsi.index).fillna(smrsi)

        return {
            "fast": smrsi.fillna(50.0),
            "slow": slow_series.fillna(50.0),
        }

    # ------------------------------------------------------------------
    # Détection du dernier croisement QQE
    # ------------------------------------------------------------------

    def _qqe_cross_bars_ago(
        self, fast: pd.Series, slow: pd.Series
    ) -> int:
        """
        Détecte le dernier croisement entre la fast line et la slow line du QQE.

        On regarde les QQE_CROSS_LOOKBACK dernières barres et on cherche
        à quel moment la fast line a croisé (dans un sens ou dans l'autre)
        la slow line.

        Un croisement est défini par :
            - Barre N-1 : fast >= slow  ET  barre N : fast < slow  (croisement baissier)
            - Barre N-1 : fast <= slow  ET  barre N : fast > slow  (croisement haussier)

        Args:
            fast (pd.Series): Ligne rapide QQE.
            slow (pd.Series): Ligne lente QQE.

        Returns:
            int: Nombre de barres écoulées depuis le dernier croisement.
                 0  = croisement sur la bougie actuelle.
                 99 = aucun croisement trouvé dans les QQE_CROSS_LOOKBACK dernières barres.
        """
        # On travaille sur les QQE_CROSS_LOOKBACK + 1 dernières barres
        # (+1 pour avoir la barre précédente lors de la comparaison)
        n = min(QQE_CROSS_LOOKBACK + 1, len(fast))
        fast_slice = fast.iloc[-n:].values
        slow_slice = slow.iloc[-n:].values

        # Parcours de la fin vers le début (bougie la plus récente en premier)
        # Index 0 de fast_slice = la plus ancienne bougie dans la fenêtre
        # Index -1 = la dernière bougie
        for i in range(len(fast_slice) - 1, 0, -1):
            curr_fast  = fast_slice[i]
            curr_slow  = slow_slice[i]
            prev_fast  = fast_slice[i - 1]
            prev_slow  = slow_slice[i - 1]

            # Vérification que les valeurs sont valides
            if any(np.isnan(v) for v in [curr_fast, curr_slow, prev_fast, prev_slow]):
                continue

            # Croisement haussier : fast passe au dessus de slow
            crossed_up   = (prev_fast <= prev_slow) and (curr_fast > curr_slow)
            # Croisement baissier : fast passe en dessous de slow
            crossed_down = (prev_fast >= prev_slow) and (curr_fast < curr_slow)

            if crossed_up or crossed_down:
                # Nombre de barres depuis ce croisement
                # i est l'index dans fast_slice, la dernière barre est à l'index len-1
                bars_ago = (len(fast_slice) - 1) - i
                return bars_ago

        # Aucun croisement trouvé dans la fenêtre
        return 99

    # ------------------------------------------------------------------
    # Calcul du MACD
    # ------------------------------------------------------------------

    def _compute_macd(self, close: pd.Series) -> dict:
        """
        Calcule le MACD (Moving Average Convergence Divergence).

        Formules :
            EMA_fast   = EMA(close, 12)
            EMA_slow   = EMA(close, 26)
            MACD       = EMA_fast - EMA_slow
            Signal     = EMA(MACD, 9)
            Histogram  = MACD - Signal

        Args:
            close (pd.Series): Prix de clôture.

        Returns:
            dict: {"macd": pd.Series, "signal": pd.Series, "histogram": pd.Series}
        """
        ema_fast   = close.ewm(span=MACD_FAST,   adjust=False).mean()
        ema_slow   = close.ewm(span=MACD_SLOW,   adjust=False).mean()
        macd_line  = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=MACD_SIGNAL, adjust=False).mean()
        histogram  = macd_line - signal_line

        return {
            "macd"     : macd_line.fillna(0.0),
            "signal"   : signal_line.fillna(0.0),
            "histogram": histogram.fillna(0.0),
        }

    # ------------------------------------------------------------------
    # Calcul des Bandes de Bollinger
    # ------------------------------------------------------------------

    def _compute_bollinger(self, close: pd.Series) -> dict:
        """
        Calcule les Bandes de Bollinger.

        Formules :
            Middle = SMA(close, 20)
            Upper  = Middle + 2 * std(close, 20)
            Lower  = Middle - 2 * std(close, 20)

        Args:
            close (pd.Series): Prix de clôture.

        Returns:
            dict: {"upper": pd.Series, "middle": pd.Series, "lower": pd.Series}
        """
        # Moyenne mobile simple sur BB_PERIOD barres
        middle = close.rolling(window=BB_PERIOD).mean()
        # Écart-type glissant sur BB_PERIOD barres (ddof=1 par défaut dans pandas)
        std    = close.rolling(window=BB_PERIOD).std()

        upper = middle + BB_STD * std
        lower = middle - BB_STD * std

        return {
            "upper" : upper.fillna(0.0),
            "middle": middle.fillna(0.0),
            "lower" : lower.fillna(0.0),
        }
