"""
vision_client.py
────────────────
Organisateur de screenshots pour analyse visuelle.
Pas d'API externe — l'analyse se fait directement dans Claude Code
qui a accès aux images + aux 17 modules + au scoring.

Workflow :
  1. L'utilisateur capture ses screenshots (semi-auto ou manuellement)
  2. Ce module les organise dans outputs/screenshots/
  3. L'utilisateur demande à Claude Code d'analyser
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("VisionAnalyzer")

SCREENSHOTS_DIR = "outputs/screenshots"
ANALYSES_DIR = "outputs/analyses"


class VisionAnalyzer:
    """
    Organise les screenshots et prépare les analyses.
    L'analyse réelle est faite par Claude Code (pas d'API externe).
    """

    def __init__(self):
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        os.makedirs(ANALYSES_DIR, exist_ok=True)

    def register_image(
        self,
        image_path: str,
        pair: str,
        timeframe: str,
        template: str = "Momentum",
    ) -> dict:
        """
        Enregistre un screenshot pour analyse future.
        Copie l'image dans le dossier organisé si nécessaire.

        Returns:
            dict avec les métadonnées du screenshot
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image introuvable : {image_path}")

        file_size = path.stat().st_size
        if file_size < 10_000:
            logger.warning(f"Image suspecte ({file_size} bytes) : {image_path}")

        # Si l'image n'est pas déjà dans le dossier screenshots, la copier
        dest = path
        if SCREENSHOTS_DIR not in str(path):
            pair_clean = pair.replace("/", "_")
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_name = f"{pair_clean}_{timeframe}_{template}_{ts}{path.suffix}"
            dest = Path(SCREENSHOTS_DIR) / dest_name
            import shutil
            shutil.copy2(path, dest)
            logger.info(f"Image copiée : {dest}")

        entry = {
            "image_path": str(dest),
            "pair": pair,
            "timeframe": timeframe,
            "template": template,
            "filename": dest.name,
            "size_kb": round(file_size / 1024, 1),
            "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        return entry

    def list_screenshots(self, pair: Optional[str] = None) -> list[dict]:
        """Liste les screenshots disponibles, filtré par paire optionnellement."""
        screenshots = []
        for ext in ("*.png", "*.jpg", "*.jpeg"):
            for f in sorted(Path(SCREENSHOTS_DIR).glob(ext), reverse=True):
                info = {
                    "filename": f.name,
                    "path": str(f),
                    "size_kb": round(f.stat().st_size / 1024, 1),
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                }
                # Extraire paire du nom de fichier (ex: GBP_USD_H1_Momentum_...)
                parts = f.stem.split("_")
                if len(parts) >= 2:
                    info["pair"] = f"{parts[0]}/{parts[1]}"
                if len(parts) >= 3:
                    info["timeframe"] = parts[2]
                if len(parts) >= 4:
                    info["template"] = parts[3]

                if pair and info.get("pair", "").replace("/", "") != pair.replace("/", ""):
                    continue

                screenshots.append(info)

        return screenshots

    def save_analysis(self, pair: str, timeframe: str, analysis: dict) -> str:
        """Sauvegarde un résultat d'analyse en JSON."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        pair_clean = pair.replace("/", "_")
        path = f"{ANALYSES_DIR}/{pair_clean}_{timeframe}_{ts}.json"

        with open(path, "w") as f:
            json.dump(analysis, f, indent=2, default=str, ensure_ascii=False)

        logger.info(f"Analyse sauvegardée : {path}")
        return path

    def get_analysis_prompt(self, pair: str, timeframe: str, template: str) -> str:
        """
        Génère le prompt optimisé que l'utilisateur peut coller dans Claude Code.
        Utile pour le mode batch ou pour copier/coller.
        """
        from bot.analysis.prompt_builder import PromptBuilder
        pb = PromptBuilder()
        return pb.build_user_prompt(pair, timeframe, template)

    def print_ready_summary(self, images: list[dict]):
        """Affiche un résumé des images prêtes pour analyse Claude Code."""
        if not images:
            print("  Aucune image à analyser.")
            return

        print(f"\n  {len(images)} screenshot(s) prêt(s) pour analyse :")
        print("  " + "-" * 50)
        for img in images:
            print(f"  {img.get('pair', '?'):10s} | {img.get('timeframe', '?'):4s} | "
                  f"{img.get('template', '?'):15s} | {img.get('filename', '?')}")
        print("  " + "-" * 50)
        print()
        print("  Pour analyser dans Claude Code :")
        print("  → Ouvre Claude Code dans ce projet")
        print("  → Dis : \"Analyse les screenshots dans outputs/screenshots/\"")
        print("  → Ou pour un seul : \"Analyse outputs/screenshots/NOM.png\"")
        print()
