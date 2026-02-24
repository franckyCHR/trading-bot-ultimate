"""
adx_validator.py
Valide le momentum ADX selon MODULE-09.
ADX < 20 → signal bloqué.
DI dans la mauvaise direction → signal bloqué.
"""

import logging
from dataclasses import dataclass

# Journalisation du module
logger = logging.getLogger(__name__)


@dataclass
class ADXResult:
    """Résultat de la validation ADX."""
    valid: bool
    reason: str
    adx_value: float
    adx_category: str  # "FAIBLE" | "NAISSANT" | "CONFIRME" | "FORT" | "EXTREME"


class ADXValidator:
    """
    Valide le momentum ADX avant d'émettre un signal.

    Règles issues du MODULE-09 :
    - ADX < 20  → pas de tendance → signal bloqué
    - ADX 20-25 → tendance naissante (faible)
    - ADX 25-40 → tendance confirmée
    - ADX 40-60 → tendance forte
    - ADX > 60  → tendance extrême (avertissement)
    - DI dans la mauvaise direction → signal bloqué
    """

    def __init__(self, min_adx: float = 20) -> None:
        """
        Initialise le validateur ADX.

        Args:
            min_adx: Valeur minimale d'ADX requise pour valider un signal (défaut : 20).
        """
        self.min_adx = min_adx
        logger.debug("ADXValidator initialisé avec min_adx=%.1f", min_adx)

    # ------------------------------------------------------------------
    # Méthode publique principale
    # ------------------------------------------------------------------

    def validate(
        self,
        adx: float,
        di_plus: float,
        di_minus: float,
        direction: str,
    ) -> ADXResult:
        """
        Valide le momentum ADX pour un signal donné.

        Args:
            adx:       Valeur actuelle de l'ADX.
            di_plus:   Valeur du +DI (momentum haussier).
            di_minus:  Valeur du -DI (momentum baissier).
            direction: Direction du signal — "LONG" ou "SHORT".

        Returns:
            ADXResult contenant le verdict et la catégorie de tendance.
        """
        direction = direction.upper()

        # --- Étape 1 : vérifier le seuil minimum ---
        if adx < self.min_adx:
            reason = f"ADX {adx:.1f} < {self.min_adx} — pas de tendance"
            logger.warning("ADX invalide : %s", reason)
            return ADXResult(
                valid=False,
                reason=reason,
                adx_value=adx,
                adx_category="FAIBLE",
            )

        # --- Étape 2 : catégoriser la force de la tendance ---
        category = self._categorize(adx)

        # --- Étape 3 : vérifier la direction des DI ---
        di_result = self._check_di_direction(adx, di_plus, di_minus, direction, category)
        if di_result is not None:
            return di_result

        # --- Étape 4 : avertissement tendance extrême ---
        if category == "EXTREME":
            reason = (
                f"ADX {adx:.1f} — tendance EXTREME, risque de retournement élevé"
            )
            logger.warning("ADX extrême détecté : %.1f", adx)
        else:
            reason = f"ADX {adx:.1f} — tendance {category}"

        logger.info(
            "ADX valide : valeur=%.1f catégorie=%s direction=%s +DI=%.1f -DI=%.1f",
            adx,
            category,
            direction,
            di_plus,
            di_minus,
        )
        return ADXResult(
            valid=True,
            reason=reason,
            adx_value=adx,
            adx_category=category,
        )

    # ------------------------------------------------------------------
    # Méthodes privées
    # ------------------------------------------------------------------

    def _categorize(self, adx: float) -> str:
        """
        Retourne la catégorie textuelle correspondant à la valeur ADX.

        Args:
            adx: Valeur de l'ADX.

        Returns:
            Chaîne parmi "NAISSANT", "CONFIRME", "FORT", "EXTREME".
        """
        if adx < 25:
            return "NAISSANT"
        if adx < 40:
            return "CONFIRME"
        if adx <= 60:
            return "FORT"
        return "EXTREME"

    def _check_di_direction(
        self,
        adx: float,
        di_plus: float,
        di_minus: float,
        direction: str,
        category: str,
    ) -> ADXResult | None:
        """
        Vérifie que les DI sont alignés avec la direction du signal.

        Args:
            adx:       Valeur ADX déjà validée (>= min_adx).
            di_plus:   Valeur du +DI.
            di_minus:  Valeur du -DI.
            direction: "LONG" ou "SHORT".
            category:  Catégorie ADX déjà calculée.

        Returns:
            ADXResult invalide si les DI sont contraires, None sinon.
        """
        if direction == "LONG" and di_minus > di_plus:
            reason = f"+DI {di_plus:.1f} < -DI {di_minus:.1f} — momentum baissier"
            logger.warning("DI contraire au LONG : %s", reason)
            return ADXResult(
                valid=False,
                reason=reason,
                adx_value=adx,
                adx_category=category,
            )

        if direction == "SHORT" and di_plus > di_minus:
            reason = f"-DI {di_minus:.1f} < +DI {di_plus:.1f} — momentum haussier"
            logger.warning("DI contraire au SHORT : %s", reason)
            return ADXResult(
                valid=False,
                reason=reason,
                adx_value=adx,
                adx_category=category,
            )

        return None
