"""
claude_brain.py
Charge tous les modules MODULE-XX.md comme contexte pour l'analyse technique.
Les fichiers sont mis en cache et rechargés uniquement si leur contenu change.
"""

import logging
import os
from pathlib import Path

# Journalisation du module
logger = logging.getLogger(__name__)

# Séparateur visuel utilisé dans le contexte assemblé
_SEPARATOR = "=" * 60


class ClaudeBrain:
    """
    Agrège les fichiers MODULE-XX.md du dossier knowledge/ en un
    seul bloc de contexte textuel utilisable par le moteur d'analyse.

    Fonctionnement du cache :
    - Le contexte est calculé une seule fois, puis conservé en mémoire.
    - Il est invalidé et reconstruit si la somme des tailles de fichiers change,
      ce qui détecte les ajouts, suppressions ou modifications de modules.
    """

    def __init__(self) -> None:
        """Initialise le cerveau et prépare le répertoire de connaissance."""
        # Chemin vers le dossier knowledge/ à la racine du projet
        self.knowledge_dir: Path = (
            Path(__file__).parent.parent.parent / "knowledge"
        )
        # Cache interne : None tant que rien n'a encore été chargé
        self._cache: str | None = None
        # Signature utilisée pour détecter les changements de fichiers
        self._cache_signature: str = ""

        logger.debug("ClaudeBrain initialisé — knowledge_dir=%s", self.knowledge_dir)

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def load_knowledge(self) -> str:
        """
        Charge tous les fichiers MODULE-XX.md et les assemble en un seul texte.

        Les fichiers sont triés par numéro de module.
        Chaque module est précédé d'un en-tête lisible.

        Returns:
            Contexte complet sous forme de chaîne, ou message d'erreur si le
            répertoire est introuvable.
        """
        # Vérification de l'existence du répertoire
        if not self.knowledge_dir.exists():
            message = (
                f"Répertoire knowledge introuvable : {self.knowledge_dir}"
            )
            logger.warning(message)
            return message

        # Récupération et tri des fichiers MODULE-*.md
        module_files = sorted(
            self.knowledge_dir.glob("MODULE-*.md"),
            key=self._extract_module_number,
        )

        if not module_files:
            message = "Aucun fichier MODULE-*.md trouvé dans knowledge/"
            logger.warning(message)
            return message

        logger.info(
            "%d module(s) trouvé(s) dans %s", len(module_files), self.knowledge_dir
        )

        # Assemblage du contexte
        sections: list[str] = []
        for filepath in module_files:
            header = (
                f"{_SEPARATOR}\n"
                f"MODULE : {filepath.name}\n"
                f"{_SEPARATOR}"
            )
            try:
                content = filepath.read_text(encoding="utf-8")
                sections.append(f"{header}\n{content}")
                logger.debug("Module chargé : %s (%d caractères)", filepath.name, len(content))
            except OSError as exc:
                erreur = f"[ERREUR lecture {filepath.name} : {exc}]"
                sections.append(f"{header}\n{erreur}")
                logger.error("Impossible de lire %s : %s", filepath.name, exc)

        return "\n\n".join(sections)

    def get_context(self) -> str:
        """
        Retourne le contexte assemblé de tous les modules (avec mise en cache).

        Le cache est invalidé automatiquement si les fichiers ont changé
        (détection par signature basée sur les tailles des fichiers).

        Returns:
            Contexte textuel complet de tous les modules.
        """
        signature = self._compute_signature()

        if self._cache is not None and signature == self._cache_signature:
            logger.debug("Cache valide — contexte retourné depuis le cache")
            return self._cache

        logger.info("Chargement du contexte (cache absent ou invalidé)")
        self._cache = self.load_knowledge()
        self._cache_signature = signature
        return self._cache

    def get_module(self, module_num: int) -> str:
        """
        Charge et retourne le contenu d'un module spécifique.

        Args:
            module_num: Numéro du module souhaité (ex. 1 pour MODULE-01).

        Returns:
            Contenu textuel du module, ou message d'erreur si introuvable.
        """
        if not self.knowledge_dir.exists():
            message = f"Répertoire knowledge introuvable : {self.knowledge_dir}"
            logger.warning(message)
            return message

        # Recherche par préfixe numéroté (ex. "MODULE-01-")
        prefix = f"MODULE-{module_num:02d}-"
        matches = list(self.knowledge_dir.glob(f"{prefix}*.md"))

        if not matches:
            message = f"Module {module_num:02d} introuvable dans {self.knowledge_dir}"
            logger.warning(message)
            return message

        # On prend le premier résultat (il ne devrait y en avoir qu'un)
        filepath = matches[0]
        try:
            content = filepath.read_text(encoding="utf-8")
            logger.debug("Module %02d chargé : %s", module_num, filepath.name)
            return content
        except OSError as exc:
            message = f"Erreur lecture MODULE-{module_num:02d} : {exc}"
            logger.error(message)
            return message

    def list_modules(self) -> list[str]:
        """
        Liste tous les noms de fichiers MODULE-XX.md disponibles.

        Returns:
            Liste triée des noms de fichiers (ex. ["MODULE-01-sr.md", ...]).
            Liste vide si le répertoire est absent ou sans modules.
        """
        if not self.knowledge_dir.exists():
            logger.warning(
                "Répertoire knowledge introuvable : %s", self.knowledge_dir
            )
            return []

        modules = sorted(
            (f.name for f in self.knowledge_dir.glob("MODULE-*.md")),
            key=lambda name: self._extract_module_number(Path(name)),
        )

        logger.debug("%d module(s) disponible(s) : %s", len(modules), modules)
        return modules

    # ------------------------------------------------------------------
    # Méthodes privées
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_module_number(filepath: Path) -> int:
        """
        Extrait le numéro entier d'un fichier MODULE-XX-nom.md.

        Args:
            filepath: Chemin vers le fichier module.

        Returns:
            Numéro entier du module, ou 999 si le nom ne correspond pas au format.
        """
        # Format attendu : MODULE-<num>-<nom>.md
        parts = filepath.stem.split("-")
        try:
            return int(parts[1])
        except (IndexError, ValueError):
            logger.warning(
                "Impossible d'extraire le numéro de module depuis '%s'", filepath.name
            )
            return 999

    def _compute_signature(self) -> str:
        """
        Calcule une signature légère pour détecter les modifications de fichiers.

        La signature est construite à partir des noms et tailles de tous les
        fichiers MODULE-*.md présents dans knowledge/.

        Returns:
            Chaîne représentant l'état actuel des fichiers modules.
        """
        if not self.knowledge_dir.exists():
            return ""

        parts: list[str] = []
        for filepath in sorted(self.knowledge_dir.glob("MODULE-*.md")):
            try:
                size = filepath.stat().st_size
                parts.append(f"{filepath.name}:{size}")
            except OSError:
                parts.append(f"{filepath.name}:?")

        return "|".join(parts)
