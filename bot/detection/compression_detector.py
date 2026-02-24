"""
Détecteur de zones de compression (range serré avant explosion).
Une compression indique une accumulation d'énergie avant un fort mouvement
directionnel — direction inconnue jusqu'au breakout.
"""

import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class CompressionDetector:
    """
    Détecte les zones de compression sur un DataFrame OHLCV.

    Définition d'une compression :
        - Range de la fenêtre < 1.5% du prix de clôture
        - ATR courant < 60% de l'ATR de référence (14 barres avant la fenêtre)

    Seule la compression la plus récente/significative est retournée.
    """

    # Période ATR standard (Wilder)
    ATR_PERIODE = 14

    # Fenêtre d'analyse maximale (en barres)
    FENETRE_MAX = 20

    # Taille minimale d'une fenêtre de compression
    FENETRE_MIN = 5

    # Taille maximale d'une fenêtre de compression
    FENETRE_TAILLE_MAX = 15

    # Seuil de range relatif pour valider une compression (1.5%)
    SEUIL_RANGE = 0.015

    # Rapport ATR courant / ATR précédent pour valider la compression
    SEUIL_ATR_RATIO = 0.6

    def detect(self, df: pd.DataFrame) -> list[dict]:
        """
        Détecte une zone de compression sur les 20 dernières barres.

        Paramètres
        ----------
        df : pd.DataFrame
            DataFrame OHLCV avec colonnes ['open', 'high', 'low', 'close', 'volume'].
            Les noms de colonnes sont insensibles à la casse.

        Retourne
        --------
        list[dict]
            Liste vide si aucune compression détectée, ou liste avec un seul dict
            décrivant la compression la plus récente.
        """
        # --- Normalisation des noms de colonnes ---
        df = df.copy()
        df.columns = [c.lower() for c in df.columns]

        # Il faut au moins ATR_PERIODE + FENETRE_MAX barres pour avoir un ATR de référence
        min_barres = self.ATR_PERIODE + self.FENETRE_MAX + self.ATR_PERIODE
        if len(df) < min_barres:
            logger.warning(
                "DataFrame trop court (%d barres) — minimum requis : %d.",
                len(df), min_barres
            )
            return []

        # --- Calcul de l'ATR sur tout le DataFrame ---
        atr_series = self._calculer_atr(df)

        # --- Analyse des fenêtres glissantes sur les 20 dernières barres ---
        compression_trouvee = self._chercher_compression(df, atr_series)

        if compression_trouvee is None:
            logger.info("Aucune compression détectée.")
            return []

        logger.info(
            "Compression détectée : %d bougies, range=%.3f%%, atr_ratio=%.2f",
            compression_trouvee["bars_count"],
            compression_trouvee["range_pct"] * 100,
            compression_trouvee["atr_ratio"],
        )
        return [compression_trouvee]

    # ------------------------------------------------------------------
    # Méthodes privées
    # ------------------------------------------------------------------

    def _calculer_atr(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcule l'ATR(14) avec la méthode Wilder (EMA lissée).

        True Range = max(H-L, |H-Cp|, |L-Cp|)
        ATR = Wilder EMA du True Range sur ATR_PERIODE barres.
        """
        high = df["high"]
        low = df["low"]
        close_prev = df["close"].shift(1)

        # True Range sur chaque bougie
        tr = pd.concat([
            high - low,
            (high - close_prev).abs(),
            (low - close_prev).abs(),
        ], axis=1).max(axis=1)

        # Première valeur de l'ATR : moyenne simple des 14 premières TR
        atr = pd.Series(index=df.index, dtype=float)
        periode = self.ATR_PERIODE

        # Initialisation avec la moyenne simple des 'periode' premières valeurs TR
        atr.iloc[periode] = tr.iloc[1:periode + 1].mean()

        # Lissage Wilder : ATR(i) = (ATR(i-1) * (n-1) + TR(i)) / n
        for i in range(periode + 1, len(df)):
            atr.iloc[i] = (atr.iloc[i - 1] * (periode - 1) + tr.iloc[i]) / periode

        logger.debug("ATR calculé sur %d barres.", len(df))
        return atr

    def _chercher_compression(
        self, df: pd.DataFrame, atr_series: pd.Series
    ) -> dict | None:
        """
        Parcourt les fenêtres glissantes des 20 dernières barres (taille 5 à 15)
        et retourne la compression la plus récente si trouvée.

        Une compression est valide si :
            - range relatif de la fenêtre < SEUIL_RANGE
            - ATR courant < ATR_REFERENCE * SEUIL_ATR_RATIO
        """
        n = len(df)
        # Indice de début de la zone d'analyse (20 dernières barres)
        debut_analyse = n - self.FENETRE_MAX

        meilleure_compression = None
        # On cherche la fenêtre la plus récente (on commence par la fin)
        for fin in range(n - 1, debut_analyse + self.FENETRE_MIN - 2, -1):
            for taille in range(self.FENETRE_TAILLE_MAX, self.FENETRE_MIN - 1, -1):
                debut = fin - taille + 1
                if debut < debut_analyse:
                    continue

                # Données de la fenêtre
                fenetre = df.iloc[debut:fin + 1]
                max_high = float(fenetre["high"].max())
                min_low = float(fenetre["low"].min())
                close_fin = float(fenetre["close"].iloc[-1])

                if close_fin == 0:
                    continue

                range_relatif = (max_high - min_low) / close_fin

                # ATR courant : dernière valeur valide dans la fenêtre
                atr_courant = atr_series.iloc[fin]
                if pd.isna(atr_courant) or atr_courant == 0:
                    continue

                # ATR de référence : 14 barres avant le début de la fenêtre
                idx_ref = debut - self.ATR_PERIODE
                if idx_ref < 0:
                    continue

                atr_reference = atr_series.iloc[idx_ref]
                if pd.isna(atr_reference) or atr_reference == 0:
                    continue

                atr_ratio = atr_courant / atr_reference

                # Validation des deux critères
                if range_relatif < self.SEUIL_RANGE and atr_ratio < self.SEUIL_ATR_RATIO:
                    compression = {
                        "pattern": "COMPRESSION",
                        "direction": "NEUTRE",
                        "pattern_clarity": 3,
                        "compression_zone": True,
                        "zone_high": round(max_high, 8),
                        "zone_low": round(min_low, 8),
                        "range_pct": round(range_relatif, 6),
                        "bars_count": taille,
                        "atr_ratio": round(atr_ratio, 4),
                        "description": (
                            f"Zone de compression de {taille} bougies "
                            f"({range_relatif * 100:.1f}% range)"
                        ),
                    }

                    # On prend la première trouvée (la plus récente car on itère à rebours)
                    if meilleure_compression is None:
                        meilleure_compression = compression
                        logger.debug(
                            "Compression candidate : taille=%d, range=%.4f, atr_ratio=%.3f",
                            taille, range_relatif, atr_ratio,
                        )
                    # On continue pour potentiellement trouver une fenêtre plus grande
                    # sur le même point final (plus de barres = signal plus fort)
                    elif taille > meilleure_compression["bars_count"] and fin == n - 1:
                        meilleure_compression = compression

        return meilleure_compression
