"""
qqe_validator.py
Valide le croisement QQE selon MODULE-10.
Un croisement récent dans le bon sens est requis pour confirmer le signal.
"""

import logging
from dataclasses import dataclass

# Journalisation du module
logger = logging.getLogger(__name__)


@dataclass
class QQEResult:
    """Résultat de la validation QQE."""
    valid: bool
    quality: str   # "OPTIMAL" | "BON" | "ACCEPTABLE" | "TROP_TARD" | "CONTRE"
    reason: str
    bars_ago: int


class QQEValidator:
    """
    Valide le croisement QQE avant d'émettre un signal.

    Règles issues du MODULE-10 :
    - Croisement dans le mauvais sens       → CONTRE (invalide)
    - Croisement il y a 0 ou 1 bougie      → OPTIMAL
    - Croisement il y a 2 ou 3 bougies     → BON
    - Croisement il y a 4 à 6 bougies      → ACCEPTABLE
    - Croisement il y a 7 bougies ou plus  → TROP_TARD (invalide)
    """

    # Seuil au-delà duquel le croisement est considéré trop ancien
    BARS_TROP_TARD: int = 7

    # ------------------------------------------------------------------
    # Méthode publique principale
    # ------------------------------------------------------------------

    def validate(
        self,
        qqe_fast: float,
        qqe_slow: float,
        qqe_fast_prev: float,
        qqe_slow_prev: float,
        bars_ago: int,
        direction: str,
    ) -> QQEResult:
        """
        Valide le croisement QQE pour un signal donné.

        Args:
            qqe_fast:      Valeur actuelle de la ligne QQE rapide.
            qqe_slow:      Valeur actuelle de la ligne QQE lente.
            qqe_fast_prev: Valeur précédente de la ligne QQE rapide (bougie n-1).
            qqe_slow_prev: Valeur précédente de la ligne QQE lente (bougie n-1).
            bars_ago:      Nombre de bougies depuis le dernier croisement.
            direction:     Direction du signal — "LONG" ou "SHORT".

        Returns:
            QQEResult contenant le verdict, la qualité et le nombre de bougies.
        """
        direction = direction.upper()

        logger.debug(
            "Validation QQE — fast=%.4f slow=%.4f fast_prev=%.4f slow_prev=%.4f "
            "bars_ago=%d direction=%s",
            qqe_fast,
            qqe_slow,
            qqe_fast_prev,
            qqe_slow_prev,
            bars_ago,
            direction,
        )

        if direction == "LONG":
            return self._validate_long(qqe_fast, qqe_slow, bars_ago)

        if direction == "SHORT":
            return self._validate_short(qqe_fast, qqe_slow, bars_ago)

        # Direction inconnue → on refuse le signal par sécurité
        reason = f"Direction '{direction}' inconnue — attendu LONG ou SHORT"
        logger.error(reason)
        return QQEResult(valid=False, quality="CONTRE", reason=reason, bars_ago=bars_ago)

    # ------------------------------------------------------------------
    # Méthodes privées par direction
    # ------------------------------------------------------------------

    def _validate_long(
        self, qqe_fast: float, qqe_slow: float, bars_ago: int
    ) -> QQEResult:
        """
        Valide le QQE pour un signal LONG.

        La ligne rapide doit être au-dessus de la ligne lente.

        Args:
            qqe_fast: Ligne QQE rapide actuelle.
            qqe_slow: Ligne QQE lente actuelle.
            bars_ago: Nombre de bougies depuis le croisement.

        Returns:
            QQEResult pour direction LONG.
        """
        # Vérification de l'alignement QQE
        if qqe_fast <= qqe_slow:
            reason = "QQE baissier — contre le trade LONG"
            logger.warning(reason)
            return QQEResult(valid=False, quality="CONTRE", reason=reason, bars_ago=bars_ago)

        return self._score_bars_ago(bars_ago, direction="LONG")

    def _validate_short(
        self, qqe_fast: float, qqe_slow: float, bars_ago: int
    ) -> QQEResult:
        """
        Valide le QQE pour un signal SHORT.

        La ligne rapide doit être en dessous de la ligne lente.

        Args:
            qqe_fast: Ligne QQE rapide actuelle.
            qqe_slow: Ligne QQE lente actuelle.
            bars_ago: Nombre de bougies depuis le croisement.

        Returns:
            QQEResult pour direction SHORT.
        """
        # Vérification de l'alignement QQE
        if qqe_fast >= qqe_slow:
            reason = "QQE haussier — contre le trade SHORT"
            logger.warning(reason)
            return QQEResult(valid=False, quality="CONTRE", reason=reason, bars_ago=bars_ago)

        return self._score_bars_ago(bars_ago, direction="SHORT")

    # ------------------------------------------------------------------
    # Notation de la fraîcheur du croisement
    # ------------------------------------------------------------------

    def _score_bars_ago(self, bars_ago: int, direction: str) -> QQEResult:
        """
        Attribue une qualité au signal en fonction de l'ancienneté du croisement.

        Args:
            bars_ago:  Nombre de bougies écoulées depuis le croisement.
            direction: Direction du signal (utilisée dans le message).

        Returns:
            QQEResult avec qualité et validité déterminées par bars_ago.
        """
        if bars_ago >= self.BARS_TROP_TARD:
            reason = (
                f"Croisement QQE il y a {bars_ago} bougies — signal {direction} trop tardif"
            )
            logger.warning(reason)
            return QQEResult(
                valid=False, quality="TROP_TARD", reason=reason, bars_ago=bars_ago
            )

        if bars_ago <= 1:
            quality = "OPTIMAL"
            emoji_hint = "✅✅"
        elif bars_ago <= 3:
            quality = "BON"
            emoji_hint = "✅"
        else:
            # 4 à 6 bougies
            quality = "ACCEPTABLE"
            emoji_hint = "⚠️"

        reason = (
            f"Croisement QQE il y a {bars_ago} bougie(s) — "
            f"{direction} {quality} {emoji_hint}"
        )
        logger.info(reason)
        return QQEResult(valid=True, quality=quality, reason=reason, bars_ago=bars_ago)
