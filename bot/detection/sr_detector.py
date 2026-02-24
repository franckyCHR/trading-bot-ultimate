"""
Détecteur de niveaux Support / Résistance.
Utilise les pivots, les nombres ronds et le clustering pour identifier
les zones de prix significatives.
"""

import logging
import numpy as np
import pandas as pd
from scipy.signal import argrelextrema

logger = logging.getLogger(__name__)


class SRDetector:
    """
    Détecte les niveaux de support et de résistance sur un DataFrame OHLCV.

    Algorithme en 4 étapes :
        1. Calcul des pivots hauts/bas via scipy.signal.argrelextrema
        2. Ajout des nombres ronds significatifs
        3. Clustering des niveaux proches (< 0.3%)
        4. Calcul de la force en fonction du nombre de touches
    """

    # Tolérance de clustering : deux niveaux à moins de 0.3% sont fusionnés
    CLUSTER_TOLERANCE = 0.003

    # Largeur de la zone autour du niveau central (±0.2%)
    ZONE_HALF_WIDTH = 0.002

    def detect(self, df: pd.DataFrame) -> list[dict]:
        """
        Détecte les niveaux S/R sur le DataFrame fourni.

        Paramètres
        ----------
        df : pd.DataFrame
            DataFrame OHLCV avec colonnes ['open', 'high', 'low', 'close', 'volume'].
            Les noms de colonnes sont insensibles à la casse.

        Retourne
        --------
        list[dict]
            Liste de niveaux triés par force décroissante.
            Chaque dict contient : price, strength, touches, type,
            zone_high, zone_low.
        """
        # --- Normalisation des noms de colonnes en minuscules ---
        df = df.copy()
        df.columns = [c.lower() for c in df.columns]

        if len(df) < 15:
            logger.warning("DataFrame trop court (%d barres) pour détecter des S/R.", len(df))
            return []

        prix_actuel = float(df["close"].iloc[-1])
        logger.debug("Début détection S/R — prix actuel : %.4f", prix_actuel)

        # --- Étape 1 : Pivots hauts et bas ---
        niveaux_bruts = self._extraire_pivots(df)

        # --- Étape 2 : Nombres ronds ---
        niveaux_bruts.extend(self._nombres_ronds(prix_actuel))

        if not niveaux_bruts:
            logger.info("Aucun niveau brut trouvé.")
            return []

        # --- Étape 3 : Clustering ---
        clusters = self._clusturiser(niveaux_bruts)

        # --- Étape 4 : Construction des résultats ---
        resultats = []
        for niveau, touches in clusters:
            if touches < 1:
                continue

            force = self._calculer_force(touches)
            type_niveau = "resistance" if niveau > prix_actuel else "support"
            zone_high = round(niveau * (1 + self.ZONE_HALF_WIDTH), 8)
            zone_low = round(niveau * (1 - self.ZONE_HALF_WIDTH), 8)

            resultats.append({
                "price": round(niveau, 8),
                "strength": force,
                "touches": touches,
                "type": type_niveau,
                "zone_high": zone_high,
                "zone_low": zone_low,
            })

        # Tri par force décroissante, puis par nombre de touches décroissant
        resultats.sort(key=lambda x: (x["strength"], x["touches"]), reverse=True)

        logger.info("Détection S/R terminée : %d niveau(x) trouvé(s).", len(resultats))
        return resultats

    # ------------------------------------------------------------------
    # Méthodes privées
    # ------------------------------------------------------------------

    def _extraire_pivots(self, df: pd.DataFrame) -> list[float]:
        """
        Extrait les pivots hauts et bas avec scipy.signal.argrelextrema (order=5).
        Utilise la colonne 'high' pour les maxima et 'low' pour les minima.
        """
        niveaux = []
        ordre = 5  # Nombre de barres de chaque côté pour définir un pivot

        highs = df["high"].values
        lows = df["low"].values

        # Indices des maxima locaux sur les hauts
        indices_max = argrelextrema(highs, np.greater, order=ordre)[0]
        for i in indices_max:
            niveaux.append(float(highs[i]))
            logger.debug("Pivot haut détecté à l'indice %d : %.4f", i, highs[i])

        # Indices des minima locaux sur les bas
        indices_min = argrelextrema(lows, np.less, order=ordre)[0]
        for i in indices_min:
            niveaux.append(float(lows[i]))
            logger.debug("Pivot bas détecté à l'indice %d : %.4f", i, lows[i])

        logger.debug("%d pivot(s) extrait(s).", len(niveaux))
        return niveaux

    def _nombres_ronds(self, prix: float) -> list[float]:
        """
        Génère des niveaux aux nombres ronds significatifs proches du prix actuel.

        Le facteur d'arrondi est calculé comme suit :
            round_factor = prix * 0.001 arrondi au multiple de 10/100/1000 le plus proche
        On génère ensuite ±10 multiples autour du prix courant.
        """
        # Calcul du facteur d'arrondi
        facteur_brut = prix * 0.001

        # Arrondi au plus proche parmi 1, 10, 100, 1000, 10000
        puissances = [1, 10, 100, 1_000, 10_000]
        facteur = min(puissances, key=lambda p: abs(facteur_brut - p))
        if facteur < 1:
            facteur = 1

        logger.debug("Facteur d'arrondi pour nombres ronds : %d", facteur)

        # Niveau de base le plus proche
        base = round(prix / facteur) * facteur

        # Génère 10 niveaux de chaque côté
        niveaux = []
        for i in range(-10, 11):
            niveau = base + i * facteur
            if niveau > 0:
                niveaux.append(float(niveau))

        return niveaux

    def _clusturiser(self, niveaux: list[float]) -> list[tuple[float, int]]:
        """
        Regroupe les niveaux proches (< CLUSTER_TOLERANCE) et retourne
        une liste de (prix_moyen, nombre_de_touches).
        """
        if not niveaux:
            return []

        niveaux_tries = sorted(niveaux)
        clusters: list[list[float]] = []
        cluster_courant: list[float] = [niveaux_tries[0]]

        for niveau in niveaux_tries[1:]:
            # Référence = milieu du cluster courant
            ref = np.mean(cluster_courant)
            if abs(niveau - ref) / ref <= self.CLUSTER_TOLERANCE:
                cluster_courant.append(niveau)
            else:
                clusters.append(cluster_courant)
                cluster_courant = [niveau]

        clusters.append(cluster_courant)

        resultats = []
        for cluster in clusters:
            prix_moyen = float(np.mean(cluster))
            touches = len(cluster)
            resultats.append((prix_moyen, touches))

        logger.debug("%d cluster(s) formé(s) à partir de %d niveau(x).", len(resultats), len(niveaux))
        return resultats

    @staticmethod
    def _calculer_force(touches: int) -> int:
        """
        Convertit le nombre de touches en score de force.

        1 touche  → 1 (faible)
        2-3 touches → 2 (moyen)
        4+  touches → 3 (fort)
        """
        if touches >= 4:
            return 3
        if touches >= 2:
            return 2
        return 1
