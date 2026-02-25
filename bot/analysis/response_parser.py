"""
response_parser.py
──────────────────
Parse et normalise les réponses JSON de Claude Vision.
Gère les blocs markdown ```json``` et valide les champs obligatoires.
"""

import json
import logging
import re

logger = logging.getLogger("ResponseParser")

# Champs obligatoires dans la réponse
REQUIRED_FIELDS = [
    "gate1_sr",
    "gate2_pattern",
    "indicators",
    "confluence_score",
    "direction",
    "summary",
]

# Champs numériques pour les niveaux de prix
PRICE_FIELDS = ["entry", "sl", "tp1", "tp2", "rr_ratio"]


class ResponseParser:
    """Parse les réponses JSON de l'analyse visuelle Claude."""

    def parse(self, raw_text: str) -> dict:
        """
        Extrait et valide le JSON depuis la réponse brute de Claude.

        Args:
            raw_text: Texte brut retourné par Claude (peut contenir ```json```)

        Returns:
            Dict normalisé compatible avec le pipeline existant (alert_manager, dashboard)
        """
        # Extraire le JSON
        data = self._extract_json(raw_text)

        # Valider les champs obligatoires
        self._validate(data)

        # Normaliser pour compatibilité pipeline
        normalized = self._normalize(data)

        return normalized

    def _extract_json(self, text: str) -> dict:
        """Extrait le JSON d'un texte qui peut contenir des blocs markdown."""
        # Stratégie 1 : bloc ```json ... ```
        match = re.search(r"```json\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                logger.warning("Bloc ```json``` trouvé mais JSON invalide")

        # Stratégie 2 : bloc ``` ... ``` (sans "json")
        match = re.search(r"```\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Stratégie 3 : JSON direct (le texte entier)
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Stratégie 4 : trouver le premier { ... } dans le texte
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        logger.error("Impossible d'extraire du JSON de la réponse")
        logger.debug(f"Texte brut : {text[:500]}")
        return {
            "error": "JSON extraction failed",
            "raw_text": text[:1000],
            "confluence_score": 0,
            "direction": "NEUTRAL",
            "summary": "Erreur de parsing — réponse non structurée",
            "gate1_sr": {"found": False},
            "gate2_pattern": {"found": False},
            "indicators": {},
            "warnings": ["Parsing échoué — vérifier manuellement"],
        }

    def _validate(self, data: dict) -> None:
        """Vérifie la présence des champs obligatoires."""
        missing = [f for f in REQUIRED_FIELDS if f not in data]
        if missing:
            logger.warning(f"Champs manquants dans la réponse : {missing}")

    def _normalize(self, data: dict) -> dict:
        """
        Normalise le dict pour le rendre compatible avec :
        - AlertManager.send() (attend: pair, pattern, direction, entry, sl, tp1, tp2, etc.)
        - DashboardGenerator._signal_card() (attend: pattern, direction, entry, etc.)
        - signals_log.json
        """
        # Extraire la direction du pattern pour rester cohérent
        gate2 = data.get("gate2_pattern", {})
        pattern_name = gate2.get("name", "Visual Analysis") if gate2.get("found") else "No Pattern"

        # Score
        score = data.get("confluence_score", 0)
        direction = data.get("direction", "NEUTRAL")

        # Prix — garder 0 si pas fourni
        entry = float(data.get("entry", 0) or 0)
        sl = float(data.get("sl", 0) or 0)
        tp1 = float(data.get("tp1", 0) or 0)
        tp2 = float(data.get("tp2", 0) or 0)
        rr = float(data.get("rr_ratio", 0) or 0)

        # Indicateurs
        indicators = data.get("indicators", {})
        adx_data = indicators.get("adx", {})
        qqe_data = indicators.get("qqe", {})
        rsi_data = indicators.get("rsi", {})
        ema_data = indicators.get("ema", {})

        # Construire le texte de confluence
        confirmations = []
        if data.get("gate1_sr", {}).get("found"):
            sr = data["gate1_sr"]
            confirmations.append(f"S/R {sr.get('type', '')} ({sr.get('strength', '')})")
        if gate2.get("found"):
            confirmations.append(f"{pattern_name}")
        if adx_data.get("valid"):
            confirmations.append(f"ADX {adx_data.get('value', 0)}")
        if qqe_data.get("crossed"):
            confirmations.append("QQE croisé")
        if rsi_data.get("divergence") and rsi_data["divergence"] != "none":
            confirmations.append(f"RSI divergence {rsi_data['divergence']}")

        confluence_text = " + ".join(confirmations) if confirmations else "Aucune confluence"

        # ADX status
        adx_val = adx_data.get("value", 0) if isinstance(adx_data, dict) else 0

        # QQE status
        qqe_crossed = qqe_data.get("crossed", False) if isinstance(qqe_data, dict) else False
        qqe_status = "croisement" if qqe_crossed else ""

        # Harmoniques
        harmonics = data.get("harmonics", {})
        has_harmonic = harmonics.get("found", False) if isinstance(harmonics, dict) else False

        # Compression
        compression = data.get("compression", {})
        has_compression = compression.get("found", False) if isinstance(compression, dict) else False

        normalized = {
            # Champs compatibles pipeline existant
            "pattern": pattern_name,
            "direction": direction,
            "entry": entry,
            "sl": sl,
            "stop_loss": sl,
            "tp1": tp1,
            "tp2": tp2,
            "rr_ratio": round(rr, 1),
            "confluence": confluence_text,
            "adx": adx_val,
            "qqe_status": qqe_status,
            "compression_zone": has_compression,
            "sr_zone": data.get("gate1_sr", {}).get("found", False),

            # Champs spécifiques analyse visuelle
            "analysis_type": "visual",
            "confluence_score": score,
            "summary": data.get("summary", ""),
            "warnings": data.get("warnings", []),

            # Données brutes pour référence
            "gate1_sr": data.get("gate1_sr", {}),
            "gate2_pattern": data.get("gate2_pattern", {}),
            "indicators_detail": indicators,
            "harmonics_detail": harmonics,
            "compression_detail": compression,

            # Meta (sera enrichi par VisionAnalyzer)
            "_meta": data.get("_meta", {}),
        }

        return normalized
