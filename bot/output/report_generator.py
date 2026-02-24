"""
report_generator.py
Génère des rapports de performance quotidiens et hebdomadaires
à partir du journal de signaux JSON.
"""

import json
import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Journalisation du module
logger = logging.getLogger(__name__)

# Séparateurs visuels ASCII pour les rapports texte
_LINE_DOUBLE = "=" * 60
_LINE_SINGLE = "-" * 60


class ReportGenerator:
    """
    Génère des rapports de performance lisibles à partir d'un fichier
    journal JSON contenant les signaux émis par le bot de trading.

    Format attendu du fichier JSON :
    [
        {
            "timestamp": "2025-01-15T09:30:00",
            "pair":      "EURUSD",
            "direction": "LONG",
            "pattern":   "Double Bottom W",
            "result":    "TP1"          (optionnel)
        },
        ...
    ]
    """

    def __init__(self, log_file: str = "outputs/signals_log.json") -> None:
        """
        Initialise le générateur de rapports.

        Args:
            log_file: Chemin relatif ou absolu vers le fichier JSON des signaux.
        """
        self.log_path = Path(log_file)
        logger.debug("ReportGenerator initialisé — log_file=%s", self.log_path)

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def daily_report(self) -> str:
        """
        Génère un rapport pour les signaux des dernières 24 heures.

        Returns:
            Rapport formaté sous forme de chaîne de caractères.
        """
        since = datetime.now(tz=timezone.utc) - timedelta(days=1)
        signals = self._load_signals(since)
        logger.info("Rapport quotidien : %d signal(s) trouvé(s)", len(signals))
        return self._format_report(signals, period="Rapport Quotidien (24h)")

    def weekly_report(self) -> str:
        """
        Génère un rapport pour les signaux des 7 derniers jours.

        Returns:
            Rapport formaté sous forme de chaîne de caractères.
        """
        since = datetime.now(tz=timezone.utc) - timedelta(days=7)
        signals = self._load_signals(since)
        logger.info("Rapport hebdomadaire : %d signal(s) trouvé(s)", len(signals))
        return self._format_report(signals, period="Rapport Hebdomadaire (7 jours)")

    # ------------------------------------------------------------------
    # Méthodes privées — chargement des données
    # ------------------------------------------------------------------

    def _load_signals(self, since: datetime) -> list[dict]:
        """
        Charge les signaux depuis le fichier JSON et filtre par date.

        Args:
            since: Date/heure de début (UTC) — les signaux antérieurs sont ignorés.

        Returns:
            Liste de dictionnaires représentant les signaux filtrés,
            triés par ordre chronologique.
        """
        # Vérification de l'existence du fichier
        if not self.log_path.exists():
            logger.warning("Fichier de signaux introuvable : %s", self.log_path)
            return []

        # Lecture du JSON
        try:
            raw_text = self.log_path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            logger.error("Erreur lecture %s : %s", self.log_path, exc)
            return []

        if not raw_text:
            logger.warning("Fichier de signaux vide : %s", self.log_path)
            return []

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.error("JSON invalide dans %s : %s", self.log_path, exc)
            return []

        if not isinstance(data, list):
            logger.error(
                "Format JSON invalide : liste attendue, %s reçu", type(data).__name__
            )
            return []

        # Filtrage par date
        filtered: list[dict] = []
        for signal in data:
            if not isinstance(signal, dict):
                continue
            ts_raw = signal.get("timestamp")
            if not ts_raw:
                continue
            try:
                ts = self._parse_timestamp(ts_raw)
            except ValueError as exc:
                logger.warning("Timestamp invalide ignoré ('%s') : %s", ts_raw, exc)
                continue
            if ts >= since:
                filtered.append(signal)

        # Tri chronologique
        filtered.sort(key=lambda s: s.get("timestamp", ""))
        logger.debug("%d signal(s) filtrés sur la période", len(filtered))
        return filtered

    # ------------------------------------------------------------------
    # Méthodes privées — formatage du rapport
    # ------------------------------------------------------------------

    def _format_report(self, signals: list[dict], period: str) -> str:
        """
        Formate les signaux en un rapport texte lisible.

        Args:
            signals: Liste des signaux à inclure dans le rapport.
            period:  Intitulé de la période (ex. "Rapport Quotidien").

        Returns:
            Rapport complet sous forme de chaîne multi-lignes.
        """
        # Cas : aucun signal
        if not signals:
            return (
                f"{_LINE_DOUBLE}\n"
                f"  {period}\n"
                f"{_LINE_DOUBLE}\n"
                "  Aucun signal enregistré\n"
                f"{_LINE_DOUBLE}"
            )

        lines: list[str] = []

        # En-tête
        lines.append(_LINE_DOUBLE)
        lines.append(f"  {period}")
        lines.append(f"  Généré le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(_LINE_DOUBLE)

        # --- Totaux ---
        total = len(signals)
        long_count = sum(1 for s in signals if s.get("direction", "").upper() == "LONG")
        short_count = sum(1 for s in signals if s.get("direction", "").upper() == "SHORT")

        lines.append(f"  Total signaux : {total}")
        lines.append(f"  LONG          : {long_count}")
        lines.append(f"  SHORT         : {short_count}")

        # --- Résultats (optionnel) ---
        results = [s.get("result") for s in signals if s.get("result")]
        if results:
            lines.append(_LINE_SINGLE)
            lines.append("  RESULTATS")
            lines.append(_LINE_SINGLE)
            result_counts = Counter(results)
            for result, count in result_counts.most_common():
                lines.append(f"  {result:<15} : {count}")

        # --- Par figure chartiste ---
        patterns = [s.get("pattern") for s in signals if s.get("pattern")]
        if patterns:
            lines.append(_LINE_SINGLE)
            lines.append("  PAR FIGURE")
            lines.append(_LINE_SINGLE)
            pattern_counts = Counter(patterns)
            for pattern, count in pattern_counts.most_common():
                lines.append(f"  {pattern:<30} : {count}")

        # --- Par paire ---
        pairs = [s.get("pair") for s in signals if s.get("pair")]
        if pairs:
            lines.append(_LINE_SINGLE)
            lines.append("  PAR PAIRE")
            lines.append(_LINE_SINGLE)
            pair_counts = Counter(pairs)
            for pair, count in pair_counts.most_common():
                lines.append(f"  {pair:<15} : {count}")

        # --- Détail des signaux ---
        lines.append(_LINE_SINGLE)
        lines.append("  DETAIL DES SIGNAUX")
        lines.append(_LINE_SINGLE)
        for i, signal in enumerate(signals, start=1):
            ts = signal.get("timestamp", "?")
            pair = signal.get("pair", "?")
            direction = signal.get("direction", "?")
            pattern = signal.get("pattern", "?")
            result = signal.get("result", "en cours")
            lines.append(
                f"  [{i:03d}] {ts}  {pair:<10} {direction:<6} {pattern:<30} → {result}"
            )

        lines.append(_LINE_DOUBLE)

        rapport = "\n".join(lines)
        return rapport

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_timestamp(ts_raw: str) -> datetime:
        """
        Parse un timestamp ISO 8601 en objet datetime UTC.

        Gère les formats avec ou sans fuseau horaire.

        Args:
            ts_raw: Chaîne de timestamp (ex. "2025-01-15T09:30:00" ou avec "+00:00").

        Returns:
            datetime avec tzinfo=UTC.

        Raises:
            ValueError: Si le format n'est pas reconnu.
        """
        # Formats courants à tenter
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]
        # Nettoyage du suffixe UTC (+00:00 ou Z)
        ts_clean = ts_raw.replace("Z", "+00:00")
        # Tentative avec fromisoformat (Python 3.7+)
        try:
            dt = datetime.fromisoformat(ts_clean)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            pass
        # Fallback sur strptime
        for fmt in formats:
            try:
                dt = datetime.strptime(ts_raw, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        raise ValueError(f"Format de timestamp non reconnu : '{ts_raw}'")
